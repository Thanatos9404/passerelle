/**
 * MOCK CORPUS — hand-written plain-language explanations (masked, with ⟦X⟧ placeholders)
 * and simulated back-translations. They exist only to exercise the UI without a model.
 * The real system generates these with Apertus via the backend.
 */

export interface MockExplanation {
  masked: string;
  /** substitutions applied to the letter's reference text to simulate the round-trip back-translation */
  drift: [string, string][];
}

type ByLang = Record<string, MockExplanation>;

export const MOCK_EXPLANATIONS: Record<string, ByLang> = {
  "de-betreibung-zahlungsbefehl": {
    en: {
      masked:
        "This letter is from the debt collection office (Betreibungsamt) in Aarenfeld. It is a payment order: a health insurance company says you owe ⟦A1⟧ for unpaid premiums, plus ⟦A2⟧ in fees.\n\nWhat you must do: if you agree that you owe the money, pay by ⟦D6⟧ to the account ⟦I1⟧ with the reference ⟦R1⟧.\n\nIf you do not agree, you must tell the office by ⟦D4⟧. This is called an objection (Rechtsvorschlag). You can say it in person or in writing, and you do not need to give a reason.\n\nIf you do nothing: the insurance company can continue the debt collection, and part of your income or belongings can be seized.\n\nWho can help: the office at ⟦L1⟧, phone ⟦P1⟧, Monday to Friday ⟦T1⟧. A social counselling service can also help you.",
      drift: [
        ["Es ist ein Zahlungsbefehl", "Es ist eine Zahlungsaufforderung"],
        ["Auch eine Sozialberatung kann Ihnen helfen.", "Auch eine soziale Beratungsstelle kann Ihnen helfen."],
      ],
    },
    ti: {
      masked:
        "እዚ ደብዳቤ ካብ ቤት ጽሕፈት ምእካብ ዕዳ (Betreibungsamt) ኣረንፈልድ እዩ። እዚ ትእዛዝ ክፍሊት እዩ፦ ሓደ ትካል ኢንሹራንስ ጥዕና ንዘይተኸፍለ ክፍሊት ⟦A1⟧ ከም እትግብኦ ይብል፣ ምስ ⟦A2⟧ ወጻኢታት።\n\nእንታይ ክትገብር ኣለካ፦ እቲ ገንዘብ ከም እትግብኦ እንተ ተሰማሚዕካ፣ ክሳብ ⟦D6⟧ ናብ ሕሳብ ⟦I1⟧ ብመወከሲ ⟦R1⟧ ክፈል።\n\nእንተ ዘይተሰማማዕካ ግን፣ ክሳብ ⟦D4⟧ ናብቲ ቤት ጽሕፈት ተቓውሞ (Rechtsvorschlag) ከተቕርብ ኣለካ። ብኣካል ወይ ብጽሑፍ ክትገብሮ ትኽእል ኢኻ፤ ምኽንያት ምሃብ ኣየድልን።\n\nዋላ ሓንቲ እንተ ዘይገበርካ፦ እቲ ትካል ነቲ ምእካብ ዕዳ ክቕጽሎ ይኽእል፣ ኣታዊኻ ወይ ንብረትካ ክተሓዝ ይኽእል።\n\nመን ክሕግዘካ ይኽእል፦ እቲ ቤት ጽሕፈት ኣብ ⟦L1⟧፣ ቴሌፎን ⟦P1⟧፣ ሰኑይ ክሳብ ዓርቢ ⟦T1⟧። ሰራሕተኛ ማሕበራዊ ጉዳይ እውን ክሕግዘካ ይኽእል።",
      drift: [
        ["Dieser Brief kommt vom Betreibungsamt Aarenfeld.", "Dieser Brief ist vom Büro für das Einsammeln von Schulden in Aarenfeld."],
        ["Es ist ein Zahlungsbefehl:", "Es ist ein Befehl zum Bezahlen:"],
        ["für nicht bezahlte Prämien schulden, plus ⟦A2⟧ Kosten", "für Zahlungen schulden, die nicht bezahlt wurden, mit ⟦A2⟧ Ausgaben"],
        ["Wenn Sie einverstanden sind,", "Wenn Sie meinen, dass Sie es schulden,"],
        ["müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben", "müssen Sie bis ⟦D4⟧ beim Büro einen Widerspruch (Rechtsvorschlag) bringen"],
        ["Das geht mündlich oder schriftlich, Sie müssen keinen Grund angeben.", "Sie können es selbst oder schriftlich machen; ein Grund ist nicht nötig."],
        ["und ein Teil Ihres Lohns oder Ihrer Sachen kann gepfändet werden", "und Ihr Einkommen oder Ihr Besitz kann genommen werden"],
        ["Auch eine Sozialberatung kann Ihnen helfen.", "Ein Sozialarbeiter kann Ihnen auch helfen."],
        ["Wer hilft:", "Wer Ihnen helfen kann:"],
      ],
    },
    ar: {
      masked:
        "هذه الرسالة من مكتب تحصيل الديون (Betreibungsamt) في آرنفيلد. إنها أمر دفع: شركة تأمين صحي تقول إنك مدين بمبلغ ⟦A1⟧ لأقساط غير مدفوعة، بالإضافة إلى رسوم قدرها ⟦A2⟧.\n\nما يجب عليك فعله: إذا كنت توافق على أنك مدين بالمبلغ، ادفع في موعد أقصاه ⟦D6⟧ إلى الحساب ⟦I1⟧ مع الرقم المرجعي ⟦R1⟧.\n\nإذا كنت لا توافق، يجب أن تقدّم اعتراضًا (Rechtsvorschlag) لدى المكتب في موعد أقصاه ⟦D4⟧. يمكنك الاعتراض شفهيًا أو كتابيًا، ولا تحتاج إلى ذكر سبب.\n\nإذا لم تفعل شيئًا: يمكن لشركة التأمين متابعة إجراءات التحصيل، وقد يتم حجز جزء من دخلك أو ممتلكاتك.\n\nمن يمكنه مساعدتك: المكتب في ⟦L1⟧، هاتف ⟦P1⟧، من الاثنين إلى الجمعة ⟦T1⟧. يمكن أيضًا لخدمة الإرشاد الاجتماعي أن تساعدك.",
      drift: [
        ["Eine Krankenkasse sagt", "Eine Krankenversicherung sagt"],
        ["müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben", "müssen Sie bis ⟦D4⟧ beim Amt einen Einspruch (Rechtsvorschlag) einreichen"],
        ["Auch eine Sozialberatung kann Ihnen helfen.", "Auch die soziale Beratung kann Ihnen helfen."],
      ],
    },
    prs: {
      masked:
        "این نامه از دفتر تحصیل قرض (Betreibungsamt) آرنفلد است. این یک حکم پرداخت است: یک شرکت بیمهٔ صحی می‌گوید شما مبلغ ⟦A1⟧ بابت حق بیمهٔ پرداخت‌نشده بدهکار هستید، به‌علاوهٔ ⟦A2⟧ مصارف.\n\nچه باید بکنید: اگر قبول دارید که این پول را بدهکار هستید، تا ⟦D6⟧ به حساب ⟦I1⟧ با شمارهٔ مرجع ⟦R1⟧ پرداخت کنید.\n\nاگر قبول ندارید، باید تا ⟦D4⟧ در دفتر اعتراض (Rechtsvorschlag) ثبت کنید. می‌توانید حضوری یا کتبی اعتراض کنید و لازم نیست دلیل بگویید.\n\nاگر هیچ کاری نکنید: شرکت بیمه می‌تواند تحصیل قرض را ادامه دهد و ممکن است بخشی از معاش یا دارایی شما ضبط شود.\n\nچه کسی می‌تواند کمک کند: دفتر در ⟦L1⟧، تلفون ⟦P1⟧، دوشنبه تا جمعه ⟦T1⟧. یک مددکار اجتماعی هم می‌تواند به شما کمک کند.",
      drift: [
        ["Es ist ein Zahlungsbefehl:", "Es ist eine Anordnung zur Zahlung:"],
        ["müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben", "müssen Sie bis ⟦D4⟧ im Büro Einspruch (Rechtsvorschlag) eintragen"],
        ["Das geht mündlich oder schriftlich, Sie müssen keinen Grund angeben.", "Sie können persönlich oder schriftlich widersprechen und müssen keinen Grund sagen."],
        ["Auch eine Sozialberatung kann Ihnen helfen.", "Auch ein Sozialarbeiter kann Ihnen helfen."],
      ],
    },
    ta: {
      // Deliberately omits ⟦T1⟧ (opening hours) to exercise the placeholder audit.
      masked:
        "இந்தக் கடிதம் ஆரன்ஃபெல்ட் கடன் வசூல் அலுவலகத்திலிருந்து (Betreibungsamt) வந்துள்ளது. இது ஒரு பணம் செலுத்தும் உத்தரவு: செலுத்தப்படாத மருத்துவக் காப்பீட்டுக் கட்டணங்களுக்காக நீங்கள் ⟦A1⟧ செலுத்த வேண்டும் என்று ஒரு காப்பீட்டு நிறுவனம் கூறுகிறது; மேலும் ⟦A2⟧ செலவுக் கட்டணமும் உள்ளது.\n\nநீங்கள் செய்ய வேண்டியது: இந்தப் பணத்தை நீங்கள் செலுத்த வேண்டும் என்று ஒப்புக்கொண்டால், ⟦D6⟧ க்குள் ⟦I1⟧ கணக்கிற்கு ⟦R1⟧ என்ற குறிப்பு எண்ணுடன் செலுத்துங்கள்.\n\nநீங்கள் ஒப்புக்கொள்ளவில்லை என்றால், ⟦D4⟧ க்குள் அலுவலகத்தில் ஆட்சேபனை (Rechtsvorschlag) தெரிவிக்க வேண்டும். நேரிலோ எழுத்து மூலமோ தெரிவிக்கலாம்; காரணம் சொல்லத் தேவையில்லை.\n\nநீங்கள் எதுவும் செய்யாவிட்டால்: நிறுவனம் கடன் வசூலைத் தொடரலாம்; உங்கள் வருமானம் அல்லது உடைமைகள் பறிமுதல் செய்யப்படலாம்.\n\nயார் உதவ முடியும்: ⟦L1⟧ இல் உள்ள அலுவலகம், தொலைபேசி ⟦P1⟧, திங்கள் முதல் வெள்ளி வரை. ஒரு சமூகப் பணியாளரும் உங்களுக்கு உதவலாம்.",
      drift: [
        ["Eine Krankenkasse sagt", "Eine Versicherungsfirma sagt"],
        ["plus ⟦A2⟧ Kosten", "dazu kommen ⟦A2⟧ Gebühren"],
        ["müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben", "müssen Sie bis ⟦D4⟧ im Büro einen Einwand (Rechtsvorschlag) mitteilen"],
        ["Montag bis Freitag ⟦T1⟧.", "Montag bis Freitag."],
        ["Auch eine Sozialberatung kann Ihnen helfen.", "Auch ein Sozialarbeiter kann Ihnen helfen."],
      ],
    },
    uk: {
      masked:
        "Цей лист — від служби стягнення боргів (Betreibungsamt) в Ааренфельді. Це платіжна вимога: компанія медичного страхування стверджує, що ви винні ⟦A1⟧ за несплачені внески, а також ⟦A2⟧ витрат.\n\nЩо потрібно зробити: якщо ви погоджуєтеся з боргом, сплатіть до ⟦D6⟧ на рахунок ⟦I1⟧ з номером ⟦R1⟧.\n\nЯкщо ви не погоджуєтеся, ви повинні подати заперечення (Rechtsvorschlag) до служби до ⟦D4⟧. Це можна зробити усно або письмово, причину вказувати не потрібно.\n\nЩо буде, якщо нічого не робити: страхова компанія може продовжити стягнення, і частину вашого доходу або майна можуть арештувати.\n\nХто може допомогти: служба за адресою ⟦L1⟧, телефон ⟦P1⟧, з понеділка по п'ятницю ⟦T1⟧. Також може допомогти служба соціальних консультацій.",
      drift: [
        ["Es ist ein Zahlungsbefehl:", "Es ist eine Zahlungsforderung:"],
        ["müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben", "müssen Sie bis ⟦D4⟧ beim Amt Widerspruch (Rechtsvorschlag) einlegen"],
      ],
    },
    tr: {
      masked:
        "Bu mektup Aarenfeld İcra Dairesi'nden (Betreibungsamt) geliyor. Bu bir ödeme emridir: Bir sağlık sigortası şirketi, ödenmemiş primler için ⟦A1⟧ borcunuz olduğunu söylüyor; buna ek olarak ⟦A2⟧ masraf var.\n\nNe yapmalısınız: Borcu kabul ediyorsanız, ⟦D6⟧ tarihine kadar ⟦R1⟧ referansıyla ⟦I1⟧ hesabına ödeyin.\n\nKabul etmiyorsanız, ⟦D4⟧ tarihine kadar daireye itiraz (Rechtsvorschlag) bildirmelisiniz. İtirazı sözlü veya yazılı yapabilirsiniz; gerekçe göstermeniz gerekmez.\n\nHiçbir şey yapmazsanız: Sigorta şirketi icra takibine devam edebilir; gelirinize veya eşyalarınıza haciz konulabilir.\n\nKim yardım edebilir: ⟦L1⟧ adresindeki daire, telefon ⟦P1⟧, pazartesiden cumaya ⟦T1⟧. Bir sosyal danışmanlık servisi de size yardım edebilir.",
      drift: [
        ["Dieser Brief kommt vom Betreibungsamt Aarenfeld.", "Dieser Brief kommt vom Betreibungsamt in Aarenfeld."],
        ["müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben", "müssen Sie bis ⟦D4⟧ dem Amt einen Widerspruch (Rechtsvorschlag) melden"],
        ["und ein Teil Ihres Lohns oder Ihrer Sachen kann gepfändet werden", "und auf Ihr Einkommen oder Ihre Sachen kann eine Pfändung gelegt werden"],
      ],
    },
  },

  "fr-permis-renouvellement": {
    en: {
      masked:
        "This letter is from the municipality of Montreval. Your residence permit ends on ⟦D2⟧.\n\nTo renew it, you must come to the counter in person on ⟦D3⟧ at ⟦T1⟧. Bring your passport, your current permit, a photo, and a certificate from your employer or the social service. You pay ⟦A1⟧ at the counter.\n\nIf you cannot come, call ⟦P1⟧ before ⟦D4⟧ and give the reference ⟦R1⟧. If you do not answer, the renewal can take longer.\n\nCounter address: ⟦L1⟧.",
      drift: [["Vous payez ⟦A1⟧ au guichet.", "Vous payez ⟦A1⟧ sur place."]],
    },
    prs: {
      masked:
        "این نامه از شاروالی مونتروال است. اجازهٔ اقامت شما در ⟦D2⟧ ختم می‌شود.\n\nبرای تمدید آن، باید در ⟦D3⟧ ساعت ⟦T1⟧ خودتان به دفتر خدمات (guichet) بیایید. پاسپورت، اجازهٔ اقامت فعلی، یک عکس و یک تصدیق از کارفرما یا خدمات اجتماعی را با خود بیاورید. در دفتر ⟦A1⟧ پرداخت می‌کنید.\n\nاگر نمی‌توانید بیایید، پیش از ⟦D4⟧ به شمارهٔ ⟦P1⟧ زنگ بزنید و شمارهٔ مرجع ⟦R1⟧ را بگویید. اگر جواب ندهید، تمدید ممکن است بیشتر طول بکشد.\n\nآدرس دفتر: ⟦L1⟧.",
      drift: [
        ["Cette lettre vient de la commune de Montreval.", "Cette lettre vient de la mairie de Montreval."],
        ["Votre permis de séjour se termine le ⟦D2⟧.", "Votre autorisation de séjour finit le ⟦D2⟧."],
        ["Si vous ne répondez pas, le renouvellement peut prendre plus de temps.", "Si vous ne répondez pas, la prolongation peut durer plus longtemps."],
      ],
    },
    ar: {
      masked:
        "هذه الرسالة من بلدية مونتروفال. تنتهي صلاحية تصريح إقامتك في ⟦D2⟧.\n\nلتجديده، يجب أن تحضر شخصيًا إلى الشباك في ⟦D3⟧ الساعة ⟦T1⟧. أحضر جواز سفرك، وتصريح إقامتك الحالي، وصورة شخصية، وشهادة من صاحب العمل أو من الخدمة الاجتماعية. تدفع ⟦A1⟧ عند الشباك.\n\nإذا لم تستطع الحضور، اتصل بالرقم ⟦P1⟧ قبل ⟦D4⟧، واذكر الرقم المرجعي ⟦R1⟧. إذا لم تردّ، قد يتأخر التجديد.\n\nعنوان الشباك: ⟦L1⟧.",
      drift: [["Si vous ne répondez pas, le renouvellement peut prendre plus de temps.", "Si vous ne répondez pas, le renouvellement peut être retardé."]],
    },
    ti: {
      masked:
        "እዚ ደብዳቤ ካብ ምምሕዳር ከተማ ሞንትረቫል እዩ። ፍቓድ መንበሪኺ ብ⟦D2⟧ ይውዳእ።\n\nንምሕዳሱ፣ ብ⟦D3⟧ ሰዓት ⟦T1⟧ ብኣካል ናብቲ ቤት ጽሕፈት ክትመጺ ኣለኪ። ፓስፖርትኪ፣ ናይ ሕጂ ፍቓድ መንበሪኺ፣ ስእሊ፣ ከምኡ'ውን ካብ ኣስራሒኺ ወይ ካብ ማሕበራዊ ኣገልግሎት ምስክር ወረቐት ኣምጽኢ። ⟦A1⟧ ኣብቲ ቤት ጽሕፈት ትኸፍሊ።\n\nክትመጺ እንተ ዘይክኢልኪ፣ ቅድሚ ⟦D4⟧ ናብ ⟦P1⟧ ደውሊ፣ ቁጽሪ መወከሲ ⟦R1⟧ ሃቢ። መልሲ እንተ ዘይሂብኪ፣ እቲ ምሕዳስ ክደናጎ ይኽእል።\n\nኣድራሻ፦ ⟦L1⟧።",
      drift: [
        ["Cette lettre vient de la commune de Montreval.", "Cette lettre est de l'administration de la ville de Montreval."],
        ["Pour le renouveler, vous devez venir au guichet", "Pour le rendre nouveau, vous devez venir au bureau en personne"],
        ["et une attestation de votre employeur ou du service social", "et un papier de témoignage de votre patron ou du service social"],
        ["Si vous ne répondez pas, le renouvellement peut prendre plus de temps.", "Si vous ne donnez pas de réponse, le renouvellement peut être en retard."],
        ["Adresse du guichet :", "Adresse :"],
      ],
    },
    uk: {
      masked:
        "Цей лист — від громади Монтреваль. Ваш дозвіл на проживання закінчується ⟦D2⟧.\n\nЩоб його продовжити, ви повинні особисто прийти до віконця ⟦D3⟧ о ⟦T1⟧. Візьміть паспорт, чинний дозвіл, фото та довідку від роботодавця або соціальної служби. На місці ви платите ⟦A1⟧.\n\nЯкщо не можете прийти, зателефонуйте за номером ⟦P1⟧ до ⟦D4⟧ і назвіть номер ⟦R1⟧. Якщо ви не відповісте, продовження може затягнутися.\n\nАдреса: ⟦L1⟧.",
      drift: [
        ["Vous payez ⟦A1⟧ au guichet.", "Sur place, vous payez ⟦A1⟧."],
        ["Adresse du guichet :", "Adresse :"],
      ],
    },
  },

  "it-sociale-convocazione": {
    en: {
      masked:
        "This letter is from the social service of the municipality of Valdora. Every year they check your right to social assistance.\n\nYou must come to an interview on ⟦D2⟧ at ⟦T1⟧, at ⟦L1⟧. Bring your bank statements for the last 3 months, your rent contract with the October receipt, and your health insurance policy for 2027. Today you receive ⟦A1⟧ per month.\n\nIf you cannot come, call ⟦P1⟧ by ⟦D3⟧ and give the reference ⟦R1⟧. If you do not come without a good reason, your assistance can be suspended.",
      drift: [["Oggi riceve ⟦A1⟧ al mese.", "Adesso riceve ⟦A1⟧ ogni mese."]],
    },
    ta: {
      masked:
        "இந்தக் கடிதம் வால்டோரா நகராட்சியின் சமூக சேவைப் பிரிவிலிருந்து வந்துள்ளது. ஒவ்வொரு ஆண்டும் உங்களுக்கு சமூக உதவி பெறும் உரிமையை அவர்கள் சரிபார்க்கிறார்கள்.\n\nநீங்கள் ⟦D2⟧ அன்று ⟦T1⟧ மணிக்கு ⟦L1⟧ இல் ஒரு நேர்காணலுக்கு வர வேண்டும். கடந்த 3 மாதங்களின் வங்கி அறிக்கைகள், அக்டோபர் வாடகை ரசீதுடன் வாடகை ஒப்பந்தம், 2027 மருத்துவக் காப்பீட்டுப் பாலிசி ஆகியவற்றைக் கொண்டு வாருங்கள். தற்போது நீங்கள் மாதம் ⟦A1⟧ பெறுகிறீர்கள்.\n\nநீங்கள் வர முடியாவிட்டால், ⟦D3⟧ க்குள் ⟦P1⟧ என்ற எண்ணுக்கு அழைத்து ⟦R1⟧ என்ற குறிப்பு எண்ணைச் சொல்லுங்கள். சரியான காரணமின்றி நீங்கள் வராவிட்டால், உதவி நிறுத்தப்படலாம்.",
      drift: [
        ["Ogni anno controllano il Suo diritto all'aiuto sociale.", "Ogni anno verificano il Suo diritto a ricevere aiuto sociale."],
        ["Porti gli estratti conto della banca degli ultimi 3 mesi", "Porti i rendiconti bancari degli ultimi 3 mesi"],
        ["Se non viene senza un buon motivo, l'aiuto può essere sospeso.", "Se non viene senza un motivo giusto, l'aiuto può essere fermato."],
      ],
    },
    ti: {
      masked:
        "እዚ ደብዳቤ ካብ ማሕበራዊ ኣገልግሎት ምምሕዳር ቫልዶራ እዩ። ኣብ ነፍሲ ወከፍ ዓመት መሰልካ ንማሕበራዊ ሓገዝ ይፍትሹ።\n\nብ⟦D2⟧ ሰዓት ⟦T1⟧ ኣብ ⟦L1⟧ ንቓለ መሕተት ክትመጽእ ኣለካ። ናይ ዝሓለፉ 3 ኣዋርሕ መግለጺ ባንክ፣ ውዕል ገዛ ምስ ናይ ጥቅምቲ ቅብሊት፣ ከምኡ'ውን ናይ 2027 ፖሊሲ ኢንሹራንስ ጥዕና ኣምጽእ። ሕጂ ኣብ ወርሒ ⟦A1⟧ ትቕበል ኢኻ።\n\nክትመጽእ እንተ ዘይክኢልካ፣ ክሳብ ⟦D3⟧ ናብ ⟦P1⟧ ደውል፣ ቁጽሪ መወከሲ ⟦R1⟧ ሃብ። ብዘይ ቅቡል ምኽንያት እንተ ዘይመጺእካ፣ እቲ ሓገዝ ክቋረጽ ይኽእል።",
      drift: [
        ["Questa lettera viene dal servizio sociale del Comune di Valdora.", "Questa lettera è dal servizio sociale dell'amministrazione di Valdora."],
        ["Ogni anno controllano il Suo diritto all'aiuto sociale.", "In ogni anno guardano il Suo diritto per l'aiuto sociale."],
        ["Lei deve venire a un colloquio", "Lei deve venire per una intervista"],
        ["il contratto d'affitto con la ricevuta di ottobre", "il contratto della casa con la ricevuta di ottobre"],
        ["Se non viene senza un buon motivo, l'aiuto può essere sospeso.", "Se non viene senza una ragione accettabile, l'aiuto può essere interrotto."],
      ],
    },
    ar: {
      masked:
        "هذه الرسالة من الخدمة الاجتماعية في بلدية فالدورا. كل سنة يراجعون حقك في المساعدة الاجتماعية.\n\nيجب أن تحضر إلى مقابلة في ⟦D2⟧ الساعة ⟦T1⟧ في ⟦L1⟧. أحضر كشوف حسابك البنكي لآخر 3 أشهر، وعقد الإيجار مع إيصال إيجار أكتوبر، وبوليصة التأمين الصحي لعام 2027. تحصل حاليًا على ⟦A1⟧ شهريًا.\n\nإذا لم تستطع الحضور، اتصل بالرقم ⟦P1⟧ في موعد أقصاه ⟦D3⟧ واذكر الرقم المرجعي ⟦R1⟧. إذا تغيبت دون سبب مقبول، قد يتم إيقاف المساعدة.",
      drift: [
        ["Oggi riceve ⟦A1⟧ al mese.", "Attualmente riceve ⟦A1⟧ al mese."],
        ["Se non viene senza un buon motivo, l'aiuto può essere sospeso.", "Se è assente senza un motivo accettabile, l'aiuto può essere sospeso."],
      ],
    },
  },

  "de-praemienverbilligung": {
    en: {
      masked:
        "This letter is from the social insurance office of Nordwald. You will get money for your health insurance: about ⟦A1⟧ per month from ⟦D2⟧.\n\nFor this, you must send three copies by ⟦D3⟧: your tax assessment or a confirmation from the social service, your rent contract, and your health insurance policy for 2027. Write the number ⟦R1⟧ on it.\n\nIf the documents arrive late, you get no money for 2027. Questions: phone ⟦P1⟧, Monday to Thursday ⟦T1⟧.",
      drift: [["Schreiben Sie die Nummer ⟦R1⟧ dazu.", "Schreiben Sie die Nummer ⟦R1⟧ darauf."]],
    },
    uk: {
      masked:
        "Цей лист — від управління соціального страхування кантону Нордвальд. Ви отримаєте допомогу на медичне страхування: приблизно ⟦A1⟧ на місяць з ⟦D2⟧.\n\nДля цього до ⟦D3⟧ надішліть три копії: податкове рішення або довідку соціальної служби, договір оренди та поліс медичного страхування на 2027 рік. Вкажіть номер ⟦R1⟧.\n\nЯкщо документи надійдуть пізно, у 2027 році ви не отримаєте допомоги. Питання: телефон ⟦P1⟧, з понеділка по четвер ⟦T1⟧.",
      drift: [
        ["Sie bekommen Geld für die Krankenkasse", "Sie bekommen eine Hilfe für die Krankenversicherung"],
        ["Schreiben Sie die Nummer ⟦R1⟧ dazu.", "Geben Sie die Nummer ⟦R1⟧ an."],
      ],
    },
    ar: {
      masked:
        "هذه الرسالة من مكتب التأمينات الاجتماعية في كانتون نوردفالد. ستحصل على مساعدة لدفع التأمين الصحي: حوالي ⟦A1⟧ شهريًا ابتداءً من ⟦D2⟧.\n\nلذلك يجب أن ترسل ثلاث نسخ في موعد أقصاه ⟦D3⟧: قرار الضرائب أو تأكيد من الخدمة الاجتماعية، وعقد الإيجار، وبوليصة التأمين الصحي لعام 2027. اكتب الرقم ⟦R1⟧ عليها.\n\nإذا وصلت الوثائق متأخرة، لن تحصل على المساعدة في عام 2027. للأسئلة: هاتف ⟦P1⟧، من الاثنين إلى الخميس ⟦T1⟧.",
      drift: [
        ["Sie bekommen Geld für die Krankenkasse", "Sie bekommen Hilfe, um die Krankenversicherung zu bezahlen"],
        ["Wenn die Unterlagen zu spät kommen, bekommen Sie 2027 kein Geld.", "Wenn die Dokumente zu spät ankommen, bekommen Sie 2027 keine Hilfe."],
      ],
    },
  },
};

/** Example client messages (for the Reply tab's "use example" action). */
export const MOCK_CLIENT_MESSAGES: Record<string, Record<string, string>> = {
  "de-betreibung-zahlungsbefehl": {
    en: "I don't agree. I already paid the April premium. I want to object.",
    ti: "ኣይሰማማዕን እየ። ናይ ሚያዝያ ክፍሊት ድሮ ከፊለዮ እየ። ተቓውሞ ከቕርብ እደሊ።",
    ar: "أنا لا أوافق. لقد دفعت قسط شهر أبريل بالفعل. أريد تقديم اعتراض.",
    prs: "من موافق نیستم. حق بیمهٔ ماه اپریل را قبلاً پرداخته‌ام. می‌خواهم اعتراض کنم.",
    ta: "நான் ஒப்புக்கொள்ளவில்லை. ஏப்ரல் மாதக் கட்டணத்தை ஏற்கனவே செலுத்திவிட்டேன். நான் ஆட்சேபனை தெரிவிக்க விரும்புகிறேன்.",
    uk: "Я не згоден. Внесок за квітень я вже сплатив. Я хочу подати заперечення.",
    tr: "Kabul etmiyorum. Nisan primini zaten ödedim. İtiraz etmek istiyorum.",
  },
  "fr-permis-renouvellement": {
    en: "I cannot come on 4 November because I have a language course. Can I have another appointment?",
    prs: "من در ۴ نوامبر نمی‌توانم بیایم، چون کورس زبان دارم. آیا می‌توانم وقت دیگری بگیرم؟",
    ar: "لا أستطيع الحضور في 4 نوفمبر لأن لدي دورة لغة. هل يمكنني الحصول على موعد آخر؟",
    ti: "ብ4 ሕዳር ክመጽእ ኣይክእልን እየ፣ ምኽንያቱ ትምህርቲ ቋንቋ ኣለኒ። ካልእ ቆጸራ ክረክብ ይኽእል ድየ?",
    uk: "Я не можу прийти 4 листопада, бо в мене мовний курс. Чи можна отримати інший запис?",
  },
  "it-sociale-convocazione": {
    en: "I will come on 12 November. My new insurance policy has not arrived yet. Can I bring it later?",
    ta: "நான் நவம்பர் 12 அன்று வருவேன். புதிய காப்பீட்டுப் பாலிசி இன்னும் வரவில்லை. அதைப் பின்னர் கொண்டு வரலாமா?",
    ti: "ብ12 ሕዳር ክመጽእ እየ። ሓድሽ ፖሊሲ ኢንሹራንስ ገና ኣይበጽሐንን። ጸኒሐ ከምጽኦ ይኽእል ድየ?",
    ar: "سآتي في 12 نوفمبر. لم تصلني بوليصة التأمين الجديدة بعد. هل يمكنني إحضارها لاحقًا؟",
  },
  "de-praemienverbilligung": {
    en: "I will send the documents this week. I do not have the 2027 policy yet.",
    uk: "Я надішлю документи цього тижня. Поліса на 2027 рік у мене ще немає.",
    ar: "سأرسل الوثائق هذا الأسبوع. ليست لدي بوليصة 2027 بعد.",
  },
};

/** Formal replies in the authority's language (masked). {TODAY} is replaced at draft time. */
export const MOCK_REPLIES: Record<string, string> = {
  "de-betreibung-zahlungsbefehl": `⟦N1⟧
⟦L2⟧

Betreibungsamt Aarenfeld
⟦L1⟧

Aarenfeld, {TODAY}

Rechtsvorschlag – Betreibung Nr. ⟦R1⟧

Sehr geehrte Frau Gerber

Gegen den Zahlungsbefehl vom ⟦D1⟧ in der Betreibung Nr. ⟦R1⟧ über ⟦A1⟧ erhebe ich hiermit Rechtsvorschlag.

Ich bestreite die Forderung. Nach meinen Unterlagen habe ich die Prämie für April 2026 bereits bezahlt.

Bitte bestätigen Sie mir den Eingang dieses Rechtsvorschlags.

Freundliche Grüsse

⟦N1⟧`,
  "fr-permis-renouvellement": `⟦N1⟧
⟦L2⟧

Commune de Montreval
Contrôle des habitants et Service des étrangers
⟦L1⟧

Montreval, le {TODAY}

Votre référence : ⟦R1⟧
Concerne : demande de report du rendez-vous du ⟦D3⟧

Madame, Monsieur,

Je vous remercie de votre lettre du ⟦D1⟧ concernant le renouvellement de mon autorisation de séjour.

Je ne pourrai malheureusement pas me présenter le ⟦D3⟧ à ⟦T1⟧, car je suis un cours de langue à cette heure-là. Je vous prie de bien vouloir me proposer un autre rendez-vous avant l'échéance de mon permis, le ⟦D2⟧.

Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.

⟦N1⟧`,
  "it-sociale-convocazione": `⟦N1⟧
⟦L2⟧

Comune di Valdora
Servizio sociale comunale
⟦L1⟧

Valdora, {TODAY}

Rif.: ⟦R1⟧
Oggetto: conferma del colloquio del ⟦D2⟧

Gentile signora Bernasconi,

con la presente confermo la mia presenza al colloquio del ⟦D2⟧ alle ore ⟦T1⟧.

Porterò gli estratti conto bancari e il contratto di locazione con la ricevuta dell'affitto. La polizza della cassa malati 2027 non mi è ancora pervenuta: La prego di comunicarmi se posso consegnarla in un secondo momento.

Distinti saluti

⟦N1⟧`,
  "de-praemienverbilligung": `⟦N1⟧
⟦L2⟧

Sozialversicherungsamt des Kantons Nordwald
Prämienverbilligung
⟦L1⟧

Nordwald, {TODAY}

Dossier ⟦R1⟧ – AHV-Nr. ⟦V1⟧
Unterlagen zur Prämienverbilligung 2027

Sehr geehrte Damen und Herren

Besten Dank für Ihr Schreiben vom ⟦D1⟧. Ich sende Ihnen die verlangten Unterlagen diese Woche zu, jedenfalls vor dem ⟦D3⟧.

Die Krankenkassen-Police 2027 habe ich noch nicht erhalten. Ich reiche sie nach, sobald sie eintrifft.

Freundliche Grüsse

⟦N1⟧`,
};
