"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import type { Workspace } from "./use-workspace";
import type { AuditEntry } from "@/lib/api/types";
import { explanationSegments, isoToSwiss, renderFactValue, TYPE_LABEL } from "@/lib/facts";
import { GATE_META } from "@/components/domain/atoms";
import { langAttr } from "./facts-pane";
import { fmtChf } from "@/lib/utils";

/** Client-copy labels in the client's language (fallback: English). */
const L10N: Record<string, { title: string; dates: string; amounts: string; ref: string; keep: string; prepared: string }> = {
  en: { title: "Explanation of your letter", dates: "Important dates", amounts: "Amounts", ref: "Reference", keep: "This is an explanation, not the official letter. Keep the original letter.", prepared: "Prepared with your caseworker on" },
  ar: { title: "شرح رسالتك", dates: "تواريخ مهمة", amounts: "المبالغ", ref: "الرقم المرجعي", keep: "هذا شرح وليس الرسالة الرسمية. احتفظ بالرسالة الأصلية.", prepared: "أُعدّ مع المرشد الاجتماعي بتاريخ" },
  prs: { title: "توضیح نامهٔ شما", dates: "تاریخ‌های مهم", amounts: "مبالغ", ref: "شمارهٔ مرجع", keep: "این یک توضیح است، نه نامهٔ رسمی. نامهٔ اصلی را نگه دارید.", prepared: "با مددکار شما تهیه شد در" },
  ti: { title: "መግለጺ ደብዳቤኻ", dates: "ኣገደስቲ ዕለታት", amounts: "መጠን ገንዘብ", ref: "ቁጽሪ መወከሲ", keep: "እዚ መግለጺ እዩ፣ እቲ ወግዓዊ ደብዳቤ ኣይኮነን። ነቲ መበቆላዊ ደብዳቤ ዓቅቦ።", prepared: "ምስ ሰራሕተኛ ጉዳይካ ተዳልዩ፣ ዕለት" },
  uk: { title: "Пояснення вашого листа", dates: "Важливі дати", amounts: "Суми", ref: "Номер справи", keep: "Це пояснення, а не офіційний лист. Збережіть оригінал листа.", prepared: "Підготовлено з вашим соціальним працівником" },
  ta: { title: "உங்கள் கடிதத்தின் விளக்கம்", dates: "முக்கிய தேதிகள்", amounts: "தொகைகள்", ref: "குறிப்பு எண்", keep: "இது ஒரு விளக்கம் மட்டுமே, அதிகாரப்பூர்வ கடிதம் அல்ல. அசல் கடிதத்தை வைத்திருங்கள்.", prepared: "உங்கள் சமூகப் பணியாளருடன் தயாரிக்கப்பட்டது" },
  tr: { title: "Mektubunuzun açıklaması", dates: "Önemli tarihler", amounts: "Tutarlar", ref: "Referans", keep: "Bu bir açıklamadır, resmi mektup değildir. Orijinal mektubu saklayın.", prepared: "Sosyal görevlinizle birlikte hazırlandı" },
};

function redactText(text: string, ws: Workspace) {
  let out = text;
  for (const f of ws.analysis?.facts ?? []) {
    if (f.type !== "name" && f.type !== "address") continue;
    for (const v of [f.value, f.value.replace(/, /g, "\n")]) out = out.split(v).join("█".repeat(Math.min(v.length, 18)));
  }
  return out;
}

export function PrintSheet({ ws, kind, redact, audit }: { ws: Workspace; kind: "client" | "caseworker" | null; redact: boolean; audit: AuditEntry[] }) {
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);
  if (!mounted || !kind) return null;
  const a = ws.analysis;
  const r = ws.explain.result;
  const lang = ws.languages.find((l) => l.code === (ws.explain.lang ?? ws.targetLang));
  const t = L10N[lang?.code ?? "en"] ?? L10N.en;
  const now = new Date();
  const facts = a?.facts ?? [];
  const card = a?.fact_card;
  const R = (s: string) => (redact ? redactText(s, ws) : s);

  const body =
    kind === "client" ? (
      <div lang={lang ? langAttr(lang.code) : undefined} dir={r?.rtl || lang?.rtl ? "rtl" : "ltr"} style={{ fontSize: "12pt", lineHeight: 1.7, color: "#1A1615" }}>
        <p style={{ fontSize: "10pt", color: "#757170" }}>Passerelle · {lang?.native_name}</p>
        <h1 style={{ fontSize: "22pt", fontWeight: 600, margin: "4pt 0 14pt", letterSpacing: "-0.02em" }}>{t.title}</h1>
        {r && (
          <div style={{ whiteSpace: "pre-line" }}>
            {explanationSegments(r, facts).map((s, i) =>
              s.kind === "text" ? (
                <React.Fragment key={i}>{s.text}</React.Fragment>
              ) : (
                <strong key={i} dir="ltr" style={{ unicodeBidi: "isolate", background: "#F0EAE5", padding: "0 3pt", borderRadius: 3 }}>
                  {s.text}
                </strong>
              ),
            )}
          </div>
        )}
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "18pt", fontSize: "11pt" }}>
          <tbody>
            {card?.deadlines.map((d, i) => (
              <tr key={`d${i}`} style={{ borderTop: "1px solid #ddd" }}>
                <td style={{ padding: "6pt 0", color: "#757170" }}>{i === 0 ? t.dates : ""}</td>
                <td style={{ padding: "6pt 0", fontWeight: 600 }} dir="ltr">
                  {d.date ? isoToSwiss(d.date) : d.relative}
                </td>
              </tr>
            ))}
            {card?.amounts.map((m, i) => (
              <tr key={`a${i}`} style={{ borderTop: "1px solid #ddd" }}>
                <td style={{ padding: "6pt 0", color: "#757170" }}>{i === 0 ? t.amounts : ""}</td>
                <td style={{ padding: "6pt 0", fontWeight: 600 }} dir="ltr">
                  {fmtChf(m.value)}
                </td>
              </tr>
            ))}
            {card?.reference_numbers.slice(0, 1).map((x, i) => (
              <tr key={`r${i}`} style={{ borderTop: "1px solid #ddd" }}>
                <td style={{ padding: "6pt 0", color: "#757170" }}>{t.ref}</td>
                <td style={{ padding: "6pt 0", fontWeight: 600 }} dir="ltr">
                  {x.value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: "20pt", fontSize: "10pt", color: "#453F3D" }}>{t.keep}</p>
        <p style={{ fontSize: "10pt", color: "#757170" }}>
          {t.prepared} <span dir="ltr">{now.toLocaleDateString("de-CH")}</span>
        </p>
      </div>
    ) : (
      <div style={{ fontSize: "10pt", lineHeight: 1.55, color: "#1A1615" }}>
        <p style={{ color: "#757170" }}>Passerelle · caseworker copy · {now.toLocaleString("de-CH")}</p>
        <h1 style={{ fontSize: "18pt", fontWeight: 600, margin: "4pt 0 2pt" }}>{card?.letter_type ?? a?.title ?? "Letter"}</h1>
        <p style={{ margin: 0 }}>{card?.authority}</p>
        {card?.required_action && (
          <p style={{ marginTop: "10pt" }}>
            <strong>Required action:</strong> {card.required_action}
          </p>
        )}
        <h2 style={{ fontSize: "12pt", marginTop: "14pt" }}>Locked facts</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            {facts.map((f) => (
              <tr key={f.id} style={{ borderTop: "1px solid #ddd" }}>
                <td style={{ padding: "3pt 6pt 3pt 0", fontFamily: "monospace" }}>⟦{f.id}⟧</td>
                <td style={{ padding: "3pt 6pt" }}>{TYPE_LABEL[f.type] ?? f.type}</td>
                <td style={{ padding: "3pt 0", fontWeight: 600 }}>{R(renderFactValue(f))}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {r && (
          <>
            <h2 style={{ fontSize: "12pt", marginTop: "14pt" }}>
              Explanation · {lang?.name} — gate: {GATE_META[r.gate.status].label} (chrF {r.chrf?.toFixed(1) ?? "—"})
            </h2>
            <ul>
              {r.gate.reasons.map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ul>
            <p style={{ whiteSpace: "pre-line" }} lang={lang ? langAttr(lang.code) : undefined} dir={r.rtl ? "rtl" : "ltr"}>
              {R(r.explanation)}
            </p>
            <h2 style={{ fontSize: "12pt", marginTop: "14pt" }}>Back-translation ({a?.letter_lang.toUpperCase()})</h2>
            <p style={{ whiteSpace: "pre-line" }}>{R(r.back_translation)}</p>
            <p>
              Placeholder audit — missing: {r.placeholder_audit.missing.join(", ") || "none"}; duplicated: {r.placeholder_audit.duplicated.join(", ") || "none"}; unexpected: {r.placeholder_audit.unexpected.join(", ") || "none"}
            </p>
          </>
        )}
        {ws.reply.result && (
          <>
            <h2 style={{ fontSize: "12pt", marginTop: "14pt" }}>Draft reply (for approval)</h2>
            <p style={{ whiteSpace: "pre-line", border: "1px solid #ddd", padding: "8pt", borderRadius: 6 }}>{R(ws.reply.result.reply_letter)}</p>
          </>
        )}
        {audit.length > 0 && (
          <>
            <h2 style={{ fontSize: "12pt", marginTop: "14pt" }}>Audit (hashes only)</h2>
            {audit.slice(0, 12).map((e, i) => (
              <p key={i} style={{ margin: 0, fontFamily: "monospace", fontSize: "8pt" }}>
                {e.ts} {e.step} {e.hash}
              </p>
            ))}
          </>
        )}
        <p style={{ marginTop: "16pt", color: "#757170" }}>{redact ? "Names and addresses redacted. " : ""}Synthetic demo data. Not legal advice; the caseworker is responsible for the final text.</p>
      </div>
    );

  return createPortal(
    <div data-print-root aria-hidden>
      {body}
    </div>,
    document.body,
  );
}
