/**
 * MOCK CORPUS — synthetic Swiss official letters (fictional offices, people, numbers).
 * Used only when NEXT_PUBLIC_DATA_SOURCE=mock. Spans are computed from literal values,
 * so the highlight offsets always match the text.
 */
import type { Disagreement, Fact, FactCard, LetterLang } from "@/lib/api/types";

export interface MockFactSpec {
  id: string;
  type: Fact["type"];
  value: string;
  normalized?: string | null;
  /** which occurrence of `value` in the text (0-based) */
  nth?: number;
  source?: Fact["source"];
}

export interface MockLetter {
  id: string;
  title: string;
  language: LetterLang;
  type: string;
  text: string;
  facts: MockFactSpec[];
  card: FactCard;
  disagreements: Disagreement[];
  /** plain-language explanation in the letter language (masked) — chrF reference */
  reference: string;
}

const L1_TEXT = `Betreibungsamt Aarenfeld
Bahnhofstrasse 14, 3999 Aarenfeld
Telefon 031 000 41 20 · betreibungsamt@aarenfeld.example

Herr
Samuel Tesfay
Lindenweg 7
3999 Aarenfeld

Aarenfeld, 9. Oktober 2026

Zahlungsbefehl – Betreibung Nr. 26-048173

Gläubigerin: Krankenkasse Helvetia Mutual AG (fiktiv), Postfach, 8000 Zürich
Forderung: CHF 1'248.60 nebst Zins zu 5 % seit 1. Juli 2026
Grund der Forderung: ausstehende Krankenkassenprämien April bis Juni 2026
Kosten des Zahlungsbefehls: CHF 73.30

Sehr geehrter Herr Tesfay

Sie werden aufgefordert, die Gläubigerin für die oben genannte Forderung samt Kosten innert 20 Tagen zu befriedigen.

Wenn Sie die Forderung ganz oder teilweise bestreiten, müssen Sie innert 10 Tagen nach Zustellung dieses Zahlungsbefehls beim Betreibungsamt Rechtsvorschlag erheben. Der Rechtsvorschlag kann mündlich oder schriftlich erfolgen und muss nicht begründet werden.

Zustellung: 12.10.2026. Letzter Tag für den Rechtsvorschlag: 22.10.2026.

Wenn Sie weder bezahlen noch Rechtsvorschlag erheben, kann die Gläubigerin die Fortsetzung der Betreibung verlangen (Pfändung).

Zahlung an: IBAN CH56 0000 0000 0048 1730 2, Referenz 26-048173

Schalteröffnungszeiten: Montag bis Freitag, 08:30–11:30 Uhr

Freundliche Grüsse
Betreibungsamt Aarenfeld
M. Gerber, Sachbearbeiterin`;

const L2_TEXT = `Commune de Montreval
Contrôle des habitants et Service des étrangers
Place du Marché 3, 1999 Montreval
Tél. 021 000 62 15 · population@montreval.example

Madame
Amina Haidari
Chemin des Vergers 12
1999 Montreval

Montreval, le 6 octobre 2026

Notre référence : SPOP-2026-11872
Concerne : renouvellement de votre autorisation de séjour (permis B)

Madame,

Votre autorisation de séjour arrive à échéance le 30 novembre 2026. Afin de procéder à son renouvellement, nous vous prions de vous présenter personnellement à notre guichet le 4 novembre 2026 à 09h30.

Veuillez apporter les documents suivants :
– votre passeport valable ;
– votre permis de séjour actuel ;
– une photo d'identité récente ;
– une attestation de votre employeur ou du service social.

Un émolument de CHF 95.– sera perçu au guichet (carte ou espèces).

Si vous ne pouvez pas venir à ce rendez-vous, merci de nous contacter au plus tard le 28 octobre 2026. Sans nouvelles de votre part, votre dossier pourra être transmis au Service cantonal des migrations, ce qui peut retarder le renouvellement.

Nous vous prions d'agréer, Madame, nos salutations distinguées.

Le chef de service
P. Rochat`;

const L3_TEXT = `Comune di Valdora
Servizio sociale comunale
Via San Gottardo 21, 6999 Valdora
Tel. 091 000 33 80 · sociale@valdora.example

Egregio Signor
Kumaran Selvarajah
Via ai Ronchi 5
6999 Valdora

Valdora, 7 ottobre 2026

Rif.: SOC-2026/0457
Oggetto: convocazione per il riesame del diritto alle prestazioni di assistenza

Egregio Signor Selvarajah,

nell'ambito del riesame annuale della Sua situazione, La invitiamo a un colloquio presso il nostro servizio il 12 novembre 2026 alle ore 14:00.

La preghiamo di portare:
– gli estratti conto bancari degli ultimi 3 mesi;
– il contratto di locazione e la ricevuta dell'affitto di ottobre;
– la polizza della cassa malati 2027.

L'importo mensile attualmente versato è di CHF 1'986.00.

Se non può presentarsi, La preghiamo di avvisarci entro il 5 novembre 2026. In caso di assenza ingiustificata, le prestazioni possono essere sospese.

Distinti saluti

Servizio sociale comunale
L. Bernasconi, assistente sociale`;

const L4_TEXT = `Sozialversicherungsamt des Kantons Nordwald
Prämienverbilligung
Hofgasse 2, 4999 Nordwald
Telefon 061 000 75 00 · ipv@nordwald.example

Frau
Olena Kovalenko
Rosenweg 18
4999 Nordwald

Nordwald, 5. Oktober 2026

AHV-Nr. 756.1234.5678.97
Dossier: IPV-2027-30561

Individuelle Prämienverbilligung 2027 – fehlende Unterlagen

Sehr geehrte Frau Kovalenko

Sie haben Anspruch auf eine Prämienverbilligung für die obligatorische Krankenversicherung. Nach unserer vorläufigen Berechnung beträgt die Verbilligung CHF 186.00 pro Monat.

Damit wir die Verbilligung ab 1. Januar 2027 auszahlen können, benötigen wir bis spätestens 30.11.2026 folgende Unterlagen:
– Kopie der aktuellen Steuerveranlagung oder Bestätigung des Sozialdienstes;
– Kopie des Mietvertrags;
– Kopie der Krankenkassen-Police 2027.

Fehlen die Unterlagen nach dieser Frist, verfällt der Anspruch für das Jahr 2027.

Für Fragen erreichen Sie uns Montag bis Donnerstag, 09:00–12:00 Uhr.

Freundliche Grüsse
Sozialversicherungsamt des Kantons Nordwald`;

export const MOCK_LETTERS: MockLetter[] = [
  {
    id: "de-betreibung-zahlungsbefehl",
    title: "Zahlungsbefehl (payment order)",
    language: "de",
    type: "Debt enforcement · Betreibung",
    text: L1_TEXT,
    facts: [
      { id: "L1", type: "address", value: "Bahnhofstrasse 14, 3999 Aarenfeld" },
      { id: "P1", type: "phone", value: "031 000 41 20", normalized: "+41310004120" },
      { id: "N1", type: "name", value: "Samuel Tesfay" },
      { id: "L2", type: "address", value: "Lindenweg 7\n3999 Aarenfeld" },
      { id: "D1", type: "date", value: "9. Oktober 2026", normalized: "2026-10-09" },
      { id: "R1", type: "reference", value: "26-048173" },
      { id: "A1", type: "amount", value: "CHF 1'248.60", normalized: "1248.60 CHF" },
      { id: "D2", type: "date", value: "1. Juli 2026", normalized: "2026-07-01" },
      { id: "A2", type: "amount", value: "CHF 73.30", normalized: "73.30 CHF" },
      { id: "D6", type: "deadline", value: "innert 20 Tagen", normalized: "2026-11-01", source: "both" },
      { id: "D5", type: "deadline", value: "innert 10 Tagen", normalized: "2026-10-22", source: "both" },
      { id: "D3", type: "date", value: "12.10.2026", normalized: "2026-10-12" },
      { id: "D4", type: "deadline", value: "22.10.2026", normalized: "2026-10-22", source: "both" },
      { id: "I1", type: "iban", value: "CH56 0000 0000 0048 1730 2", normalized: "CH5600000000004817302" },
      { id: "T1", type: "time", value: "08:30–11:30 Uhr", normalized: "08:30-11:30" },
    ],
    card: {
      authority: "Betreibungsamt Aarenfeld (debt enforcement office)",
      letter_type: "Payment order · Zahlungsbefehl",
      summary: "A health insurer claims unpaid premiums (April–June 2026) through debt enforcement.",
      required_action:
        "Either pay the claim plus costs within 20 days, or file an objection (Rechtsvorschlag) at the office within 10 days of delivery if the debt is disputed. No reason needs to be given.",
      deadlines: [
        { label: "Objection (Rechtsvorschlag)", date: "2026-10-22", relative: "innert 10 Tagen nach Zustellung", fact_id: "D4" },
        { label: "Payment", date: "2026-11-01", relative: "innert 20 Tagen", fact_id: "D6" },
      ],
      amounts: [
        { label: "Claim", value: 1248.6, currency: "CHF", fact_id: "A1" },
        { label: "Cost of the payment order", value: 73.3, currency: "CHF", fact_id: "A2" },
      ],
      reference_numbers: [
        { label: "Betreibung Nr.", value: "26-048173", fact_id: "R1" },
        { label: "IBAN", value: "CH56 0000 0000 0048 1730 2", fact_id: "I1" },
      ],
      documents_to_bring: ["The payment order itself when objecting in person", "Proof of any premium already paid"],
      consequences: "If neither paid nor objected, the creditor can continue enforcement (seizure of wages or belongings).",
      contact: {
        name: "M. Gerber, Sachbearbeiterin",
        phone: "031 000 41 20",
        email: "betreibungsamt@aarenfeld.example",
        address: "Bahnhofstrasse 14, 3999 Aarenfeld",
        hours: "Mon–Fri 08:30–11:30",
      },
    },
    disagreements: [
      {
        field: "Payment deadline",
        deterministic: "2026-11-01 (20 days after delivery 12.10.2026)",
        llm: "2026-10-29 (20 days after letter date)",
        note: "Counted from delivery, as the letter states. Check the delivery date with the client.",
      },
    ],
    reference:
      "Dieser Brief kommt vom Betreibungsamt Aarenfeld. Es ist ein Zahlungsbefehl: Eine Krankenkasse sagt, dass Sie ⟦A1⟧ für nicht bezahlte Prämien schulden, plus ⟦A2⟧ Kosten. Was Sie tun müssen: Wenn Sie einverstanden sind, bezahlen Sie bis ⟦D6⟧ auf das Konto ⟦I1⟧ mit der Referenz ⟦R1⟧. Wenn Sie nicht einverstanden sind, müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben. Das geht mündlich oder schriftlich, Sie müssen keinen Grund angeben. Wenn Sie nichts tun: Die Krankenkasse kann die Betreibung fortsetzen, und ein Teil Ihres Lohns oder Ihrer Sachen kann gepfändet werden. Wer hilft: das Amt an der ⟦L1⟧, Telefon ⟦P1⟧, Montag bis Freitag ⟦T1⟧. Auch eine Sozialberatung kann Ihnen helfen.",
  },
  {
    id: "fr-permis-renouvellement",
    title: "Renouvellement du permis B",
    language: "fr",
    type: "Residence permit · Permis de séjour",
    text: L2_TEXT,
    facts: [
      { id: "L1", type: "address", value: "Place du Marché 3, 1999 Montreval" },
      { id: "P1", type: "phone", value: "021 000 62 15", normalized: "+41210006215" },
      { id: "N1", type: "name", value: "Amina Haidari" },
      { id: "L2", type: "address", value: "Chemin des Vergers 12\n1999 Montreval" },
      { id: "D1", type: "date", value: "6 octobre 2026", normalized: "2026-10-06" },
      { id: "R1", type: "reference", value: "SPOP-2026-11872" },
      { id: "D2", type: "date", value: "30 novembre 2026", normalized: "2026-11-30" },
      { id: "D3", type: "deadline", value: "4 novembre 2026", normalized: "2026-11-04", source: "both" },
      { id: "T1", type: "time", value: "09h30", normalized: "09:30" },
      { id: "A1", type: "amount", value: "CHF 95.–", normalized: "95.00 CHF" },
      { id: "D4", type: "deadline", value: "28 octobre 2026", normalized: "2026-10-28", source: "both" },
    ],
    card: {
      authority: "Commune de Montreval — Contrôle des habitants et Service des étrangers",
      letter_type: "Residence permit renewal · Permis B",
      summary: "The B permit expires on 30 November 2026; an in-person appointment is booked for the renewal.",
      required_action: "Attend the appointment in person with the listed documents and pay the fee at the counter.",
      deadlines: [
        { label: "Appointment at the counter", date: "2026-11-04", relative: "le 4 novembre 2026 à 09h30", fact_id: "D3" },
        { label: "Cancel or reschedule by", date: "2026-10-28", relative: "au plus tard le 28 octobre 2026", fact_id: "D4" },
        { label: "Permit expires", date: "2026-11-30", relative: null, fact_id: "D2" },
      ],
      amounts: [{ label: "Fee (card or cash)", value: 95, currency: "CHF", fact_id: "A1" }],
      reference_numbers: [{ label: "Notre référence", value: "SPOP-2026-11872", fact_id: "R1" }],
      documents_to_bring: [
        "Valid passport",
        "Current residence permit",
        "Recent passport photo",
        "Certificate from the employer or the social service",
      ],
      consequences: "Without a reply the file may be passed to the cantonal migration service, which can delay the renewal.",
      contact: {
        name: "P. Rochat, chef de service",
        phone: "021 000 62 15",
        email: "population@montreval.example",
        address: "Place du Marché 3, 1999 Montreval",
        hours: null,
      },
    },
    disagreements: [],
    reference:
      "Cette lettre vient de la commune de Montreval. Votre permis de séjour se termine le ⟦D2⟧. Pour le renouveler, vous devez venir au guichet le ⟦D3⟧ à ⟦T1⟧. Apportez votre passeport, votre permis actuel, une photo et une attestation de votre employeur ou du service social. Vous payez ⟦A1⟧ au guichet. Si vous ne pouvez pas venir, appelez le ⟦P1⟧ avant le ⟦D4⟧. Donnez la référence ⟦R1⟧. Si vous ne répondez pas, le renouvellement peut prendre plus de temps. Adresse du guichet : ⟦L1⟧.",
  },
  {
    id: "it-sociale-convocazione",
    title: "Convocazione servizio sociale",
    language: "it",
    type: "Social assistance · Assistenza",
    text: L3_TEXT,
    facts: [
      { id: "L1", type: "address", value: "Via San Gottardo 21, 6999 Valdora" },
      { id: "P1", type: "phone", value: "091 000 33 80", normalized: "+41910003380" },
      { id: "N1", type: "name", value: "Kumaran Selvarajah" },
      { id: "L2", type: "address", value: "Via ai Ronchi 5\n6999 Valdora" },
      { id: "D1", type: "date", value: "7 ottobre 2026", normalized: "2026-10-07" },
      { id: "R1", type: "reference", value: "SOC-2026/0457" },
      { id: "D2", type: "deadline", value: "12 novembre 2026", normalized: "2026-11-12", source: "both" },
      { id: "T1", type: "time", value: "14:00", normalized: "14:00" },
      { id: "A1", type: "amount", value: "CHF 1'986.00", normalized: "1986.00 CHF" },
      { id: "D3", type: "deadline", value: "5 novembre 2026", normalized: "2026-11-05", source: "both" },
    ],
    card: {
      authority: "Comune di Valdora — Servizio sociale comunale",
      letter_type: "Appointment · Annual review of social assistance",
      summary: "Annual review of entitlement to social assistance; an interview is scheduled.",
      required_action: "Attend the interview with bank statements, the rent contract and receipt, and the 2027 health-insurance policy.",
      deadlines: [
        { label: "Interview", date: "2026-11-12", relative: "il 12 novembre 2026 alle ore 14:00", fact_id: "D2" },
        { label: "Tell the office if you cannot come", date: "2026-11-05", relative: "entro il 5 novembre 2026", fact_id: "D3" },
      ],
      amounts: [{ label: "Current monthly payment", value: 1986, currency: "CHF", fact_id: "A1" }],
      reference_numbers: [{ label: "Rif.", value: "SOC-2026/0457", fact_id: "R1" }],
      documents_to_bring: [
        "Bank statements for the last 3 months",
        "Rent contract and October rent receipt",
        "Health-insurance policy 2027",
      ],
      consequences: "If absent without a valid reason, benefits can be suspended.",
      contact: {
        name: "L. Bernasconi, assistente sociale",
        phone: "091 000 33 80",
        email: "sociale@valdora.example",
        address: "Via San Gottardo 21, 6999 Valdora",
        hours: null,
      },
    },
    disagreements: [],
    reference:
      "Questa lettera viene dal servizio sociale del Comune di Valdora. Ogni anno controllano il Suo diritto all'aiuto sociale. Lei deve venire a un colloquio il ⟦D2⟧ alle ⟦T1⟧, all'indirizzo ⟦L1⟧. Porti gli estratti conto della banca degli ultimi 3 mesi, il contratto d'affitto con la ricevuta di ottobre e la polizza della cassa malati 2027. Oggi riceve ⟦A1⟧ al mese. Se non può venire, telefoni al ⟦P1⟧ entro il ⟦D3⟧ e indichi il riferimento ⟦R1⟧. Se non viene senza un buon motivo, l'aiuto può essere sospeso.",
  },
  {
    id: "de-praemienverbilligung",
    title: "Prämienverbilligung 2027",
    language: "de",
    type: "Health insurance subsidy · IPV",
    text: L4_TEXT,
    facts: [
      { id: "L1", type: "address", value: "Hofgasse 2, 4999 Nordwald" },
      { id: "P1", type: "phone", value: "061 000 75 00", normalized: "+41610007500" },
      { id: "N1", type: "name", value: "Olena Kovalenko" },
      { id: "L2", type: "address", value: "Rosenweg 18\n4999 Nordwald" },
      { id: "D1", type: "date", value: "5. Oktober 2026", normalized: "2026-10-05" },
      { id: "V1", type: "ahv", value: "756.1234.5678.97", normalized: "7561234567897" },
      { id: "R1", type: "reference", value: "IPV-2027-30561" },
      { id: "A1", type: "amount", value: "CHF 186.00", normalized: "186.00 CHF" },
      { id: "D2", type: "date", value: "1. Januar 2027", normalized: "2027-01-01" },
      { id: "D3", type: "deadline", value: "30.11.2026", normalized: "2026-11-30", source: "both" },
      { id: "T1", type: "time", value: "09:00–12:00 Uhr", normalized: "09:00-12:00" },
    ],
    card: {
      authority: "Sozialversicherungsamt des Kantons Nordwald",
      letter_type: "Health-insurance premium subsidy · missing documents",
      summary: "Entitled to a premium subsidy for 2027; documents are missing.",
      required_action: "Send copies of the tax assessment (or social-service confirmation), the rent contract and the 2027 insurance policy.",
      deadlines: [{ label: "Send documents by", date: "2026-11-30", relative: "bis spätestens 30.11.2026", fact_id: "D3" }],
      amounts: [{ label: "Subsidy per month (provisional)", value: 186, currency: "CHF", fact_id: "A1" }],
      reference_numbers: [
        { label: "Dossier", value: "IPV-2027-30561", fact_id: "R1" },
        { label: "AHV-Nr.", value: "756.1234.5678.97", fact_id: "V1" },
      ],
      documents_to_bring: ["Tax assessment or social-service confirmation", "Rent contract", "Health-insurance policy 2027"],
      consequences: "If the documents are missing after the deadline, the 2027 entitlement lapses.",
      contact: { name: null, phone: "061 000 75 00", email: "ipv@nordwald.example", address: "Hofgasse 2, 4999 Nordwald", hours: "Mon–Thu 09:00–12:00" },
    },
    disagreements: [],
    reference:
      "Dieser Brief kommt vom Sozialversicherungsamt Nordwald. Sie bekommen Geld für die Krankenkasse: etwa ⟦A1⟧ pro Monat ab ⟦D2⟧. Dafür müssen Sie bis ⟦D3⟧ drei Kopien schicken: die Steuerveranlagung oder eine Bestätigung vom Sozialdienst, den Mietvertrag und die Krankenkassen-Police 2027. Schreiben Sie die Nummer ⟦R1⟧ dazu. Wenn die Unterlagen zu spät kommen, bekommen Sie 2027 kein Geld. Fragen: Telefon ⟦P1⟧, Montag bis Donnerstag ⟦T1⟧.",
  },
];

export function buildFacts(letter: MockLetter): Fact[] {
  return letter.facts.map((f) => {
    let from = 0;
    let idx = -1;
    for (let i = 0; i <= (f.nth ?? 0); i++) {
      idx = letter.text.indexOf(f.value, from);
      if (idx === -1) break;
      from = idx + f.value.length;
    }
    return {
      id: f.id,
      type: f.type,
      value: f.value.replace(/\n/g, ", "),
      normalized: f.normalized ?? null,
      span: idx >= 0 ? ([idx, idx + f.value.length] as [number, number]) : null,
      source: f.source ?? "deterministic",
    };
  });
}
