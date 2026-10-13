/** Word-level LCS diff. Returns, for each side, which tokens are shared with the other side. */
export interface DiffToken {
  text: string;
  shared: boolean;
}

function tokenize(s: string): string[] {
  // keep placeholders and whitespace as their own tokens
  return s.match(/⟦[A-Z]{1,3}\d{1,3}⟧|\s+|[^\s⟦]+/g) ?? [];
}

const norm = (t: string) => t.toLowerCase().replace(/[.,;:!?()«»"'’]/g, "");

export function wordDiff(a: string, b: string): { a: DiffToken[]; b: DiffToken[] } {
  const ta = tokenize(a);
  const tb = tokenize(b);
  const wa = ta.map((t, i) => ({ t, i })).filter((x) => !/^\s+$/.test(x.t));
  const wb = tb.map((t, i) => ({ t, i })).filter((x) => !/^\s+$/.test(x.t));
  const n = wa.length;
  const m = wb.length;
  // guard against pathological sizes
  if (n * m > 400_000) return { a: ta.map((text) => ({ text, shared: true })), b: tb.map((text) => ({ text, shared: true })) };
  const dp: Uint16Array[] = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--) dp[i][j] = norm(wa[i].t) === norm(wb[j].t) ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const sa = new Set<number>();
  const sb = new Set<number>();
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (norm(wa[i].t) === norm(wb[j].t)) {
      sa.add(wa[i].i);
      sb.add(wb[j].i);
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
    else j++;
  }
  return {
    a: ta.map((text, k) => ({ text, shared: /^\s+$/.test(text) || sa.has(k) })),
    b: tb.map((text, k) => ({ text, shared: /^\s+$/.test(text) || sb.has(k) })),
  };
}
