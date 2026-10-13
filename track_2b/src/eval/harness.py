"""Shared harness utilities: a caching LLM client (append-only JSONL), GPU power sampling, dataset loading."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import threading
import time
from dataclasses import asdict
from pathlib import Path

from passerelle.config import Settings, get_settings
from passerelle.ingest import normalize_text
from passerelle.llm import LLMClient, LLMResult

ROOT = Path(__file__).resolve().parents[2]
LETTERS = ROOT / "data" / "letters"
RUNS = ROOT / "data" / "eval_runs"


def load_letters(split: str | None = None) -> list[dict]:
    out = []
    for gp in sorted(LETTERS.glob("*_[0-9].json")):
        gt = json.loads(gp.read_text(encoding="utf-8"))
        if split == "explain":
            if not (gt["split"] == "dev" or gt.get("explain_subset")):
                continue
        elif split and gt["split"] != split:
            continue
        gt["text"] = normalize_text(gp.with_suffix(".txt").read_text(encoding="utf-8"))
        out.append(gt)
    return out


class CachedClient(LLMClient):
    """LLMClient whose calls are memoised in an append-only JSONL file (resumable, reproducible)."""

    def __init__(self, cache_path: Path, settings: Settings | None = None, offline: bool = False):
        super().__init__(settings or get_settings())
        self.cache_path = Path(cache_path)
        self.cache: dict[str, dict] = {}
        self.offline = offline
        self.calls: list[dict] = []
        self._lock = threading.Lock()
        if self.cache_path.exists():
            with self.cache_path.open(encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        e = json.loads(line)
                        self.cache[e["key"]] = e

    def _key(self, kind: str, messages: list[dict], **kw) -> str:
        blob = json.dumps([self.s.llm_name, kind, messages, kw], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _lookup(self, key: str, task: str) -> LLMResult | None:
        e = self.cache.get(key)
        if e is None:
            if self.offline:
                raise RuntimeError(f"cache miss in offline mode for task {task}")
            return None
        r = LLMResult(**e["result"])
        self.calls.append({"task": task, "cached": True, **r.usage(), "finish": r.finish_reason})
        return r

    def _store(self, key: str, task: str, res: LLMResult, t0: float, t1: float) -> None:
        e = {"key": key, "task": task, "model": self.s.llm_name, "t_start": t0, "t_end": t1, "result": asdict(res)}
        with self._lock:
            self.cache[key] = e
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        self.calls.append({"task": task, "cached": False, **res.usage(), "finish": res.finish_reason})

    def chat(self, messages, *, task, max_tokens=800, temperature=None, stop=None, response_format=None):
        key = self._key("chat", messages, max_tokens=max_tokens, temperature=temperature, stop=stop,
                        rf=bool(response_format), seed=self.s.seed, temp_default=self.s.temperature)
        hit = self._lookup(key, task)
        if hit is not None:
            return hit
        t0 = time.time()
        res = super().chat(messages, task=task, max_tokens=max_tokens, temperature=temperature, stop=stop,
                           response_format=response_format)
        self._store(key, task, res, t0, time.time())
        return res

    def chat_guarded(self, messages, *, task, max_tokens=800, temperature=None):
        key = self._key("guarded", messages, max_tokens=max_tokens, temperature=temperature,
                        seed=self.s.seed, temp_default=self.s.temperature)
        hit = self._lookup(key, task)
        if hit is not None:
            return hit
        t0 = time.time()
        res = super().chat_guarded(messages, task=task, max_tokens=max_tokens, temperature=temperature)
        self._store(key, task, res, t0, time.time())
        return res


class GpuSampler:
    """Samples GPU power/utilisation once per second via nvidia-smi (if available)."""

    def __init__(self, interval_ms: int = 1000):
        self.interval_ms = interval_ms
        self.samples: list[tuple[float, float, float, float]] = []  # t, watts, util%, mem MiB
        self._proc = None
        self._thread = None

    def start(self) -> "GpuSampler":
        exe = shutil.which("nvidia-smi")
        if not exe:
            return self
        self._proc = subprocess.Popen(
            [exe, "--query-gpu=power.draw,utilization.gpu,memory.used", "--format=csv,noheader,nounits",
             f"-lms={self.interval_ms}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()
        return self

    def _read(self) -> None:
        assert self._proc and self._proc.stdout
        for line in self._proc.stdout:
            try:
                w, u, m = (float(x) for x in line.strip().split(","))
                self.samples.append((time.time(), w, u, m))
            except ValueError:
                continue

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()

    def energy_wh(self, t0: float, t1: float) -> float | None:
        pts = [(t, w) for t, w, _, _ in self.samples if t0 <= t <= t1]
        if len(pts) < 2:
            return None
        wh = 0.0
        for (ta, wa), (tb, wb) in zip(pts, pts[1:]):
            wh += (wa + wb) / 2 * (tb - ta) / 3600
        return wh

    def summary(self) -> dict:
        if not self.samples:
            return {"available": False}
        ws = [w for _, w, _, _ in self.samples]
        us = [u for _, _, u, _ in self.samples]
        ms = [m for _, _, _, m in self.samples]
        return {"available": True, "n": len(ws), "mean_w": round(sum(ws) / len(ws), 1), "max_w": max(ws),
                "mean_util": round(sum(us) / len(us), 1), "max_mem_mib": max(ms),
                "energy_wh": round(self.energy_wh(self.samples[0][0], self.samples[-1][0]) or 0, 2)}


def energy_from_cache(entries: list[dict], samples: list[tuple]) -> float | None:
    """Integrate sampled GPU power over the time windows of fresh LLM calls."""
    if not samples:
        return None
    total = 0.0
    for e in entries:
        pts = [(t, w) for t, w, *_ in samples if e["t_start"] <= t <= e["t_end"]]
        for (ta, wa), (tb, wb) in zip(pts, pts[1:]):
            total += (wa + wb) / 2 * (tb - ta) / 3600
    return total
