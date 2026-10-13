/**
 * Minimal SSE reader over fetch (POST bodies are not possible with EventSource).
 * Assumed wire format for POST /api/explain/stream (text/event-stream):
 *   event: stage   data: {"stage":"explain"|"backtranslate"|"verify"}
 *   event: token   data: {"text":"<masked delta>"}
 *   event: done    data: <ExplainResponse>
 *   event: error   data: {"message":"..."}
 * Unnamed events with a JSON {"type": ...} field are accepted too.
 */
export interface RawSseEvent {
  event: string;
  data: string;
}

export async function readSse(res: Response, onEvent: (e: RawSseEvent) => void, signal?: AbortSignal): Promise<void> {
  if (!res.body) throw new Error("Streaming response has no body");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  const flush = (block: string) => {
    let event = "message";
    const data: string[] = [];
    for (const line of block.split(/\r?\n/)) {
      if (!line || line.startsWith(":")) continue;
      const idx = line.indexOf(":");
      const field = idx === -1 ? line : line.slice(0, idx);
      const value = idx === -1 ? "" : line.slice(idx + 1).replace(/^ /, "");
      if (field === "event") event = value;
      else if (field === "data") data.push(value);
    }
    if (data.length) onEvent({ event, data: data.join("\n") });
  };
  try {
    for (;;) {
      if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const sep = /\r?\n\r?\n/;
      let m = sep.exec(buf);
      while (m) {
        const block = buf.slice(0, m.index);
        buf = buf.slice(m.index + m[0].length);
        flush(block);
        m = sep.exec(buf);
      }
    }
    if (buf.trim()) flush(buf);
  } finally {
    reader.releaseLock();
  }
}
