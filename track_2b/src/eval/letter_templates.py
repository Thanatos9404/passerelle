"""Hand-written templates for 12 types of Swiss official letters in German, French and Italian.

All authorities, places, people, accounts and numbers are fictional (filled in by make_letters.py).
Slots in {braces} are filled per instance; every fact-bearing slot is recorded in the ground truth.
Licence of the generated data: CDLA-Permissive-2.0.
"""

HEADER = {
    "de": "{auth_name}\n{auth_dept}\n{auth_street}\n{auth_postal}\n{phone_label} {auth_phone}\n{auth_email}\n\n"
          "{rcp_title}\n{rcp_name}\n{rcp_street}\n{rcp_postal}\n\n{place}, {letter_date}\n\n",
    "fr": "{auth_name}\n{auth_dept}\n{auth_street}\n{auth_postal}\n{phone_label} {auth_phone}\n{auth_email}\n\n"
          "{rcp_title}\n{rcp_name}\n{rcp_street}\n{rcp_postal}\n\n{place}, le {letter_date}\n\n",
    "it": "{auth_name}\n{auth_dept}\n{auth_street}\n{auth_postal}\n{phone_label} {auth_phone}\n{auth_email}\n\n"
          "{rcp_title}\n{rcp_name}\n{rcp_street}\n{rcp_postal}\n\n{place}, {letter_date}\n\n",
}

T: dict[str, dict] = {}

# ----------------------------------------------------------------------------------------- 1
T["tax_reminder"] = {
    "auth": {"de": "Gemeinde {commune}", "fr": "Commune de {commune}", "it": "Comune di {commune}"},
    "dept": {"de": "Steueramt", "fr": "Office des impôts", "it": "Ufficio di tassazione"},
    "title": {"de": "Mahnung Steuererklärung", "fr": "Rappel déclaration d'impôt", "it": "Richiamo dichiarazione d'imposta"},
    "body": {
        "de": """Steuernummer: {ref}

Mahnung: Steuererklärung {tax_year}

{salutation}

Gemäss unseren Unterlagen haben Sie die Steuererklärung {tax_year} trotz unserer Aufforderung noch nicht eingereicht.

Wir fordern Sie auf, die vollständig ausgefüllte und unterschriebene Steuererklärung mit allen Belegen bis spätestens {deadline} einzureichen. Sie können die Steuererklärung auch online ausfüllen.

Wenn Sie die Frist nicht einhalten, werden Sie nach pflichtgemässem Ermessen eingeschätzt. Zudem kann eine Ordnungsbusse von bis zu {fine} verhängt werden. Für diese Mahnung verrechnen wir eine Gebühr von {fee}.

Bei Fragen hilft Ihnen {contact} gerne weiter (Telefon {auth_phone}).

Freundliche Grüsse

Steueramt {commune}""",
        "fr": """N° de contribuable : {ref}

Rappel : déclaration d'impôt {tax_year}

{salutation}

Selon nos dossiers, vous n'avez pas encore déposé votre déclaration d'impôt {tax_year}, malgré notre invitation.

Nous vous prions de nous retourner la déclaration dûment remplie et signée, avec toutes les pièces justificatives, au plus tard le {deadline}. Vous pouvez aussi remplir la déclaration en ligne.

À défaut, vous serez taxé(e) d'office et une amende d'ordre pouvant aller jusqu'à {fine} pourra être prononcée. Des frais de rappel de {fee} vous sont facturés.

Pour toute question, {contact} se tient à votre disposition au {auth_phone}.

Veuillez agréer, {salutation_close}, nos salutations distinguées.

Office des impôts de {commune}""",
        "it": """N. contribuente: {ref}

Richiamo: dichiarazione d'imposta {tax_year}

{salutation}

Dai nostri atti risulta che, nonostante il nostro invito, non ha ancora inoltrato la dichiarazione d'imposta {tax_year}.

La invitiamo a trasmetterci la dichiarazione completa e firmata, con tutti i documenti giustificativi, entro il {deadline}. Può compilare la dichiarazione anche online.

In caso contrario sarà tassato/a d'ufficio e potrà esserle inflitta una multa disciplinare fino a {fine}. Per il presente richiamo le addebitiamo una tassa di {fee}.

Per domande può rivolgersi a {contact}, telefono {auth_phone}.

Distinti saluti

Ufficio di tassazione di {commune}""",
    },
    "action": {"de": "Steuererklärung mit Belegen einreichen", "fr": "Déposer la déclaration d'impôt avec les pièces", "it": "Inoltrare la dichiarazione d'imposta con i giustificativi"},
    "consequence": {"de": "Ermessenseinschätzung und Ordnungsbusse", "fr": "Taxation d'office et amende d'ordre", "it": "Tassazione d'ufficio e multa disciplinare"},
    "documents": {"de": ["Steuererklärung", "Belege"], "fr": ["déclaration d'impôt", "pièces justificatives"], "it": ["dichiarazione d'imposta", "documenti giustificativi"]},
}

# ----------------------------------------------------------------------------------------- 2
T["premium_reduction"] = {
    "auth": {"de": "Sozialversicherungsanstalt Kanton {canton}", "fr": "Caisse cantonale de compensation {canton}", "it": "Istituto delle assicurazioni sociali {canton}"},
    "dept": {"de": "Prämienverbilligung", "fr": "Subsides d'assurance-maladie", "it": "Riduzione dei premi"},
    "title": {"de": "Verfügung Prämienverbilligung", "fr": "Décision subside d'assurance-maladie", "it": "Decisione riduzione dei premi"},
    "body": {
        "de": """Versichertennummer: {ref}
AHV-Nr.: {ahv}

Verfügung über die individuelle Prämienverbilligung {year_next}

{salutation}

Sie haben Anspruch auf eine Prämienverbilligung für die obligatorische Krankenversicherung. Ab {effective} beträgt die Verbilligung {amount_month} pro Monat. Der Betrag wird direkt an Ihre Krankenkasse überwiesen und mit Ihren Prämien verrechnet.

Damit wir den Anspruch für das ganze Jahr bestätigen können, benötigen wir bis {deadline} folgende Unterlagen:
- Kopie der aktuellen Steuerveranlagung
- Kopie Ihres Mietvertrags

Reichen Sie die Unterlagen nicht fristgerecht ein, wird die Prämienverbilligung ab {stop_date} eingestellt.

Gegen diese Verfügung können Sie innert {objection_days} Tagen schriftlich Einsprache erheben.

Auskunft: Telefon {auth_phone}, {auth_email}

Freundliche Grüsse
Sozialversicherungsanstalt Kanton {canton}""",
        "fr": """N° d'assuré : {ref}
N° AVS : {ahv}

Décision relative au subside d'assurance-maladie {year_next}

{salutation}

Vous avez droit à un subside pour les primes de l'assurance obligatoire des soins. Dès le {effective}, le subside s'élève à {amount_month} par mois. Le montant est versé directement à votre caisse-maladie et déduit de vos primes.

Afin de confirmer votre droit pour toute l'année, nous avons besoin des documents suivants d'ici au {deadline} :
- copie de votre dernière décision de taxation
- copie de votre bail à loyer

Sans ces documents dans le délai, le subside sera supprimé dès le {stop_date}.

Vous pouvez former opposition par écrit contre cette décision dans les {objection_days} jours.

Renseignements : tél. {auth_phone}, {auth_email}

Avec nos meilleures salutations
Caisse cantonale de compensation {canton}""",
        "it": """N. assicurato: {ref}
N. AVS: {ahv}

Decisione sulla riduzione individuale dei premi {year_next}

{salutation}

Lei ha diritto a una riduzione dei premi dell'assicurazione malattie obbligatoria. Dal {effective} la riduzione ammonta a {amount_month} al mese. L'importo viene versato direttamente alla Sua cassa malati e dedotto dai premi.

Per confermare il diritto per tutto l'anno ci occorrono entro il {deadline} i seguenti documenti:
- copia dell'ultima notifica di tassazione
- copia del contratto di locazione

Se i documenti non ci pervengono entro il termine, la riduzione sarà sospesa dal {stop_date}.

Contro la presente decisione può presentare reclamo scritto entro {objection_days} giorni.

Informazioni: tel. {auth_phone}, {auth_email}

Distinti saluti
Istituto delle assicurazioni sociali {canton}""",
    },
    "action": {"de": "Steuerveranlagung und Mietvertrag einreichen", "fr": "Envoyer décision de taxation et bail", "it": "Inviare notifica di tassazione e contratto di locazione"},
    "consequence": {"de": "Prämienverbilligung wird eingestellt", "fr": "Le subside est supprimé", "it": "La riduzione viene sospesa"},
    "documents": {"de": ["Steuerveranlagung", "Mietvertrag"], "fr": ["décision de taxation", "bail à loyer"], "it": ["notifica di tassazione", "contratto di locazione"]},
}

# ----------------------------------------------------------------------------------------- 3
T["permit_renewal"] = {
    "auth": {"de": "Migrationsamt des Kantons {canton}", "fr": "Service de la population et des migrants {canton}", "it": "Ufficio della migrazione del Cantone {canton}"},
    "dept": {"de": "Abteilung Aufenthalt", "fr": "Secteur séjour", "it": "Settore permessi"},
    "title": {"de": "Verlängerung Aufenthaltsbewilligung B", "fr": "Renouvellement autorisation de séjour B", "it": "Rinnovo permesso di dimora B"},
    "body": {
        "de": """Dossier-Nr.: {ref}
ZEMIS-Nr.: {zemis}

Verlängerung Ihrer Aufenthaltsbewilligung B

{salutation}

Ihre Aufenthaltsbewilligung B läuft am {expiry} ab. Wenn Sie weiterhin in der Schweiz wohnen möchten, müssen Sie die Verlängerung beantragen.

Bitte senden Sie uns das beiliegende Formular bis {deadline} zusammen mit folgenden Unterlagen:
- Kopie des gültigen Reisepasses
- ein aktuelles Passfoto
- Kopie des Arbeitsvertrags oder Bestätigung der Sozialhilfe
- Kopie des Mietvertrags

Die Gebühr für die Verlängerung beträgt {fee}. Bitte bezahlen Sie den Betrag mit dem beiliegenden Einzahlungsschein (IBAN {iban}).

Wenn Sie die Verlängerung nicht rechtzeitig beantragen, halten Sie sich ohne gültige Bewilligung in der Schweiz auf. Dies kann ausländerrechtliche Massnahmen zur Folge haben.

Für Fragen: Telefon {auth_phone}, Montag bis Freitag, {open_from} bis {open_to}

Freundliche Grüsse
Migrationsamt des Kantons {canton}""",
        "fr": """Dossier n° : {ref}
N° SYMIC : {zemis}

Renouvellement de votre autorisation de séjour B

{salutation}

Votre autorisation de séjour B arrive à échéance le {expiry}. Si vous souhaitez continuer à résider en Suisse, vous devez en demander le renouvellement.

Nous vous prions de nous retourner le formulaire ci-joint d'ici au {deadline}, accompagné des documents suivants :
- copie de votre passeport valable
- une photo d'identité récente
- copie de votre contrat de travail ou attestation de l'aide sociale
- copie de votre bail à loyer

L'émolument pour le renouvellement s'élève à {fee}. Veuillez le régler au moyen du bulletin de versement annexé (IBAN {iban}).

Si vous ne demandez pas le renouvellement à temps, vous séjournerez en Suisse sans autorisation valable, ce qui peut entraîner des mesures relevant du droit des étrangers.

Renseignements : tél. {auth_phone}, du lundi au vendredi de {open_from} à {open_to}

Nous vous prions d'agréer, {salutation_close}, nos salutations distinguées.""",
        "it": """Incarto n.: {ref}
N. SIMIC: {zemis}

Rinnovo del permesso di dimora B

{salutation}

Il Suo permesso di dimora B scade il {expiry}. Se desidera continuare a vivere in Svizzera, deve chiederne il rinnovo.

La preghiamo di inviarci il modulo allegato entro il {deadline}, insieme ai seguenti documenti:
- copia del passaporto valido
- una fotografia recente
- copia del contratto di lavoro o attestazione dell'assistenza sociale
- copia del contratto di locazione

La tassa per il rinnovo ammonta a {fee}. La preghiamo di pagarla con la polizza di versamento allegata (IBAN {iban}).

Se non chiede il rinnovo in tempo, soggiornerà in Svizzera senza un permesso valido, con possibili misure secondo il diritto degli stranieri.

Informazioni: tel. {auth_phone}, dal lunedì al venerdì dalle {open_from} alle {open_to}

Distinti saluti
Ufficio della migrazione""",
    },
    "action": {"de": "Verlängerungsgesuch mit Unterlagen einreichen und Gebühr bezahlen", "fr": "Demander le renouvellement avec les documents et payer l'émolument", "it": "Chiedere il rinnovo con i documenti e pagare la tassa"},
    "consequence": {"de": "Aufenthalt ohne gültige Bewilligung, ausländerrechtliche Massnahmen", "fr": "Séjour sans autorisation, mesures du droit des étrangers", "it": "Soggiorno senza permesso, misure del diritto degli stranieri"},
    "documents": {"de": ["Reisepass", "Passfoto", "Arbeitsvertrag oder Sozialhilfebestätigung", "Mietvertrag"], "fr": ["passeport", "photo", "contrat de travail ou attestation d'aide sociale", "bail"], "it": ["passaporto", "fotografia", "contratto di lavoro o attestazione assistenza", "contratto di locazione"]},
}

# ----------------------------------------------------------------------------------------- 4
T["social_assistance_appointment"] = {
    "auth": {"de": "Gemeinde {commune}", "fr": "Commune de {commune}", "it": "Comune di {commune}"},
    "dept": {"de": "Sozialdienst", "fr": "Service social", "it": "Servizio sociale"},
    "title": {"de": "Einladung Sozialdienst", "fr": "Convocation service social", "it": "Convocazione servizio sociale"},
    "body": {
        "de": """Fall-Nr.: {ref}

Einladung zu einem Gespräch

{salutation}

Wir laden Sie zu einem Gespräch mit Ihrer Sozialarbeiterin {contact} ein:

Datum: {appt_date}
Zeit: {appt_time}
Ort: Sozialdienst {commune}, {appt_street}, Büro 2.14

Bitte bringen Sie folgende Unterlagen mit:
- Kontoauszüge der letzten drei Monate
- aktuelle Mietzinsrechnung
- Krankenkassenpolice {year_next}
- Lohnabrechnungen, falls Sie arbeiten

Wenn Sie den Termin nicht wahrnehmen können, melden Sie sich bitte bis spätestens {cancel_deadline} unter Telefon {auth_phone}. Wenn Sie ohne Entschuldigung nicht erscheinen, kann die wirtschaftliche Hilfe gekürzt werden.

Freundliche Grüsse
Sozialdienst {commune}""",
        "fr": """Dossier n° : {ref}

Convocation à un entretien

{salutation}

Nous vous convoquons à un entretien avec votre assistante sociale, {contact} :

Date : {appt_date}
Heure : {appt_time}
Lieu : Service social de {commune}, {appt_street}, bureau 2.14

Veuillez apporter les documents suivants :
- relevés bancaires des trois derniers mois
- dernière facture de loyer
- police d'assurance-maladie {year_next}
- fiches de salaire, si vous travaillez

Si vous ne pouvez pas venir, veuillez nous en informer au plus tard le {cancel_deadline} au {auth_phone}. En cas d'absence non excusée, l'aide financière peut être réduite.

Avec nos salutations les meilleures
Service social de {commune}""",
        "it": """Pratica n.: {ref}

Convocazione a un colloquio

{salutation}

La invitiamo a un colloquio con la Sua assistente sociale, {contact}:

Data: {appt_date}
Ora: {appt_time}
Luogo: Servizio sociale di {commune}, {appt_street}, ufficio 2.14

La preghiamo di portare i seguenti documenti:
- estratti conto degli ultimi tre mesi
- ultima fattura dell'affitto
- polizza della cassa malati {year_next}
- buste paga, se lavora

Se non può presentarsi, La preghiamo di avvisarci entro il {cancel_deadline} al numero {auth_phone}. In caso di assenza ingiustificata, l'aiuto economico può essere ridotto.

Cordiali saluti
Servizio sociale di {commune}""",
    },
    "action": {"de": "Zum Gespräch erscheinen und Unterlagen mitbringen", "fr": "Se présenter à l'entretien avec les documents", "it": "Presentarsi al colloquio con i documenti"},
    "consequence": {"de": "Wirtschaftliche Hilfe kann gekürzt werden", "fr": "L'aide financière peut être réduite", "it": "L'aiuto economico può essere ridotto"},
    "documents": {"de": ["Kontoauszüge", "Mietzinsrechnung", "Krankenkassenpolice", "Lohnabrechnungen"], "fr": ["relevés bancaires", "facture de loyer", "police d'assurance-maladie", "fiches de salaire"], "it": ["estratti conto", "fattura dell'affitto", "polizza cassa malati", "buste paga"]},
}

# ----------------------------------------------------------------------------------------- 5
T["school_enrolment"] = {
    "auth": {"de": "Schule {commune}", "fr": "Établissement scolaire de {commune}", "it": "Istituto scolastico di {commune}"},
    "dept": {"de": "Schulverwaltung", "fr": "Administration scolaire", "it": "Direzione scolastica"},
    "title": {"de": "Anmeldung Kindergarten", "fr": "Inscription école enfantine", "it": "Iscrizione scuola dell'infanzia"},
    "body": {
        "de": """Referenz: {ref}

Anmeldung für den Kindergarten, Schuljahr {school_year}

{salutation}

Ihr Kind {child_name}, geboren am {child_birth}, wird im Sommer {year_next} kindergartenpflichtig. Der Kindergarten beginnt am {school_start}.

Bitte melden Sie Ihr Kind bis {deadline} an. Sie können das beiliegende Formular per Post senden oder am Schalter der Schulverwaltung abgeben.

Bitte legen Sie bei:
- Kopie des Familienbüchleins oder der Geburtsurkunde
- Kopie des Impfausweises
- Kopie der Aufenthaltsbewilligung des Kindes

Am {info_date} um {info_time} findet im Schulhaus {school_house} ein Informationsabend für Eltern statt. Es gibt eine Übersetzung in mehrere Sprachen.

Der Besuch des Kindergartens ist obligatorisch. Für Fragen erreichen Sie uns unter {auth_phone} oder {auth_email}.

Freundliche Grüsse
Schulverwaltung {commune}""",
        "fr": """Référence : {ref}

Inscription à l'école enfantine, année scolaire {school_year}

{salutation}

Votre enfant {child_name}, né(e) le {child_birth}, sera en âge de scolarité obligatoire à l'été {year_next}. L'école enfantine commence le {school_start}.

Nous vous prions d'inscrire votre enfant d'ici au {deadline}. Vous pouvez envoyer le formulaire ci-joint par la poste ou le déposer au guichet de l'administration scolaire.

Veuillez joindre :
- copie du livret de famille ou de l'acte de naissance
- copie du carnet de vaccination
- copie du titre de séjour de l'enfant

Une séance d'information pour les parents aura lieu le {info_date} à {info_time} au collège {school_house}. Une traduction dans plusieurs langues sera proposée.

La fréquentation de l'école enfantine est obligatoire. Pour toute question : {auth_phone} ou {auth_email}.

Meilleures salutations
Administration scolaire de {commune}""",
        "it": """Riferimento: {ref}

Iscrizione alla scuola dell'infanzia, anno scolastico {school_year}

{salutation}

Suo figlio/Sua figlia {child_name}, nato/a il {child_birth}, sarà soggetto/a all'obbligo scolastico nell'estate {year_next}. La scuola dell'infanzia inizia il {school_start}.

La preghiamo di iscrivere il bambino entro il {deadline}. Può inviare il modulo allegato per posta o consegnarlo allo sportello della direzione scolastica.

Alleghi per favore:
- copia del libretto di famiglia o dell'atto di nascita
- copia del libretto delle vaccinazioni
- copia del permesso di dimora del bambino

Il {info_date} alle {info_time} si terrà una serata informativa per i genitori presso la sede scolastica {school_house}. Sarà disponibile una traduzione in diverse lingue.

La frequenza della scuola dell'infanzia è obbligatoria. Per domande: {auth_phone} o {auth_email}.

Cordiali saluti
Direzione scolastica di {commune}""",
    },
    "action": {"de": "Kind für den Kindergarten anmelden", "fr": "Inscrire l'enfant à l'école enfantine", "it": "Iscrivere il bambino alla scuola dell'infanzia"},
    "consequence": {"de": "Kindergartenbesuch ist obligatorisch", "fr": "La fréquentation est obligatoire", "it": "La frequenza è obbligatoria"},
    "documents": {"de": ["Familienbüchlein oder Geburtsurkunde", "Impfausweis", "Aufenthaltsbewilligung des Kindes"], "fr": ["livret de famille ou acte de naissance", "carnet de vaccination", "titre de séjour de l'enfant"], "it": ["libretto di famiglia o atto di nascita", "libretto delle vaccinazioni", "permesso di dimora del bambino"]},
}

# ----------------------------------------------------------------------------------------- 6
T["debt_collection"] = {
    "auth": {"de": "Betreibungsamt {commune}", "fr": "Office des poursuites de {commune}", "it": "Ufficio di esecuzione di {commune}"},
    "dept": {"de": "Betreibungen", "fr": "Poursuites", "it": "Esecuzioni"},
    "title": {"de": "Zahlungsbefehl", "fr": "Commandement de payer", "it": "Precetto esecutivo"},
    "body": {
        "de": """Zahlungsbefehl
Betreibung Nr. {ref}

Schuldnerin/Schuldner: {rcp_name}
Gläubigerin: {creditor}

Forderung: {amount_main} nebst Zins zu 5 % seit {interest_from}
Betreibungskosten: {costs}

{salutation}

Die Gläubigerin verlangt von Ihnen die Bezahlung der oben genannten Forderung. Sie werden aufgefordert, die Gläubigerin innert {pay_days} Tagen seit Zustellung zu befriedigen (Zahlung auf IBAN {iban}).

Wenn Sie die Forderung ganz oder teilweise bestreiten, müssen Sie innert {objection_days} Tagen seit Zustellung beim Betreibungsamt Rechtsvorschlag erheben, mündlich oder schriftlich ({legal_ref}).

Wenn Sie weder bezahlen noch Rechtsvorschlag erheben, kann die Gläubigerin die Fortsetzung der Betreibung verlangen (Pfändung).

Schalteröffnungszeiten: Montag bis Freitag, {open_from} bis {open_to}

Betreibungsamt {commune}""",
        "fr": """Commandement de payer
Poursuite n° {ref}

Débiteur/débitrice : {rcp_name}
Créancier : {creditor}

Créance : {amount_main} avec intérêts à 5 % dès le {interest_from}
Frais de poursuite : {costs}

{salutation}

Le créancier vous somme de payer la créance ci-dessus. Vous êtes invité(e) à le satisfaire dans les {pay_days} jours dès la notification (paiement sur IBAN {iban}).

Si vous contestez tout ou partie de la créance, vous devez former opposition auprès de l'office des poursuites dans les {objection_days} jours dès la notification, oralement ou par écrit ({legal_ref}).

Si vous ne payez pas et ne formez pas opposition, le créancier pourra requérir la continuation de la poursuite (saisie).

Heures d'ouverture : du lundi au vendredi, de {open_from} à {open_to}

Office des poursuites de {commune}""",
        "it": """Precetto esecutivo
Esecuzione n. {ref}

Debitore/debitrice: {rcp_name}
Creditore: {creditor}

Credito: {amount_main} più interessi del 5 % dal {interest_from}
Spese esecutive: {costs}

{salutation}

Il creditore Le chiede di pagare il credito indicato. La invitiamo a soddisfare il creditore entro {pay_days} giorni dalla notifica (pagamento sull'IBAN {iban}).

Se contesta il credito in tutto o in parte, deve fare opposizione presso l'Ufficio di esecuzione entro {objection_days} giorni dalla notifica, oralmente o per iscritto ({legal_ref}).

Se non paga e non fa opposizione, il creditore può chiedere la continuazione dell'esecuzione (pignoramento).

Orari di sportello: dal lunedì al venerdì, dalle {open_from} alle {open_to}

Ufficio di esecuzione di {commune}""",
    },
    "action": {"de": "Bezahlen oder innert Frist Rechtsvorschlag erheben", "fr": "Payer ou former opposition dans le délai", "it": "Pagare o fare opposizione entro il termine"},
    "consequence": {"de": "Fortsetzung der Betreibung (Pfändung)", "fr": "Continuation de la poursuite (saisie)", "it": "Continuazione dell'esecuzione (pignoramento)"},
    "documents": {"de": [], "fr": [], "it": []},
}

# ----------------------------------------------------------------------------------------- 7
T["rent_increase"] = {
    "auth": {"de": "{agency}", "fr": "{agency}", "it": "{agency}"},
    "dept": {"de": "Bewirtschaftung", "fr": "Gérance", "it": "Gestione stabili"},
    "title": {"de": "Mietzinserhöhung", "fr": "Majoration de loyer", "it": "Aumento della pigione"},
    "body": {
        "de": """Mieter-Nr.: {ref}
Objekt: {rcp_street}, 3. Obergeschoss links

Mitteilung einer Mietzinserhöhung

{salutation}

Gestützt auf die Anpassung des hypothekarischen Referenzzinssatzes erhöhen wir den Nettomietzins Ihrer Wohnung per {effective}.

Bisheriger Nettomietzins: {rent_old} pro Monat
Neuer Nettomietzins: {rent_new} pro Monat
Nebenkosten (unverändert): {extra_costs} pro Monat

Die Erhöhung wird auf dem beiliegenden amtlichen Formular mitgeteilt. Wenn Sie die Erhöhung für missbräuchlich halten, können Sie sie innert {contest_days} Tagen nach Empfang bei der Schlichtungsbehörde in Mietsachen anfechten, {conc_street}, {conc_postal} ({legal_ref}).

Wenn Sie nicht reagieren, gilt ab {effective} der neue Mietzins.

Für Fragen: {contact}, Telefon {auth_phone}, {auth_email}

Freundliche Grüsse
{agency}""",
        "fr": """N° de locataire : {ref}
Objet : {rcp_street}, 3e étage gauche

Avis de majoration de loyer

{salutation}

En raison de l'adaptation du taux d'intérêt hypothécaire de référence, nous augmentons le loyer net de votre appartement dès le {effective}.

Loyer net actuel : {rent_old} par mois
Nouveau loyer net : {rent_new} par mois
Charges (inchangées) : {extra_costs} par mois

La majoration vous est notifiée sur la formule officielle ci-jointe. Si vous estimez cette hausse abusive, vous pouvez la contester dans les {contest_days} jours dès réception auprès de la Commission de conciliation en matière de baux et loyers, {conc_street}, {conc_postal} ({legal_ref}).

Sans réaction de votre part, le nouveau loyer sera dû dès le {effective}.

Pour toute question : {contact}, tél. {auth_phone}, {auth_email}

Veuillez agréer, {salutation_close}, nos salutations distinguées.
{agency}""",
        "it": """N. inquilino: {ref}
Oggetto: {rcp_street}, 3° piano a sinistra

Avviso di aumento della pigione

{salutation}

In seguito all'adeguamento del tasso d'interesse ipotecario di riferimento, aumentiamo la pigione netta del Suo appartamento a partire dal {effective}.

Pigione netta attuale: {rent_old} al mese
Nuova pigione netta: {rent_new} al mese
Spese accessorie (invariate): {extra_costs} al mese

L'aumento Le viene notificato con il modulo ufficiale allegato. Se ritiene l'aumento abusivo, può contestarlo entro {contest_days} giorni dalla ricezione presso l'Ufficio di conciliazione in materia di locazione, {conc_street}, {conc_postal} ({legal_ref}).

Senza Sua reazione, la nuova pigione sarà dovuta dal {effective}.

Per domande: {contact}, tel. {auth_phone}, {auth_email}

Distinti saluti
{agency}""",
    },
    "action": {"de": "Neuen Mietzins zahlen oder Erhöhung anfechten", "fr": "Payer le nouveau loyer ou contester", "it": "Pagare la nuova pigione o contestare"},
    "consequence": {"de": "Neuer Mietzins wird verbindlich", "fr": "Le nouveau loyer devient dû", "it": "La nuova pigione diventa dovuta"},
    "documents": {"de": [], "fr": [], "it": []},
}

# ----------------------------------------------------------------------------------------- 8
T["ahv_contributions"] = {
    "auth": {"de": "Ausgleichskasse des Kantons {canton}", "fr": "Caisse cantonale de compensation AVS {canton}", "it": "Cassa cantonale di compensazione AVS {canton}"},
    "dept": {"de": "Beiträge Nichterwerbstätige", "fr": "Cotisations personnes sans activité lucrative", "it": "Contributi persone senza attività lucrativa"},
    "title": {"de": "AHV-Beiträge Nichterwerbstätige", "fr": "Cotisations AVS sans activité lucrative", "it": "Contributi AVS senza attività lucrativa"},
    "body": {
        "de": """AHV-Nr.: {ahv}
Abrechnungs-Nr.: {ref}

Akontobeiträge {year_next} für Nichterwerbstätige

{salutation}

Als nichterwerbstätige Person sind Sie verpflichtet, Beiträge an die AHV/IV/EO zu bezahlen. Gestützt auf Ihre Angaben zu Vermögen und Renteneinkommen betragen Ihre Akontobeiträge für {year_next} insgesamt {annual} (inkl. Verwaltungskosten).

Die Beiträge sind vierteljährlich zu bezahlen. Die erste Rate von {quarter} ist am {due} fällig. Bitte zahlen Sie auf folgendes Konto: IBAN {iban}, Zahlungsreferenz {qr_ref}.

Wenn Sie nicht rechtzeitig bezahlen, werden Verzugszinsen von 5 % pro Jahr erhoben, und es kann eine Betreibung eingeleitet werden. Fehlende Beitragsjahre können später zu einer Kürzung Ihrer Rente führen.

Haben sich Ihre Verhältnisse geändert, melden Sie dies bitte innert {notify_days} Tagen.

Auskunft: Telefon {auth_phone}

Freundliche Grüsse
Ausgleichskasse des Kantons {canton}""",
        "fr": """N° AVS : {ahv}
N° de décompte : {ref}

Acomptes de cotisations {year_next} pour personnes sans activité lucrative

{salutation}

En tant que personne sans activité lucrative, vous êtes tenu(e) de verser des cotisations AVS/AI/APG. Sur la base de vos indications concernant votre fortune et vos rentes, vos acomptes de cotisations pour {year_next} s'élèvent au total à {annual} (frais d'administration compris).

Les cotisations sont payables trimestriellement. La première tranche de {quarter} est échue le {due}. Veuillez effectuer le paiement sur le compte suivant : IBAN {iban}, référence de paiement {qr_ref}.

En cas de retard, des intérêts moratoires de 5 % par an sont perçus et une poursuite peut être engagée. Des années de cotisations manquantes peuvent entraîner plus tard une réduction de votre rente.

Si votre situation a changé, veuillez nous l'annoncer dans les {notify_days} jours.

Renseignements : tél. {auth_phone}

Avec nos meilleures salutations
Caisse cantonale de compensation AVS {canton}""",
        "it": """N. AVS: {ahv}
N. conteggio: {ref}

Acconti di contributi {year_next} per persone senza attività lucrativa

{salutation}

In quanto persona senza attività lucrativa, Lei è tenuto/a a versare contributi AVS/AI/IPG. In base alle Sue indicazioni su sostanza e rendite, gli acconti di contributi per il {year_next} ammontano complessivamente a {annual} (spese amministrative incluse).

I contributi sono pagabili trimestralmente. La prima rata di {quarter} scade il {due}. La preghiamo di effettuare il pagamento sul conto seguente: IBAN {iban}, riferimento di pagamento {qr_ref}.

In caso di ritardo vengono riscossi interessi di mora del 5 % annuo e può essere avviata un'esecuzione. Anni di contribuzione mancanti possono comportare in futuro una riduzione della rendita.

Se la Sua situazione è cambiata, ce lo comunichi entro {notify_days} giorni.

Informazioni: tel. {auth_phone}

Distinti saluti
Cassa cantonale di compensazione AVS {canton}""",
    },
    "action": {"de": "Erste Beitragsrate bezahlen", "fr": "Payer la première tranche de cotisations", "it": "Pagare la prima rata dei contributi"},
    "consequence": {"de": "Verzugszinsen, Betreibung, spätere Rentenkürzung", "fr": "Intérêts moratoires, poursuite, réduction de rente", "it": "Interessi di mora, esecuzione, riduzione della rendita"},
    "documents": {"de": [], "fr": [], "it": []},
}

# ----------------------------------------------------------------------------------------- 9
T["family_allowance"] = {
    "auth": {"de": "Familienausgleichskasse Kanton {canton}", "fr": "Caisse d'allocations familiales {canton}", "it": "Cassa per gli assegni familiari {canton}"},
    "dept": {"de": "Familienzulagen", "fr": "Allocations familiales", "it": "Assegni familiari"},
    "title": {"de": "Familienzulagen: fehlende Unterlagen", "fr": "Allocations familiales : documents manquants", "it": "Assegni familiari: documenti mancanti"},
    "body": {
        "de": """Dossier-Nr.: {ref}

Familienzulagen für {child_name}: fehlende Unterlagen

{salutation}

Ihr Kind {child_name} (geboren am {child_birth}) wird am {age16_date} 16 Jahre alt. Ab diesem Zeitpunkt haben Sie nur noch Anspruch auf eine Ausbildungszulage von {allowance} pro Monat, wenn Ihr Kind eine Schule oder eine Lehre besucht.

Bitte senden Sie uns bis {deadline} eine aktuelle Ausbildungsbestätigung (Schulbestätigung oder Lehrvertrag).

Erhalten wir die Bestätigung nicht rechtzeitig, stellen wir die Zahlung der Familienzulagen per {stop_date} ein. Zu Unrecht bezogene Zulagen müssen zurückbezahlt werden.

Sie erreichen uns unter {auth_phone} oder {auth_email}.

Freundliche Grüsse
Familienausgleichskasse Kanton {canton}""",
        "fr": """Dossier n° : {ref}

Allocations familiales pour {child_name} : documents manquants

{salutation}

Votre enfant {child_name} (né(e) le {child_birth}) aura 16 ans le {age16_date}. Dès cette date, vous n'avez droit à une allocation de formation de {allowance} par mois que si votre enfant suit une école ou un apprentissage.

Veuillez nous envoyer d'ici au {deadline} une attestation de formation récente (attestation scolaire ou contrat d'apprentissage).

Si nous ne recevons pas l'attestation à temps, le versement des allocations familiales sera suspendu dès le {stop_date}. Les allocations perçues à tort doivent être remboursées.

Vous pouvez nous joindre au {auth_phone} ou à l'adresse {auth_email}.

Avec nos meilleures salutations
Caisse d'allocations familiales {canton}""",
        "it": """Incarto n.: {ref}

Assegni familiari per {child_name}: documenti mancanti

{salutation}

Suo figlio/Sua figlia {child_name} (nato/a il {child_birth}) compirà 16 anni il {age16_date}. Da quel momento ha diritto a un assegno di formazione di {allowance} al mese solo se il figlio frequenta una scuola o un apprendistato.

La preghiamo di inviarci entro il {deadline} un attestato di formazione recente (attestato scolastico o contratto di tirocinio).

Se non riceviamo l'attestato in tempo, il pagamento degli assegni familiari sarà sospeso dal {stop_date}. Gli assegni percepiti indebitamente devono essere restituiti.

Può contattarci al numero {auth_phone} o all'indirizzo {auth_email}.

Distinti saluti
Cassa per gli assegni familiari {canton}""",
    },
    "action": {"de": "Ausbildungsbestätigung einsenden", "fr": "Envoyer une attestation de formation", "it": "Inviare un attestato di formazione"},
    "consequence": {"de": "Zahlung der Familienzulagen wird eingestellt", "fr": "Le versement des allocations est suspendu", "it": "Il pagamento degli assegni è sospeso"},
    "documents": {"de": ["Ausbildungsbestätigung"], "fr": ["attestation de formation"], "it": ["attestato di formazione"]},
}

# ---------------------------------------------------------------------------------------- 10
T["health_insurance_reminder"] = {
    "auth": {"de": "{insurer}", "fr": "{insurer}", "it": "{insurer}"},
    "dept": {"de": "Inkasso", "fr": "Encaissement", "it": "Incasso"},
    "title": {"de": "Krankenkasse: 2. Mahnung", "fr": "Caisse-maladie : 2e rappel", "it": "Cassa malati: 2° richiamo"},
    "body": {
        "de": """Versicherten-Nr.: {ref}
Rechnungs-Nr.: {invoice}

2. Mahnung

{salutation}

Trotz unserer Zahlungserinnerung haben wir die Prämien für die Monate August und September {year} noch nicht erhalten.

Offener Betrag: {amount_open}
Mahngebühr: {fee}
Total: {total}

Bitte überweisen Sie das Total bis {deadline} auf IBAN {iban}.

Wenn wir die Zahlung nicht fristgerecht erhalten, leiten wir die Betreibung ein. Die Kosten der Betreibung gehen zu Ihren Lasten. Können Sie den Betrag nicht auf einmal bezahlen, kontaktieren Sie uns für eine Ratenzahlung.

Kundendienst: {auth_phone}, {auth_email}

Freundliche Grüsse
{insurer}""",
        "fr": """N° d'assuré : {ref}
Facture n° : {invoice}

2e rappel

{salutation}

Malgré notre rappel, nous n'avons pas encore reçu les primes des mois d'août et de septembre {year}.

Montant dû : {amount_open}
Frais de rappel : {fee}
Total : {total}

Veuillez verser le total d'ici au {deadline} sur l'IBAN {iban}.

Si nous ne recevons pas le paiement dans le délai, nous engagerons une poursuite. Les frais de poursuite sont à votre charge. Si vous ne pouvez pas payer le montant en une fois, contactez-nous pour un plan de paiement.

Service clientèle : {auth_phone}, {auth_email}

Meilleures salutations
{insurer}""",
        "it": """N. assicurato: {ref}
Fattura n.: {invoice}

2° richiamo

{salutation}

Nonostante il nostro sollecito, non abbiamo ancora ricevuto i premi dei mesi di agosto e settembre {year}.

Importo scoperto: {amount_open}
Spese di richiamo: {fee}
Totale: {total}

La preghiamo di versare il totale entro il {deadline} sull'IBAN {iban}.

Se non riceviamo il pagamento entro il termine, avvieremo un'esecuzione. Le spese esecutive sono a Suo carico. Se non può pagare l'importo in una volta, ci contatti per un pagamento rateale.

Servizio clienti: {auth_phone}, {auth_email}

Cordiali saluti
{insurer}""",
    },
    "action": {"de": "Offenen Betrag mit Mahngebühr bezahlen", "fr": "Payer le montant dû avec les frais", "it": "Pagare l'importo scoperto con le spese"},
    "consequence": {"de": "Betreibung mit Kosten", "fr": "Poursuite avec frais", "it": "Esecuzione con spese"},
    "documents": {"de": [], "fr": [], "it": []},
}

# ---------------------------------------------------------------------------------------- 11
T["asylum_interview"] = {
    "auth": {"de": "Bundesasylzentrum {region}", "fr": "Centre fédéral pour requérants d'asile {region}", "it": "Centro federale d'asilo {region}"},
    "dept": {"de": "Asylverfahren", "fr": "Procédure d'asile", "it": "Procedura d'asilo"},
    "title": {"de": "Vorladung Anhörung Asylgründe", "fr": "Convocation audition motifs d'asile", "it": "Convocazione audizione motivi d'asilo"},
    "body": {
        "de": """N-Nummer: {ref}

Vorladung zur Anhörung zu den Asylgründen

{salutation}

Sie werden zur Anhörung zu Ihren Asylgründen vorgeladen:

Datum: {appt_date}
Zeit: {appt_time}
Ort: Bundesasylzentrum {region}, {appt_street}, {appt_postal}

Bitte melden Sie sich 15 Minuten vor Beginn an der Loge. Eine Dolmetscherin oder ein Dolmetscher wird anwesend sein. Ihre Rechtsvertretung wird ebenfalls eingeladen.

Bitte bringen Sie mit:
- alle Identitätsdokumente (Pass, Identitätskarte, Geburtsurkunde)
- Beweismittel zu Ihren Asylgründen
- diese Vorladung

Wenn Sie ohne entschuldbaren Grund nicht erscheinen, kann Ihr Asylgesuch formlos abgeschrieben werden. Bei Krankheit informieren Sie uns sofort unter Telefon {auth_phone} und reichen Sie ein Arztzeugnis ein.

Freundliche Grüsse
Bundesasylzentrum {region}""",
        "fr": """Dossier n° : {ref}

Convocation à l'audition sur les motifs d'asile

{salutation}

Vous êtes convoqué(e) à l'audition sur vos motifs d'asile :

Date : {appt_date}
Heure : {appt_time}
Lieu : Centre fédéral pour requérants d'asile {region}, {appt_street}, {appt_postal}

Veuillez vous présenter à la loge 15 minutes avant le début. Un ou une interprète sera présent(e). Votre représentation juridique est également convoquée.

Veuillez apporter :
- tous vos documents d'identité (passeport, carte d'identité, acte de naissance)
- les moyens de preuve concernant vos motifs d'asile
- la présente convocation

Si vous ne vous présentez pas sans excuse valable, votre demande d'asile peut être radiée. En cas de maladie, informez-nous immédiatement au {auth_phone} et remettez un certificat médical.

Meilleures salutations
Centre fédéral pour requérants d'asile {region}""",
        "it": """Incarto n.: {ref}

Convocazione all'audizione sui motivi d'asilo

{salutation}

Lei è convocato/a all'audizione sui Suoi motivi d'asilo:

Data: {appt_date}
Ora: {appt_time}
Luogo: Centro federale d'asilo {region}, {appt_street}, {appt_postal}

La preghiamo di presentarsi alla portineria 15 minuti prima dell'inizio. Sarà presente un/una interprete. Anche la Sua rappresentanza legale è convocata.

Porti con sé:
- tutti i documenti d'identità (passaporto, carta d'identità, atto di nascita)
- i mezzi di prova sui Suoi motivi d'asilo
- la presente convocazione

Se non si presenta senza un motivo valido, la Sua domanda d'asilo può essere stralciata. In caso di malattia ci informi subito al numero {auth_phone} e presenti un certificato medico.

Cordiali saluti
Centro federale d'asilo {region}""",
    },
    "action": {"de": "Zur Anhörung erscheinen mit Dokumenten", "fr": "Se présenter à l'audition avec les documents", "it": "Presentarsi all'audizione con i documenti"},
    "consequence": {"de": "Asylgesuch kann abgeschrieben werden", "fr": "La demande d'asile peut être radiée", "it": "La domanda d'asilo può essere stralciata"},
    "documents": {"de": ["Identitätsdokumente", "Beweismittel", "Vorladung"], "fr": ["documents d'identité", "moyens de preuve", "convocation"], "it": ["documenti d'identità", "mezzi di prova", "convocazione"]},
}

# ---------------------------------------------------------------------------------------- 12
T["fine_notice"] = {
    "auth": {"de": "Stadtpolizei {commune}", "fr": "Police municipale de {commune}", "it": "Polizia comunale di {commune}"},
    "dept": {"de": "Ordnungsbussen", "fr": "Amendes d'ordre", "it": "Multe disciplinari"},
    "title": {"de": "Ordnungsbusse", "fr": "Amende d'ordre", "it": "Multa disciplinare"},
    "body": {
        "de": """Busse Nr.: {ref}

Ordnungsbusse

{salutation}

Am {offence_date} um {offence_time} wurde mit dem Fahrzeug {plate} in {commune}, {offence_street}, folgende Übertretung festgestellt: Parkieren ohne gültiges Parkticket.

Busse: {amount}

Bitte bezahlen Sie die Busse innert {pay_days} Tagen mit dem beiliegenden QR-Einzahlungsschein (IBAN {iban}, Referenz {qr_ref}). Mit der fristgerechten Zahlung ist die Angelegenheit erledigt.

Wird die Busse nicht innert Frist bezahlt, wird ein ordentliches Strafverfahren eingeleitet. Dabei entstehen zusätzliche Kosten.

Auskunft: Telefon {auth_phone}, Montag bis Freitag

Stadtpolizei {commune}""",
        "fr": """Amende n° : {ref}

Amende d'ordre

{salutation}

Le {offence_date} à {offence_time}, l'infraction suivante a été constatée avec le véhicule {plate} à {commune}, {offence_street} : stationnement sans ticket valable.

Amende : {amount}

Veuillez payer l'amende dans les {pay_days} jours au moyen de la QR-facture ci-jointe (IBAN {iban}, référence {qr_ref}). Le paiement dans le délai règle l'affaire.

Si l'amende n'est pas payée dans le délai, une procédure pénale ordinaire sera ouverte, ce qui entraînera des frais supplémentaires.

Renseignements : tél. {auth_phone}, du lundi au vendredi

Police municipale de {commune}""",
        "it": """Multa n.: {ref}

Multa disciplinare

{salutation}

Il {offence_date} alle {offence_time} è stata constatata con il veicolo {plate} a {commune}, {offence_street}, la seguente infrazione: parcheggio senza biglietto valido.

Multa: {amount}

La preghiamo di pagare la multa entro {pay_days} giorni con la polizza QR allegata (IBAN {iban}, riferimento {qr_ref}). Con il pagamento entro il termine la questione è chiusa.

Se la multa non viene pagata entro il termine, sarà avviato un procedimento penale ordinario, con costi supplementari.

Informazioni: tel. {auth_phone}, dal lunedì al venerdì

Polizia comunale di {commune}""",
    },
    "action": {"de": "Busse innert Frist bezahlen", "fr": "Payer l'amende dans le délai", "it": "Pagare la multa entro il termine"},
    "consequence": {"de": "Ordentliches Strafverfahren mit Zusatzkosten", "fr": "Procédure pénale ordinaire avec frais", "it": "Procedimento penale ordinario con costi"},
    "documents": {"de": [], "fr": [], "it": []},
}

LETTER_TYPES = list(T)
