/* app.js — Zustandsmaschine + Theme-Switcher + Datenanbindung (Vanilla-JS).
   Port von repair-app.jsx + Stufe-1/2/3-Erweiterungen (PROJ-1…27).
   Flow: Start → (pick/Diagnose) → Consent-Gate → Eigentum → Triage → [Unklar?] →
         [Diagnose kuratiert] → [Rückruf-Stopp?] → Ampel → [Mehrfachdefekte?] →
         Entscheidung → [self: Können → Garantie-Gate → [Datenlöschung?] → Reparatur(+Sicherheit) → Rückblick]
         | [andere: Weg]. Persistenz via /api/vorgang. Eine Phone-Instanz, mittig. */
(function () {
  'use strict';

  var h = window.h;
  var Screen = window.Screen, Sheet = window.Sheet;
  var toast = window.toast || function () {};

  /* ===================== I18N (PROJ-24) ===================== */
  var I18N = {
    de: {
      // Navigation / Allgemein
      'nav.zurueck': 'Zurück',
      'nav.protokoll': 'Protokoll',
      'nav.weiter': 'Weiter',
      'nav.ueberspringen': 'Überspringen',
      'nav.startseite': 'Zur Startseite',
      'nav.abbrechen': 'Abbrechen',
      // Start
      'start.brand': 'Reparatur-Helfer',
      'start.hero': 'Was ist kaputt?',
      'start.heroSub': 'Erzähl einfach, was los ist — als würdest du es einem Bekannten beschreiben.',
      'start.placeholder': '„Mein Toaster wirft das Brot nicht mehr aus …"',
      'start.methode.tippen': 'Tippen oder einsprechen',
      'start.methode.foto': 'Foto machen',
      'start.methode.etikett': 'Etikett scannen',
      // Loading
      'loading.moment': 'Einen Moment …',
      'loading.schaue': 'Ich schaue mir dein Problem an.',
      // Consent Gate (PROJ-22)
      'consent.titel': 'Einwilligung zur Datenverarbeitung',
      'consent.body': 'Um dir helfen zu können, verarbeitet diese App deine Gerätebeschreibung und Angaben zum Reparaturfall. Deine Daten werden nicht an Dritte verkauft.',
      'consent.trainingshinweis': 'Mit deiner Einwilligung kann dein anonymisierter Fall (ohne persönliche Daten) die Wissensbasis verbessern — du kannst das ablehnen, ohne dass die App weniger funktioniert.',
      'consent.verweis': 'Mehr dazu: Schwungrad-Beitrag (anonymisiert)',
      'consent.erteilen': 'Einverstanden',
      'consent.ablehnen': 'Ablehnen',
      'consent.widerrufen': 'Einwilligung widerrufen',
      'consent.status.erteilt': 'Einwilligung erteilt',
      'consent.status.abgelehnt': 'Einwilligung abgelehnt',
      'consent.status.widerrufen': 'Einwilligung widerrufen',
      'consent.abgelehntHinweis': 'Kein Problem — die App funktioniert weiter. Der Schwungrad-Beitrag entfällt.',
      // Diagnose kuratiert (PROJ-17)
      'diag.titel': 'Mögliche Ursachen',
      'diag.eyebrow': 'Diagnose',
      'diag.unklar': 'Keine verlässliche Eingrenzung möglich — weiter zum Unklar-Pfad.',
      'diag.weiter': 'Mit dieser Einschätzung weiter',
      'diag.abgrenzung': 'Abgrenzungsfrage',
      'diag.herkunft.kuratiert': 'Kuratiert',
      'diag.herkunft.ki': 'KI-Einschätzung',
      'diag.konfidenz.hoch': 'Hohe Konfidenz',
      'diag.konfidenz.mittel': 'Mittlere Konfidenz',
      'diag.konfidenz.niedrig': 'Niedrige Konfidenz',
      // Rückruf (PROJ-19)
      'recall.titel.rueckruf': '⛔ Offizieller Rückruf',
      'recall.titel.sicherheitsmangel': '⚠️ Sicherheitsmangel',
      'recall.unsicher': 'Modell nicht eindeutig identifiziert — kein bestätigter Rückruf.',
      'recall.weiter': 'Trotzdem fortfahren (auf eigene Verantwortung)',
      'recall.grund.label': 'Grund:',
      'recall.quelle.label': 'Quelle:',
      'recall.stand.label': 'Stand / gültig bis:',
      'recall.vorgehen.label': 'Vorgehen:',
      'recall.hinweis': 'Für dieses Gerät liegt ein offizieller Rückruf oder ein bekannter Sicherheitsmangel vor. Bitte zuerst dem angegebenen Vorgehen folgen, bevor eine Selbstreparatur in Betracht gezogen wird.',
      // Mehrfachdefekte (PROJ-21)
      'fazit.titel': 'Gesamt-Einschätzung',
      'fazit.knackpunkt': 'Kritischer Punkt:',
      'fazit.begruendung': 'Begründung:',
      'fazit.prioritaet': 'Priorisierung:',
      // Datenlöschung (PROJ-20)
      'wipe.titel': 'Datenschutz vor Abgabe',
      'wipe.eyebrow': 'Schutzschritt',
      'wipe.hinweis': 'Dieses Gerät speichert persönliche Daten. Bitte die folgenden Schritte vor der Abgabe durchführen.',
      'wipe.backup': 'Backup erstellt',
      'wipe.loeschen': 'Persönliche Daten gelöscht / Gerät zurückgesetzt',
      'wipe.abmelden': 'Von allen Konten abgemeldet',
      'wipe.warn': '⚠️ Nicht gelöscht: deine Daten könnten in fremden Händen landen.',
      'wipe.skip': 'Bewusst überspringen (nicht empfohlen)',
      'wipe.weiter': 'Fertig — weiter zur Abgabe',
      // Multimodal (PROJ-27)
      'media.foto': 'Foto aufnehmen',
      'media.video': 'Video aufnehmen',
      'media.sprache': 'Einsprechen',
      'media.barcode': 'Barcode/Etikett scannen',
      'media.consent.titel': 'Medien-Einwilligung',
      'media.consent.body': 'Für Foto- und Sprachaufnahmen wird kurz deine Kamera bzw. dein Mikrofon genutzt. Du kannst jederzeit zur Texteingabe zurückkehren.',
      'media.consent.ok': 'Einverstanden',
      'media.consent.nein': 'Nein danke',
      'media.unavail': 'Nicht verfügbar in diesem Browser',
      'media.toText': 'Zur Texteingabe',
      'media.qualityWarn': 'Bild zu dunkel oder unscharf — bitte erneut versuchen oder Text nutzen.',
      'media.voiceLive': 'Ich höre zu …',
      'media.voiceCorrect': 'Erkannter Text — bitte prüfen:',
      'media.scanResult': 'Gefundene Gerätedaten:',
      // Vision-Diagnose (PROJ-31)
      'media.dokument': 'Dokument/PDF beifügen',
      'media.limit': 'Höchstens {n} Medien pro Anfrage — bitte zuerst eins entfernen.',
      'media.unsupported': 'Dieses Format wird nicht unterstützt (erlaubt: Bilder JPG/PNG/WebP & PDF).',
      'start.fotoHint': 'Tipp: Ein Foto vom Gerät, Typenschild oder Schaden — oder die Rechnung als PDF — macht die Diagnose treffsicherer. Optional, reiner Text geht auch.',
      'vision.included': '📷 Bild in die Diagnose einbezogen',
      // Chat-Anhang (PROJ-31 Frontend)
      'chat.attach': 'Foto oder Dokument anhängen',
      'chat.attachHint': 'Bild wird zur Auswertung an die KI gesendet.',
      'chat.attachDefaultText': '(Bild angehängt)',
      'chat.attachUploading': 'Wird hochgeladen …',
      'chat.attachFail': 'Anhang konnte nicht hochgeladen werden.',
      'chat.attachRemove': 'Anhang entfernen',
      'extract.eyebrow': 'Prüfen',
      'extract.title': 'Das habe ich erkannt',
      'extract.intro': 'Bitte prüfe und korrigiere die Angaben, bevor die Diagnose startet. Jedes Feld kannst du ändern oder leeren.',
      'extract.f.kategorie': 'Gerätekategorie',
      'extract.f.modell': 'Modell / Typ',
      'extract.f.schaeden': 'Sichtbare Schäden',
      'extract.f.kaufdatum': 'Kaufdatum',
      'extract.f.haendler': 'Händler',
      'extract.f.hinweise': 'Hinweise aus Dokumenten',
      'extract.ph': 'nicht erkannt — hier eintragen',
      'extract.phItem': 'weiteren Eintrag hinzufügen',
      'extract.add': '+ Hinzufügen',
      'extract.confirm': 'Bestätigen & Diagnose starten',
      'extract.nothing': 'Ich konnte nichts Sicheres erkennen. Du kannst die Angaben manuell ergänzen, ein neues Foto/Dokument aufnehmen oder direkt mit der Text-Diagnose fortfahren.',
      'extract.retake': 'Neu aufnehmen',
      'extract.textonly': 'Ohne Bild fortfahren',
      'extract.conf.hoch': 'sicher erkannt',
      'extract.conf.mittel': 'erkannt',
      'extract.conf.niedrig': 'unsicher — bitte prüfen',
      // Lotse (PROJ-18)
      'steer.weiter': 'Weiter',
      'steer.profi': 'Profi / Café',
      'steer.austausch': 'Austausch',
      'steer.entsorgen': 'Entsorgen',
      'steer.abbrechen': 'Abbrechen',
      // Ampel-Stufen
      'level.gut': 'grün',
      'level.mittel': 'gelb',
      'level.stop': 'rot',
      // Nur-Deutsch-Badge
      'onlyde': 'Nur auf Deutsch verfügbar',
      // Empfehlung
      'recommend.self': 'Selbst reparieren',
      'recommend.pro': 'Profi empfohlen',
      'recommend.replace': 'Ersetzen empfohlen',
      'recommend.local': 'Hilfe vor Ort',
      // ===== Bestehende Stufe-1/2-Screens (PROJ-24 Retrofit) =====
      // Allgemein / AppBar
      'common.aufnahme': 'Aufnahme',
      'common.weiter': 'Weiter',
      'common.zurueck': 'Zurück',
      'common.ueberspringen': 'Überspringen',
      'common.ueberspringenArrow': 'Überspringen →',
      'common.startseite': 'Zur Startseite',
      'common.protokoll': 'Protokoll',
      'common.protokollTeilen': '📄 Protokoll ansehen & teilen',
      'common.quelle': 'Quelle',
      'common.nichtAngegeben': 'nicht angegeben',
      'common.aiWarn': 'Die KI kann sich irren — sieh das als Orientierung, nicht als Urteil.',
      'common.aiWarnStrong': '⚠️ Besonders hier gilt: ',
      // Ownership (PROJ-1)
      'owner.q': 'Ist das dein Gerät?',
      'owner.hint': 'Nur wichtig, falls Garantie oder Kosten eine Rolle spielen. Du musst nichts angeben.',
      'owner.yes': 'Ja, gehört mir',
      'owner.no': 'Nein',
      'owner.unknown': 'Weiß nicht',
      'owner.followupHint': 'Optionale Angaben — beide kannst du überspringen.',
      'owner.ownerPlaceholder': 'Wem gehört es? (z. B. Vermieter, Firma)',
      'owner.costPlaceholder': 'Wer trägt die Kosten?',
      // Triage (PROJ-2)
      'triage.eyebrow': 'Nachfragen',
      'triage.foot': 'Frage {i} von {n} · ich frage nur so viel, wie ich brauche',
      'triage.textPlaceholder': 'Optional: in eigenen Worten beschreiben …',
      'triage.frei': 'Nur frei antworten …',
      'triage.freiTag': 'frei beschrieben',
      // Ampel
      'ampel.eyebrow': 'Einschätzung',
      'ampel.title': 'Worauf du dich einlässt',
      'ampel.footer': 'Was möchtest du tun?',
      'ampel.confTitle': 'Woher kommt diese Einschätzung?',
      'ampel.confSource': 'Quelle: ',
      'ampel.confLevel': 'Wie sicher: ',
      'ampel.confFine': 'Die App verbietet dir nichts — je riskanter die Sache, desto deutlicher die Warnung. Die Verantwortung für dein Handeln bleibt bei dir.',
      'ampel.sheetBewertung': 'Bewertung: ',
      // Unclear (PROJ-4)
      'unclear.footer': 'Trotzdem zur Einschätzung →',
      'unclear.title': 'Ehrlich: keine verlässliche Eingrenzung möglich',
      'unclear.body': 'Mit den bisherigen Angaben kann ich die Ursache nicht seriös bestimmen. Ich täusche dir hier lieber keine Sicherheit vor. Dein Protokoll ist gespeichert — du kannst es behalten und weitergeben.',
      'unclear.dangerWarn': '⚠️ Dieses Gerät kann gefährlich sein. Auch wenn die Ursache unklar ist: bitte nicht selbst öffnen — der Profi-Weg hat Vorrang.',
      'unclear.titleShort': 'Unklar',
      'unclear.proT': 'Profi beauftragen',
      'unclear.proS': 'Fachbetrieb schaut sich das Gerät an',
      'unclear.localT': 'Repair Café finden',
      'unclear.localS': 'gemeinsam vor Ort eingrenzen',
      'unclear.communityT': 'Community fragen',
      'unclear.communityS': 'Forum / Gruppe mit deinem Protokoll',
      'unclear.share': ' Protokoll ansehen, exportieren & teilen',
      // Vergleich (PROJ-5)
      'compare.eyebrow': 'Vergleich aller Wege ',
      'compare.geschaetzt': 'geschätzt',
      'compare.repair': 'Selbst reparieren',
      'compare.pro': 'Profi-Reparatur',
      'compare.neu': 'Neu kaufen',
      'compare.entsorgung': 'Entsorgen',
      'compare.reco': '★ Empfehlung',
      'compare.geld': '💶 Geld',
      'compare.zeit': '⏱️ Zeit',
      'compare.umwelt': '🌍 Ökologie',
      'compare.versteckt': 'Versteckte Posten:',
      'compare.trustSource': 'KI-Einschätzung',
      'compare.trustReason': 'Geschätzte Vergleichswerte — keine belegten Preise.',
      // Förderung (PROJ-6)
      'foerder.head': '🎁 Mögliche Förderung & Reparatur-Bonus',
      'foerder.loading': 'Förderprogramme werden geladen …',
      'foerder.empty': 'Aktuell sind hier keine passenden Förderprogramme hinterlegt. Frag im Zweifel bei deiner Kommune oder deinem Bundesland nach.',
      'foerder.statusAktuell': 'aktuell',
      'foerder.statusVeraltet': 'evtl. veraltet',
      'foerder.statusAusgelaufen': 'ausgelaufen',
      'foerder.stand': 'Stand: ',
      'foerder.gueltigBis': ' · gültig bis: ',
      'foerder.unbekannt': 'unbekannt',
      'foerder.unbefristet': 'unbefristet',
      'foerder.quelle': 'Quelle ↗',
      'foerder.disclaimer': 'Unverbindlicher Hinweis — keine Zusage. Bedingungen beim Träger prüfen.',
      // Decision (PROJ-5/6)
      'decision.eyebrow': 'Entscheidung',
      'decision.title': 'Du entscheidest.',
      'decision.hintStop': 'Ehrlich: Selbst öffnen wäre gefährlich. Ich empfehle Hilfe vor Ort — du wägst ab.',
      'decision.hintGo': 'Ich empfehle, es selbst zu probieren. Aber du hast die Wahl.',
      'decision.selfT': "Ich mach's selbst",
      'decision.selfS': 'Schritt für Schritt begleitet',
      'decision.proT': 'Hilfe / Profi finden',
      'decision.proS': 'Repair Café, Werkstatt & Fachbetrieb in der Nähe',
      'decision.neuT': 'Neues Gerät vergleichen',
      'decision.neuS': 'Alternativen, ehrlich gegen die Reparatur gerechnet',
      'decision.entsorgungT': 'Entsorgen / Recycling',
      'decision.entsorgungS': 'fachgerechter Weg + Rohstoffe zurück',
      // Skill (PROJ-3)
      'skill.eyebrow': 'Bevor es losgeht',
      'skill.title': 'Wie sehr traust du dir das zu?',
      'skill.hint': 'Das steuert nur, wie ausführlich ich erkläre — keine Wertung. Du kannst es jederzeit umstellen.',
      'skill.anfaengerT': 'Eher Anfänger',
      'skill.anfaengerS': 'Ich erkläre jeden Schritt ausführlich.',
      'skill.geuebtT': 'Schon geübt',
      'skill.geuebtS': 'Knappe Anweisungen, kein Ballast.',
      'skill.outHint': 'Lieber doch nicht selbst? Völlig in Ordnung:',
      'skill.outPro': '🏪 Profi beauftragen',
      'skill.outLocal': '🤝 Repair Café / Hilfe vor Ort',
      'skill.outReplace': '♻️ Ersetzen / entsorgen',
      // Gate (PROJ-7)
      'gate.eyebrow': 'Kurz vorher',
      'gate.q': 'Wann hast du das Gerät gekauft?',
      'gate.hint': 'Nur eine grobe Zeitspanne — damit du keinen Garantie-Anspruch verschenkst. Überspringen ist okay.',
      'gate.age6m': 'Vor unter 6 Monaten',
      'gate.age624': 'Vor 6 Mon. – 2 Jahren',
      'gate.age2j': 'Vor über 2 Jahren',
      'gate.ageUnknown': 'Weiß nicht',
      'gate.alt': '✅ Älter als 2 Jahre — Gewährleistung greift in der Regel nicht mehr. Du kannst direkt loslegen.',
      'gate.warnLead': '⚠️ Achtung Gewährleistung: ',
      'gate.warnBody': 'Wenn du das Gerät selbst öffnest, kann dein Gewährleistungs-/Garantieanspruch verfallen. Bei einem echten Defekt ist eine Reklamation oft kostenlos.',
      'gate.reklamation': 'Reklamation prüfen',
      'gate.reklamationSub': 'kostenlos bei Hersteller/Händler',
      'gate.proceed': 'Trotzdem selbst reparieren →',
      'gate.skipFoot': 'Du kannst diese Frage überspringen.',
      // Repair (PROJ-8)
      'repair.step': 'Schritt {i}/{n}',
      'repair.dangerLead': '☠️ Dieser Schritt kann gefährlich sein. ',
      'repair.dangerBody': 'Bitte lies erst weiter, wenn du sicher bist. Es gibt jederzeit den Profi-Weg.',
      'repair.confirmQ': 'Zwei kurze Fragen — ehrlich an dich selbst:',
      'repair.confirmAdult': 'Ich bin volljährig.',
      'repair.confirmConfident': 'Ich traue mir diesen Schritt zu.',
      'repair.confirmFine': 'Ein „Nein" sperrt dich nicht — es ist nur ein ehrlicher Hinweis. Du entscheidest.',
      'repair.confirmProceed': 'Verstanden — Schritt anzeigen',
      'repair.confirmAlt': 'Lieber Profi finden',
      'repair.calloutDanger': '☠️ Lebensgefahr möglich — bitte genau lesen.',
      'repair.calloutSafetyPlug': '⚡ Sicherheit zuerst: erst ausstecken!',
      'repair.calloutSafety': '⚡ Sicherheit zuerst: aufpassen.',
      'repair.depthAnfaenger': 'Anfänger',
      'repair.depthGeuebt': 'Geübt',
      'repair.vorlesen': ' Vorlesen',
      'repair.exit': 'Das wird mir zu heikel — Profi finden',
      'repair.navZurueck': 'Zurück',
      'repair.navWeiter': 'Weiter →',
      'repair.navHandoff': 'Zum Profi & Protokoll →',
      'repair.navFinish': 'Fertig — hat’s geklappt?',
      'repair.handoff': '📎 Dein Protokoll wird automatisch mitgegeben — die Werkstatt muss nicht bei null anfangen.',
      'repair.parts': '🧩 Ersatzteile für diese Reparatur finden',
      // Result
      'result.askQ': 'Hat’s geklappt?',
      'result.askHint': 'Ganz ehrlich — beides ist völlig in Ordnung.',
      'result.yes': 'Ja! 🎉',
      'result.no': 'Noch nicht',
      'result.winQ': 'Geschafft!',
      'result.savedLab': 'gespart',
      'result.co2Lab': 'vermieden',
      'result.deviceLab': 'Gerät gerettet',
      'result.winFoot': 'Und ein Stück Selbstvertrauen fürs nächste Mal. Im Reparatur-Tagebuch festgehalten.',
      'result.winShare': ' Protokoll ansehen & teilen',
      'result.noQ': 'Kein Vorwurf.',
      'result.noHint': 'Du hast das Problem systematisch eingegrenzt — das war goldrichtig. Jetzt hilft dir ein Profi schneller, weil die halbe Arbeit schon getan ist.',
      'result.proFinish': 'Profi finden',
      'result.proSub': 'dein Protokoll geht automatisch mit',
      // Path
      'path.localT': 'Hilfe vor Ort',
      'path.localBody': 'In deiner Nähe gibt es Repair Cafés und Werkstätten. Nimm dein Protokoll mit — so versteht jede helfende Person dein Problem sofort.',
      'path.localSlot': 'Karte mit Repair Cafés',
      'path.proT': 'Profi beauftragen',
      'path.proBody': 'Dein Reparatur-Steckbrief geht direkt an die Werkstatt. Der Mechaniker fängt nicht bei null an — das spart Zeit und Geld.',
      'path.proSlot': 'Werkstatt-Anfrage gesendet',
      'path.replaceT': 'Fachgerecht ersetzen',
      'path.replaceBody': 'Wenn ein Neukauf wirklich klüger ist, ist das auch in Ordnung. So entsorgst du das alte Gerät richtig — und nimmst Rohstoffe in den Kreislauf zurück.',
      'path.replaceSlot': 'Wertstoffhof in der Nähe',
      'path.reklamationT': 'Reklamation einleiten',
      'path.reklamationBody': 'Wende dich mit deinem Protokoll an Händler oder Hersteller. Bei einem Defekt innerhalb der Gewährleistung ist die Reparatur oder der Austausch in der Regel kostenlos.',
      'path.reklamationSlot': 'Reklamations-Vorlage',
      'path.communityT': 'Community fragen',
      'path.communityBody': 'Teile dein Protokoll in einem Reparatur-Forum oder einer Gruppe. Mit den gesammelten Angaben können andere dir gezielter helfen.',
      'path.communitySlot': 'Community-Beitrag vorbereitet',
      // UnivTriage (PROJ-26)
      'univ.eyebrow': 'Systematische Aufnahme',
      'univ.loading': 'Die Fragen werden geladen …',
      'univ.foot': 'Frage {i} von {n} · systematische Aufnahme, gerätunabhängig',
      // Service-Screens (PROJ-11/12/13/14)
      'svc.curatedReason': 'Kuratierte Demodaten ({quelle}) — kein echter Anbieter-Nachweis.',
      'svc.curatedDefault': 'kuratierte Demodaten',
      'svc.empty': 'In deiner Region sind hier keine Einträge hinterlegt. Frag im Zweifel bei deiner Kommune nach — oder probier es ohne Ortsangabe.',
      'svc.locLabel': '📍 Ort / PLZ (optional)',
      'svc.locPlaceholder': 'z. B. 50667 oder Köln',
      'svc.suchen': 'Suchen',
      // Vermittlung (PROJ-11)
      'verm.eyebrow': 'Hilfe vor Ort',
      'verm.title': 'Anbieter in deiner Nähe',
      'verm.intro': 'Repair Cafés helfen kostenlos & ehrenamtlich. Werkstätten und Fachbetriebe arbeiten gegen Bezahlung. Du wählst frei.',
      'verm.loading': 'Anbieter werden geladen …',
      'verm.typRepaircafe': '🤝 Repair Café',
      'verm.typWerkstatt': '🔧 Werkstatt',
      'verm.typProfi': '🏪 Fachbetrieb',
      'verm.demo': 'Demo',
      'verm.schwerpunkt': 'Schwerpunkt: ',
      'verm.free': '🆓 ',
      'verm.freeDefault': 'kostenlos / ehrenamtlich',
      'verm.costDefault': 'kostenpflichtig',
      'verm.selected': '✓ Ausgewählt',
      'verm.select': 'Diesen Anbieter merken',
      // Entsorgung (PROJ-12)
      'ents.eyebrow': 'Entsorgung & Recycling',
      'ents.title': 'Fachgerecht entsorgen',
      'ents.intro': 'Elektrogeräte gehören nicht in den Hausmüll. So bringst du die Rohstoffe zurück in den Kreislauf.',
      'ents.loading': 'Entsorgungswege werden geladen …',
      'ents.emptyDefault': 'Kein lokaler Eintrag. Nach ElektroG nehmen Wertstoffhöfe und größere Händler Elektrogeräte kostenlos zurück.',
      'ents.artWertstoffhof': '♻️ Wertstoffhof',
      'ents.artRuecknahme': '🏬 Händler-Rücknahme',
      'ents.artSammelstelle': '📦 Sammelstelle',
      'ents.rohstoffe': '🔁 Rohstoffe: ',
      'ents.kostenDefault': 'meist kostenlos',
      'ents.selected': '✓ Ausgewählt',
      'ents.select': 'Diesen Weg merken',
      // Produktsuche (PROJ-13)
      'prod.eyebrow': 'Neu vs. Reparatur',
      'prod.title': 'Alternativen im Vergleich',
      'prod.intro': 'Gleiche Optik wie die Wege-Tabelle: Geld, Zeit & Ökologie je Gerät — ehrlich gegen die Reparatur gerechnet.',
      'prod.loading': 'Alternativen werden geladen …',
      'prod.emptyDefault': 'Für diese Kategorie sind keine Alternativen hinterlegt.',
      'prod.energieklasse': ' · Energieklasse ',
      'prod.setup': '🔧 Einrichtungsaufwand: ',
      'prod.selected': '✓ Gemerkt',
      'prod.select': 'Diese Alternative merken',
      // Beschaffung (PROJ-14)
      'besch.loading': 'Ersatzteile werden geladen …',
      'besch.emptyDefault': 'Für dieses Gerät sind keine Ersatzteile hinterlegt.',
      'besch.passendFuer': 'Passend für: ',
      'besch.oosDefault': 'Nicht lieferbar',
      'besch.herstellerAnfrage': ' — beim Hersteller anfragen: ',
      'besch.affiliate': '🔗 Partner-Link (Provision)',
      'besch.partnerDefault': 'Partner-Shop',
      'besch.orderDisclaimer': 'Über diesen Link erhalten wir ggf. eine Provision. Die Empfehlung folgt trotzdem nur dem günstigsten/sinnvollsten Bezug.',
      'besch.kept': '✓ Gemerkt',
      'besch.keep': 'Teil merken',
      'besch.head': '🧩 Ersatzteile beschaffen',
      'besch.intro': 'Günstigste Quelle zuerst. Eine Bestellung ist optional und klar als Partner-Link gekennzeichnet — nie vorausgewählt.',
      'besch.backToRepair': '← Zurück zur Reparatur',
      // Protokoll (PROJ-1/2/3/4/7/8/10)
      'proto.title': 'Reparatur-Steckbrief',
      'proto.unclearWarn': '🤔 Diagnose unklar — keine verlässliche Eingrenzung. Bitte einem Profi/Repair Café vorlegen.',
      'proto.symptom': 'Symptom',
      'proto.tested': 'Was schon getestet wurde',
      'proto.nothingYet': 'noch nichts erfasst',
      'proto.ownWords': 'In eigenen Worten',
      'proto.causeAmpel': 'Wahrscheinliche Ursache & Ampel',
      'proto.why': ' Warum schätzt die App das so ein?',
      'proto.whyQuelle': 'Quelle: ',
      'proto.whySicherheit': ' · Sicherheit: ',
      'proto.whyKiIrrt': '. Die KI kann sich irren.',
      'proto.koennenGarantie': 'Können & Garantie',
      'proto.selbsteinschaetzung': 'Selbsteinschätzung: ',
      'proto.gewaehrleistung': 'Gewährleistung: ',
      'proto.kauf': 'Kauf: ',
      'proto.wahl': ' · Wahl: ',
      'proto.wahlReklamation': 'Reklamation',
      'proto.wahlSelbst': 'selbst reparieren',
      'proto.nichtErfasst': 'nicht erfasst',
      'proto.geraetLabel': '👤 Gerät: ',
      'proto.kostenLabel': ' · Kosten: ',
      'proto.fremdWarn': '⚠️ Fremdes Gerät: vor jedem Eingriff Rücksprache mit Eigentümer/Kostenträger halten (D14).',
      'proto.sicherheitsBestaetigungen': 'Sicherheits-Bestätigungen',
      'proto.schritt': 'Schritt ',
      'proto.volljaehrig': ' — volljährig: ',
      'proto.zugetraut': ', zugetraut: ',
      'proto.ja': 'ja',
      'proto.nein': 'nein',
      'proto.vertrauenQuelle': 'Vertrauen & Quelle',
      'proto.wegeBeschaffung': 'Gewählte Wege & Beschaffung',
      'proto.anbieterLabel': '🤝 Anbieter: ',
      'proto.entsorgungLabel': '♻️ Entsorgungsweg: ',
      'proto.altLabel': '🆕 Alternativgerät: ',
      'proto.ersatzteileLabel': '🧩 Gemerkte Ersatzteile: ',
      'proto.affiliateDisclaimer': 'Bestelloptionen sind Partner-Links (Provision) — kennzeichnungspflichtig, nie vorausgewählt.',
      'proto.quelleLabel': ' · Quelle: ',
      'proto.kuratierteDemo': ' (kuratierte Demodaten)',
      'proto.exportText': 'Text',
      'proto.exportPdf': 'PDF',
      'proto.exportLink': 'Link',
      'proto.exportKopieren': 'Kopieren',
      'proto.linkNote': 'Wer den Link hat, kann den Vorgang lesen. Der Link läuft 30 Tage nach Erstellung ab.',
      'proto.emptyDevice': 'Noch kein Gerät erfasst — wähl auf der Startseite ein Gerät, dann fülle ich den Steckbrief im Hintergrund.',
      'proto.ownGehoertMir': 'gehört mir',
      'proto.ownZuKlaeren': 'zu klären',
      'proto.ownGehoertNicht': 'gehört nicht mir ({who})',
      // Protokoll Stufe-3
      'proto.einwilligung': 'Einwilligung',
      'proto.rueckruf': '⛔ Rückruf / Sicherheitsmangel',
      'proto.datenloeschung': 'Datenlöschung vor Abgabe',
      'proto.bewusstUebersprungen': ' · bewusst übersprungen',
      'proto.mehrfachdefekte': 'Mehrfachdefekte ({n})',
      'proto.gesamt': 'Gesamt: ',
      'proto.knackpunkt': ' · Knackpunkt: ',
      'proto.schwungrad': 'Schwungrad-Beitrag',
      'proto.beitragId': 'Beitrag-ID: ',
      'proto.ausgeschlossen': 'Ausgeschlossen: ',
      'proto.medien': 'Medien ({n})',
      // Diag (PROJ-17) KI-Badge
      'diag.kiShort': 'KI',
      // Toast-Meldungen
      'toast.diagnoseFail': 'Diagnose nicht möglich — versuch es nochmal.',
      'toast.copyOk': 'Protokoll in die Zwischenablage kopiert.',
      'toast.copyUnsupported': 'Kopieren wird hier nicht unterstützt — bitte den Link nutzen.',
      'toast.textFail': 'Konnte den Text nicht laden.',
      'toast.linkCopied': 'Link kopiert.',
      'toast.linkManual': 'Bitte den Link manuell markieren und kopieren.',
      'toast.vorgangFail': 'Konnte den Vorgang nicht speichern — bitte erneut versuchen.',
      'toast.vorgangNotFound': 'Vorgang nicht gefunden — neuer Start.',
      // Report / Download (PROJ-44)
      'report.open': 'Report herunterladen',
      'report.title': 'Report herunterladen',
      'report.varianteLabel': 'Variante',
      'report.pdf': 'PDF',
      'report.markdown': 'Markdown',
      'report.text': 'Text',
      'report.copy': 'Kopieren',
      'report.copyOk': 'Report in die Zwischenablage kopiert.',
      'report.pdfFail': 'PDF derzeit nicht verfügbar — bitte Markdown oder Text laden.',
    },
    en: {
      // Navigation / General
      'nav.zurueck': 'Back',
      'nav.protokoll': 'Report',
      'nav.weiter': 'Continue',
      'nav.ueberspringen': 'Skip',
      'nav.startseite': 'Back to start',
      'nav.abbrechen': 'Cancel',
      // Start
      'start.brand': 'Repair Helper',
      'start.hero': 'What is broken?',
      'start.heroSub': "Just describe what's happening — as if you were telling a friend.",
      'start.placeholder': 'My toaster does not pop the bread up anymore …',
      'start.methode.tippen': 'Type or speak',
      'start.methode.foto': 'Take a photo',
      'start.methode.etikett': 'Scan label',
      // Loading
      'loading.moment': 'Just a moment …',
      'loading.schaue': "I'm looking at your problem.",
      // Consent Gate
      'consent.titel': 'Data processing consent',
      'consent.body': 'To help you, this app processes your device description and repair details. Your data will not be sold to third parties.',
      'consent.trainingshinweis': 'With your consent, your anonymised case (no personal data) can improve the knowledge base — you can decline without the app working any less well.',
      'consent.verweis': 'More info: Flywheel contribution (anonymised)',
      'consent.erteilen': 'I agree',
      'consent.ablehnen': 'Decline',
      'consent.widerrufen': 'Withdraw consent',
      'consent.status.erteilt': 'Consent given',
      'consent.status.abgelehnt': 'Consent declined',
      'consent.status.widerrufen': 'Consent withdrawn',
      'consent.abgelehntHinweis': 'No problem — the app keeps working. The flywheel contribution is skipped.',
      // Diagnose kuratiert
      'diag.titel': 'Possible causes',
      'diag.eyebrow': 'Diagnosis',
      'diag.unklar': 'No reliable narrowing possible — continuing to unclear path.',
      'diag.weiter': 'Continue with this assessment',
      'diag.abgrenzung': 'Clarifying question',
      'diag.herkunft.kuratiert': 'Curated',
      'diag.herkunft.ki': 'AI estimate',
      'diag.konfidenz.hoch': 'High confidence',
      'diag.konfidenz.mittel': 'Medium confidence',
      'diag.konfidenz.niedrig': 'Low confidence',
      // Recall
      'recall.titel.rueckruf': '⛔ Official recall',
      'recall.titel.sicherheitsmangel': '⚠️ Safety defect',
      'recall.unsicher': 'Model not clearly identified — no confirmed recall.',
      'recall.weiter': 'Continue anyway (at your own risk)',
      'recall.grund.label': 'Reason:',
      'recall.quelle.label': 'Source:',
      'recall.stand.label': 'Date / valid until:',
      'recall.vorgehen.label': 'Action:',
      'recall.hinweis': 'An official recall or known safety defect exists for this device. Please follow the stated action before considering self-repair.',
      // Multi-defect
      'fazit.titel': 'Overall assessment',
      'fazit.knackpunkt': 'Critical point:',
      'fazit.begruendung': 'Reasoning:',
      'fazit.prioritaet': 'Priority order:',
      // Data wipe
      'wipe.titel': 'Data protection before handover',
      'wipe.eyebrow': 'Protection step',
      'wipe.hinweis': 'This device stores personal data. Please complete the following steps before handing it over.',
      'wipe.backup': 'Backup created',
      'wipe.loeschen': 'Personal data deleted / device reset',
      'wipe.abmelden': 'Signed out of all accounts',
      'wipe.warn': '⚠️ Not deleted: your data could end up in the wrong hands.',
      'wipe.skip': 'Skip consciously (not recommended)',
      'wipe.weiter': 'Done — continue to handover',
      // Multimodal
      'media.foto': 'Take photo',
      'media.video': 'Take video',
      'media.sprache': 'Speak',
      'media.barcode': 'Scan barcode/label',
      'media.consent.titel': 'Media consent',
      'media.consent.body': 'For photo and voice capture, your camera or microphone will be used briefly. You can always return to text input.',
      'media.consent.ok': 'I agree',
      'media.consent.nein': 'No thanks',
      'media.unavail': 'Not available in this browser',
      'media.toText': 'Back to text input',
      'media.qualityWarn': 'Image too dark or blurry — please try again or use text.',
      'media.voiceLive': 'Listening …',
      'media.voiceCorrect': 'Recognised text — please check:',
      'media.scanResult': 'Found device data:',
      // Vision diagnosis (PROJ-31)
      'media.dokument': 'Attach document/PDF',
      'media.limit': 'At most {n} media per request — please remove one first.',
      'media.unsupported': 'This format is not supported (allowed: images JPG/PNG/WebP & PDF).',
      'start.fotoHint': 'Tip: A photo of the device, type plate or damage — or the receipt as a PDF — makes the diagnosis more accurate. Optional, plain text works too.',
      'vision.included': '📷 Image used in the diagnosis',
      // Chat attachment (PROJ-31 frontend)
      'chat.attach': 'Attach a photo or document',
      'chat.attachHint': 'The image will be sent to the AI for analysis.',
      'chat.attachDefaultText': '(image attached)',
      'chat.attachUploading': 'Uploading …',
      'chat.attachFail': 'The attachment could not be uploaded.',
      'chat.attachRemove': 'Remove attachment',
      'extract.eyebrow': 'Review',
      'extract.title': 'Here is what I recognised',
      'extract.intro': 'Please check and correct the details before the diagnosis starts. You can change or clear every field.',
      'extract.f.kategorie': 'Device category',
      'extract.f.modell': 'Model / type',
      'extract.f.schaeden': 'Visible damage',
      'extract.f.kaufdatum': 'Purchase date',
      'extract.f.haendler': 'Retailer',
      'extract.f.hinweise': 'Notes from documents',
      'extract.ph': 'not recognised — enter here',
      'extract.phItem': 'add another entry',
      'extract.add': '+ Add',
      'extract.confirm': 'Confirm & start diagnosis',
      'extract.nothing': 'I could not reliably recognise anything. You can fill in the details manually, take a new photo/document, or continue with the text diagnosis.',
      'extract.retake': 'Capture again',
      'extract.textonly': 'Continue without image',
      'extract.conf.hoch': 'confidently recognised',
      'extract.conf.mittel': 'recognised',
      'extract.conf.niedrig': 'uncertain — please check',
      // Lotse
      'steer.weiter': 'Continue',
      'steer.profi': 'Pro / Café',
      'steer.austausch': 'Replace',
      'steer.entsorgen': 'Recycle',
      'steer.abbrechen': 'Cancel',
      // Levels
      'level.gut': 'green',
      'level.mittel': 'yellow',
      'level.stop': 'red',
      // Only-German badge
      'onlyde': 'Available in German only',
      // Recommend
      'recommend.self': 'Self-repair',
      'recommend.pro': 'Pro recommended',
      'recommend.replace': 'Replace recommended',
      'recommend.local': 'Local help',
      // ===== Existing Stufe-1/2 screens (PROJ-24 retrofit) =====
      // General / AppBar
      'common.aufnahme': 'Intake',
      'common.weiter': 'Continue',
      'common.zurueck': 'Back',
      'common.ueberspringen': 'Skip',
      'common.ueberspringenArrow': 'Skip →',
      'common.startseite': 'Back to start',
      'common.protokoll': 'Report',
      'common.protokollTeilen': '📄 View & share report',
      'common.quelle': 'Source',
      'common.nichtAngegeben': 'not specified',
      'common.aiWarn': 'The AI can be wrong — treat this as guidance, not a verdict.',
      'common.aiWarnStrong': '⚠️ Especially here: ',
      // Ownership
      'owner.q': 'Is this your device?',
      'owner.hint': 'Only relevant if warranty or costs matter. You do not have to provide anything.',
      'owner.yes': 'Yes, it is mine',
      'owner.no': 'No',
      'owner.unknown': "Don't know",
      'owner.followupHint': 'Optional details — you can skip both.',
      'owner.ownerPlaceholder': 'Who owns it? (e.g. landlord, company)',
      'owner.costPlaceholder': 'Who bears the costs?',
      // Triage
      'triage.eyebrow': 'Follow-up questions',
      'triage.foot': 'Question {i} of {n} · I only ask as much as I need',
      'triage.textPlaceholder': 'Optional: describe in your own words …',
      'triage.frei': 'Just answer freely …',
      'triage.freiTag': 'described freely',
      // Ampel
      'ampel.eyebrow': 'Assessment',
      'ampel.title': 'What you are getting into',
      'ampel.footer': 'What would you like to do?',
      'ampel.confTitle': 'Where does this assessment come from?',
      'ampel.confSource': 'Source: ',
      'ampel.confLevel': 'How certain: ',
      'ampel.confFine': 'The app forbids nothing — the riskier it is, the clearer the warning. The responsibility for your actions stays with you.',
      'ampel.sheetBewertung': 'Rating: ',
      // Unclear
      'unclear.footer': 'Go to the assessment anyway →',
      'unclear.title': 'Honestly: no reliable narrowing possible',
      'unclear.body': "With the details so far I cannot seriously determine the cause. I would rather not pretend any false certainty. Your report is saved — you can keep it and pass it on.",
      'unclear.dangerWarn': '⚠️ This device can be dangerous. Even if the cause is unclear: please do not open it yourself — the pro path takes priority.',
      'unclear.titleShort': 'Unclear',
      'unclear.proT': 'Hire a pro',
      'unclear.proS': 'A specialist takes a look at the device',
      'unclear.localT': 'Find a Repair Café',
      'unclear.localS': 'narrow it down together on site',
      'unclear.communityT': 'Ask the community',
      'unclear.communityS': 'forum / group with your report',
      'unclear.share': ' View, export & share report',
      // Compare
      'compare.eyebrow': 'Comparison of all paths ',
      'compare.geschaetzt': 'estimated',
      'compare.repair': 'Self-repair',
      'compare.pro': 'Pro repair',
      'compare.neu': 'Buy new',
      'compare.entsorgung': 'Recycle',
      'compare.reco': '★ Recommendation',
      'compare.geld': '💶 Money',
      'compare.zeit': '⏱️ Time',
      'compare.umwelt': '🌍 Ecology',
      'compare.versteckt': 'Hidden items:',
      'compare.trustSource': 'AI estimate',
      'compare.trustReason': 'Estimated comparison values — no verified prices.',
      // Förderung
      'foerder.head': '🎁 Possible funding & repair bonus',
      'foerder.loading': 'Loading funding programmes …',
      'foerder.empty': 'No matching funding programmes are listed here right now. When in doubt, ask your municipality or federal state.',
      'foerder.statusAktuell': 'current',
      'foerder.statusVeraltet': 'possibly outdated',
      'foerder.statusAusgelaufen': 'expired',
      'foerder.stand': 'As of: ',
      'foerder.gueltigBis': ' · valid until: ',
      'foerder.unbekannt': 'unknown',
      'foerder.unbefristet': 'open-ended',
      'foerder.quelle': 'Source ↗',
      'foerder.disclaimer': 'Non-binding note — no guarantee. Check the conditions with the provider.',
      // Decision
      'decision.eyebrow': 'Decision',
      'decision.title': 'You decide.',
      'decision.hintStop': 'Honestly: opening it yourself would be dangerous. I recommend local help — you weigh it up.',
      'decision.hintGo': 'I recommend trying it yourself. But the choice is yours.',
      'decision.selfT': "I'll do it myself",
      'decision.selfS': 'guided step by step',
      'decision.proT': 'Find help / a pro',
      'decision.proS': 'Repair Café, workshop & specialist nearby',
      'decision.neuT': 'Compare a new device',
      'decision.neuS': 'alternatives, honestly weighed against the repair',
      'decision.entsorgungT': 'Dispose / recycle',
      'decision.entsorgungS': 'proper route + raw materials returned',
      // Skill
      'skill.eyebrow': 'Before we start',
      'skill.title': 'How confident are you about this?',
      'skill.hint': 'This only controls how detailed my explanations are — no judgement. You can change it anytime.',
      'skill.anfaengerT': 'Rather a beginner',
      'skill.anfaengerS': 'I explain every step in detail.',
      'skill.geuebtT': 'Already experienced',
      'skill.geuebtS': 'Concise instructions, no ballast.',
      'skill.outHint': 'Rather not do it yourself? Totally fine:',
      'skill.outPro': '🏪 Hire a pro',
      'skill.outLocal': '🤝 Repair Café / local help',
      'skill.outReplace': '♻️ Replace / recycle',
      // Gate
      'gate.eyebrow': 'Just before',
      'gate.q': 'When did you buy the device?',
      'gate.hint': "Just a rough timeframe — so you don't waste a warranty claim. Skipping is fine.",
      'gate.age6m': 'Less than 6 months ago',
      'gate.age624': '6 months – 2 years ago',
      'gate.age2j': 'More than 2 years ago',
      'gate.ageUnknown': "Don't know",
      'gate.alt': '✅ Older than 2 years — the statutory warranty usually no longer applies. You can get started right away.',
      'gate.warnLead': '⚠️ Warranty warning: ',
      'gate.warnBody': 'If you open the device yourself, your statutory/manufacturer warranty claim may be void. For a genuine defect, a warranty claim is often free.',
      'gate.reklamation': 'Check warranty claim',
      'gate.reklamationSub': 'free of charge at manufacturer/retailer',
      'gate.proceed': 'Repair it myself anyway →',
      'gate.skipFoot': 'You can skip this question.',
      // Repair
      'repair.step': 'Step {i}/{n}',
      'repair.dangerLead': '☠️ This step can be dangerous. ',
      'repair.dangerBody': 'Please only read on when you are sure. The pro path is always available.',
      'repair.confirmQ': 'Two short questions — honestly to yourself:',
      'repair.confirmAdult': 'I am of legal age.',
      'repair.confirmConfident': 'I feel confident doing this step.',
      'repair.confirmFine': 'A "no" does not lock you out — it is just an honest hint. You decide.',
      'repair.confirmProceed': 'Understood — show the step',
      'repair.confirmAlt': 'Rather find a pro',
      'repair.calloutDanger': '☠️ Risk to life possible — please read carefully.',
      'repair.calloutSafetyPlug': '⚡ Safety first: unplug it first!',
      'repair.calloutSafety': '⚡ Safety first: be careful.',
      'repair.depthAnfaenger': 'Beginner',
      'repair.depthGeuebt': 'Experienced',
      'repair.vorlesen': ' Read aloud',
      'repair.exit': 'This is getting too risky for me — find a pro',
      'repair.navZurueck': 'Back',
      'repair.navWeiter': 'Continue →',
      'repair.navHandoff': 'To the pro & report →',
      'repair.navFinish': 'Done — did it work?',
      'repair.handoff': '📎 Your report is passed on automatically — the workshop does not have to start from scratch.',
      'repair.parts': '🧩 Find spare parts for this repair',
      // Result
      'result.askQ': 'Did it work?',
      'result.askHint': 'Honestly — either way is perfectly fine.',
      'result.yes': 'Yes! 🎉',
      'result.no': 'Not yet',
      'result.winQ': 'Done!',
      'result.savedLab': 'saved',
      'result.co2Lab': 'avoided',
      'result.deviceLab': 'device rescued',
      'result.winFoot': 'And a bit of confidence for next time. Recorded in the repair diary.',
      'result.winShare': ' View & share report',
      'result.noQ': 'No blame.',
      'result.noHint': 'You narrowed the problem down systematically — that was exactly right. Now a pro can help you faster, because half the work is already done.',
      'result.proFinish': 'Find a pro',
      'result.proSub': 'your report is sent along automatically',
      // Path
      'path.localT': 'Local help',
      'path.localBody': 'There are Repair Cafés and workshops near you. Take your report along — that way every helper understands your problem right away.',
      'path.localSlot': 'Map of Repair Cafés',
      'path.proT': 'Hire a pro',
      'path.proBody': 'Your repair profile goes straight to the workshop. The mechanic does not start from scratch — that saves time and money.',
      'path.proSlot': 'Workshop request sent',
      'path.replaceT': 'Replace properly',
      'path.replaceBody': 'If buying new really is the smarter choice, that is okay too. This way you dispose of the old device correctly — and return raw materials to the cycle.',
      'path.replaceSlot': 'Recycling centre nearby',
      'path.reklamationT': 'Start a warranty claim',
      'path.reklamationBody': 'Contact the retailer or manufacturer with your report. For a defect within the warranty period, repair or replacement is usually free.',
      'path.reklamationSlot': 'Warranty claim template',
      'path.communityT': 'Ask the community',
      'path.communityBody': 'Share your report in a repair forum or group. With the collected details, others can help you more precisely.',
      'path.communitySlot': 'Community post prepared',
      // UnivTriage
      'univ.eyebrow': 'Systematic intake',
      'univ.loading': 'Loading the questions …',
      'univ.foot': 'Question {i} of {n} · systematic intake, device-independent',
      // Service screens
      'svc.curatedReason': 'Curated demo data ({quelle}) — not a real provider record.',
      'svc.curatedDefault': 'curated demo data',
      'svc.empty': 'No entries are listed for your region here. When in doubt, ask your municipality — or try without a location.',
      'svc.locLabel': '📍 Location / postcode (optional)',
      'svc.locPlaceholder': 'e.g. 50667 or Cologne',
      'svc.suchen': 'Search',
      // Vermittlung
      'verm.eyebrow': 'Local help',
      'verm.title': 'Providers near you',
      'verm.intro': 'Repair Cafés help for free & voluntarily. Workshops and specialists work for payment. You choose freely.',
      'verm.loading': 'Loading providers …',
      'verm.typRepaircafe': '🤝 Repair Café',
      'verm.typWerkstatt': '🔧 Workshop',
      'verm.typProfi': '🏪 Specialist',
      'verm.demo': 'Demo',
      'verm.schwerpunkt': 'Focus: ',
      'verm.free': '🆓 ',
      'verm.freeDefault': 'free / voluntary',
      'verm.costDefault': 'chargeable',
      'verm.selected': '✓ Selected',
      'verm.select': 'Remember this provider',
      // Entsorgung
      'ents.eyebrow': 'Disposal & recycling',
      'ents.title': 'Dispose properly',
      'ents.intro': 'Electrical devices do not belong in household waste. This is how you return the raw materials to the cycle.',
      'ents.loading': 'Loading disposal routes …',
      'ents.emptyDefault': 'No local entry. Under the German ElektroG, recycling centres and larger retailers take back electrical devices free of charge.',
      'ents.artWertstoffhof': '♻️ Recycling centre',
      'ents.artRuecknahme': '🏬 Retailer take-back',
      'ents.artSammelstelle': '📦 Collection point',
      'ents.rohstoffe': '🔁 Raw materials: ',
      'ents.kostenDefault': 'usually free',
      'ents.selected': '✓ Selected',
      'ents.select': 'Remember this route',
      // Produktsuche
      'prod.eyebrow': 'New vs. repair',
      'prod.title': 'Alternatives compared',
      'prod.intro': 'Same look as the paths table: money, time & ecology per device — honestly weighed against the repair.',
      'prod.loading': 'Loading alternatives …',
      'prod.emptyDefault': 'No alternatives are listed for this category.',
      'prod.energieklasse': ' · Energy class ',
      'prod.setup': '🔧 Setup effort: ',
      'prod.selected': '✓ Remembered',
      'prod.select': 'Remember this alternative',
      // Beschaffung
      'besch.loading': 'Loading spare parts …',
      'besch.emptyDefault': 'No spare parts are listed for this device.',
      'besch.passendFuer': 'Fits: ',
      'besch.oosDefault': 'Not available',
      'besch.herstellerAnfrage': ' — ask the manufacturer: ',
      'besch.affiliate': '🔗 Partner link (commission)',
      'besch.partnerDefault': 'Partner shop',
      'besch.orderDisclaimer': 'Via this link we may receive a commission. The recommendation still follows only the cheapest/most sensible source.',
      'besch.kept': '✓ Remembered',
      'besch.keep': 'Remember part',
      'besch.head': '🧩 Source spare parts',
      'besch.intro': 'Cheapest source first. An order is optional and clearly marked as a partner link — never preselected.',
      'besch.backToRepair': '← Back to the repair',
      // Protokoll
      'proto.title': 'Repair profile',
      'proto.unclearWarn': '🤔 Diagnosis unclear — no reliable narrowing. Please present it to a pro / Repair Café.',
      'proto.symptom': 'Symptom',
      'proto.tested': 'What has been tested',
      'proto.nothingYet': 'nothing recorded yet',
      'proto.ownWords': 'In your own words',
      'proto.causeAmpel': 'Probable cause & traffic light',
      'proto.why': ' Why does the app assess it this way?',
      'proto.whyQuelle': 'Source: ',
      'proto.whySicherheit': ' · Certainty: ',
      'proto.whyKiIrrt': '. The AI can be wrong.',
      'proto.koennenGarantie': 'Skill & warranty',
      'proto.selbsteinschaetzung': 'Self-assessment: ',
      'proto.gewaehrleistung': 'Warranty: ',
      'proto.kauf': 'Purchase: ',
      'proto.wahl': ' · Choice: ',
      'proto.wahlReklamation': 'Warranty claim',
      'proto.wahlSelbst': 'self-repair',
      'proto.nichtErfasst': 'not recorded',
      'proto.geraetLabel': '👤 Device: ',
      'proto.kostenLabel': ' · Costs: ',
      'proto.fremdWarn': '⚠️ Third-party device: before any intervention, consult the owner/cost bearer (D14).',
      'proto.sicherheitsBestaetigungen': 'Safety confirmations',
      'proto.schritt': 'Step ',
      'proto.volljaehrig': ' — of legal age: ',
      'proto.zugetraut': ', confident: ',
      'proto.ja': 'yes',
      'proto.nein': 'no',
      'proto.vertrauenQuelle': 'Trust & source',
      'proto.wegeBeschaffung': 'Chosen paths & sourcing',
      'proto.anbieterLabel': '🤝 Provider: ',
      'proto.entsorgungLabel': '♻️ Disposal route: ',
      'proto.altLabel': '🆕 Alternative device: ',
      'proto.ersatzteileLabel': '🧩 Remembered spare parts: ',
      'proto.affiliateDisclaimer': 'Order options are partner links (commission) — subject to labelling, never preselected.',
      'proto.quelleLabel': ' · Source: ',
      'proto.kuratierteDemo': ' (curated demo data)',
      'proto.exportText': 'Text',
      'proto.exportPdf': 'PDF',
      'proto.exportLink': 'Link',
      'proto.exportKopieren': 'Copy',
      'proto.linkNote': 'Anyone with the link can read the case. The link expires 30 days after creation.',
      'proto.emptyDevice': 'No device recorded yet — pick a device on the start page, then I fill in the profile in the background.',
      'proto.ownGehoertMir': 'belongs to me',
      'proto.ownZuKlaeren': 'to be clarified',
      'proto.ownGehoertNicht': 'not mine ({who})',
      // Protokoll Stufe-3
      'proto.einwilligung': 'Consent',
      'proto.rueckruf': '⛔ Recall / safety defect',
      'proto.datenloeschung': 'Data deletion before handover',
      'proto.bewusstUebersprungen': ' · consciously skipped',
      'proto.mehrfachdefekte': 'Multiple defects ({n})',
      'proto.gesamt': 'Overall: ',
      'proto.knackpunkt': ' · Critical point: ',
      'proto.schwungrad': 'Flywheel contribution',
      'proto.beitragId': 'Contribution ID: ',
      'proto.ausgeschlossen': 'Excluded: ',
      'proto.medien': 'Media ({n})',
      // Diag AI badge
      'diag.kiShort': 'AI',
      // Toast messages
      'toast.diagnoseFail': 'Diagnosis not possible — please try again.',
      'toast.copyOk': 'Report copied to the clipboard.',
      'toast.copyUnsupported': 'Copying is not supported here — please use the link.',
      'toast.textFail': 'Could not load the text.',
      'toast.linkCopied': 'Link copied.',
      'toast.linkManual': 'Please select and copy the link manually.',
      'toast.vorgangFail': 'Could not save the case — please try again.',
      'toast.vorgangNotFound': 'Case not found — fresh start.',
      // Report / Download (PROJ-44)
      'report.open': 'Download report',
      'report.title': 'Download report',
      'report.varianteLabel': 'Variant',
      'report.pdf': 'PDF',
      'report.markdown': 'Markdown',
      'report.text': 'Text',
      'report.copy': 'Copy',
      'report.copyOk': 'Report copied to clipboard.',
      'report.pdfFail': 'PDF currently unavailable — please use Markdown or Text.',
    }
  };

  function interpolate(str, params) {
    if (!params) return str;
    return str.replace(/\{(\w+)\}/g, function (m, k) {
      return (params[k] != null) ? params[k] : m;
    });
  }

  // t(key) oder t(key, params) — params interpolieren {i},{n},{who},{quelle},…
  function t(key, params) {
    var lang = (window.RepairAppState && window.RepairAppState.lang) || 'de';
    var cat = I18N[lang] || I18N.de;
    if (cat[key] !== undefined) return interpolate(cat[key], params);
    // Fallback: deutscher Text mit Kennzeichnung
    var de = I18N.de[key];
    if (de !== undefined) return (lang !== 'de' ? '[DE] ' : '') + interpolate(de, params);
    return key;
  }
  window.RKt = t; // für screens.js

  /* ===================== THEME-TOKENS (Port von repair-themes.js) ===================== */
  var AMPEL = {
    gut: '#1f8a4c', gutBg: '#e7f4ec', gutInk: '#0f5a30',
    mittel: '#c98a00', mittelBg: '#fbf1d9', mittelInk: '#7a5400',
    stop: '#cf3a2c', stopBg: '#fbe6e3', stopInk: '#8a2018',
  };
  function ampelVars() {
    return {
      '--gut': AMPEL.gut, '--gut-bg': AMPEL.gutBg, '--gut-ink': AMPEL.gutInk,
      '--mittel': AMPEL.mittel, '--mittel-bg': AMPEL.mittelBg, '--mittel-ink': AMPEL.mittelInk,
      '--stop': AMPEL.stop, '--stop-bg': AMPEL.stopBg, '--stop-ink': AMPEL.stopInk,
    };
  }

  var SOLIDE = {
    id: 'solide', label: 'Solide',
    flags: { labelCase: 'none', chrome: 'light', hero: 'calm', mono: false },
    vars: Object.assign({
      '--bg': '#f6f5f2', '--surface': '#ffffff', '--surface-2': '#f1efea',
      '--ink': '#1b1a18', '--ink-soft': '#6c6862', '--line': '#e6e2db', '--line-strong': '#d8d3ca',
      '--accent': '#4940c9', '--accent-ink': '#ffffff', '--accent-soft': '#ecebfb',
      '--accent2': '#e8612c', '--accent2-soft': '#fdeee5',
      '--radius': '20px', '--radius-sm': '13px', '--radius-pill': '999px',
      '--shadow': '0 1px 2px rgba(20,18,14,.05), 0 8px 24px rgba(20,18,14,.06)',
      '--shadow-sm': '0 1px 2px rgba(20,18,14,.06)',
      '--font-display': "'IBM Plex Sans', system-ui, sans-serif",
      '--font-body': "'IBM Plex Sans', system-ui, sans-serif",
      '--font-mono': "'IBM Plex Mono', ui-monospace, monospace",
      '--display-weight': '600', '--display-tracking': '-0.01em',
      '--pad': '22px', '--gap': '12px',
    }, ampelVars()),
  };

  var WERKSTATT = {
    id: 'werkstatt', label: 'Werkstatt',
    flags: { labelCase: 'upper', chrome: 'light', hero: 'panel', mono: true },
    vars: Object.assign({
      '--bg': '#ecebe6', '--surface': '#ffffff', '--surface-2': '#f3f1ea',
      '--ink': '#16140f', '--ink-soft': '#5f5b52', '--line': '#dcd8cf', '--line-strong': '#16140f',
      '--accent': '#ff5a1f', '--accent-ink': '#16140f', '--accent-soft': '#ffe9dd',
      '--accent2': '#2a2575', '--accent2-soft': '#e6e4f5',
      '--radius': '12px', '--radius-sm': '8px', '--radius-pill': '8px',
      '--shadow': '4px 4px 0 #16140f', '--shadow-sm': '2px 2px 0 #16140f',
      '--font-display': "'Space Grotesk', system-ui, sans-serif",
      '--font-body': "'IBM Plex Sans', system-ui, sans-serif",
      '--font-mono': "'IBM Plex Mono', ui-monospace, monospace",
      '--display-weight': '700', '--display-tracking': '-0.02em',
      '--pad': '20px', '--gap': '11px',
    }, ampelVars()),
  };

  var MUTIG = {
    id: 'mutig', label: 'Mutig',
    flags: { labelCase: 'upper', chrome: 'dark', hero: 'bold', mono: true },
    vars: Object.assign({
      '--bg': '#141118', '--surface': '#211b29', '--surface-2': '#2e2640',
      '--ink': '#f7f3ee', '--ink-soft': '#a89fb5', '--line': '#352c44', '--line-strong': '#4a3f5e',
      '--accent': '#ff6a3d', '--accent-ink': '#1a1015', '--accent-soft': '#3a221c',
      '--accent2': '#9b8bff', '--accent2-soft': '#2a2350',
      '--radius': '22px', '--radius-sm': '14px', '--radius-pill': '999px',
      '--shadow': '0 18px 50px rgba(0,0,0,.5)', '--shadow-sm': '0 6px 18px rgba(0,0,0,.4)',
      '--font-display': "'Space Grotesk', system-ui, sans-serif",
      '--font-body': "'IBM Plex Sans', system-ui, sans-serif",
      '--font-mono': "'IBM Plex Mono', ui-monospace, monospace",
      '--display-weight': '700', '--display-tracking': '-0.03em',
      '--pad': '22px', '--gap': '12px',
      '--gut': AMPEL.gut, '--gut-bg': '#143524', '--gut-ink': '#7fe0a6',
      '--mittel': AMPEL.mittel, '--mittel-bg': '#3a2e10', '--mittel-ink': '#f3c969',
      '--stop': '#ff5a47', '--stop-bg': '#3a1a18', '--stop-ink': '#ff9d92',
    }),
  };

  var THEMES = { solide: SOLIDE, werkstatt: WERKSTATT, mutig: MUTIG };
  var DEFAULT_VARS = { '--font-size': '16px', '--motion': '.22s' };

  window.REPAIR_THEMES = THEMES;
  window.REPAIR_AMPEL = AMPEL;

  /* ===================== LANG-DETECT (PROJ-24) =====================
     Die App ist bewusst Deutsch-only („Nur auf Deutsch verfügbar"). Frühere
     Browser-Sprach-Erkennung schaltete bei englischem Browser ungewollt auf
     'en' und ließ Teile der Oberfläche englisch erscheinen — jetzt immer 'de'. */
  function detectLang() {
    return 'de';
  }

  /* ===================== STATE (Chat-Flow PROJ-37) =====================
     Konversations-Statemachine: ein Vorgang, ein linearer Verlauf aus
     User-/Assistenz-Bubbles. Karten kommen eingebettet je Assistenz-Turn.
     Die alte device-basierte Statemachine ist abgelöst. */
  var State = {
    themeId: 'werkstatt',
    lang: detectLang(),
    vorgangId: null,
    verlauf: [],        // [{ rolle:'user'|'assistant', text, karten?, abgebrochen? }]
    draft: '',          // aktuelle Eingabe (kein Re-Render bei Tippen)
    pending: false,     // Anfrage läuft (Denk-Indikator)
    error: null,        // letzter Fehler ({error, code}) — als Bubble gerendert
    abgebrochen: false, // Vorgang vom Lotsen beendet
    appEl: null,
    // PROJ-27/31: Medien + bestätigte Vision-Extraktion am Vorgang (Chat-Attach)
    medienConsent: false,
    medien: [],
    extraktion: null,
    // PROJ-31 Frontend: transiente, noch nicht gesendete Anhänge der nächsten Nachricht
    pendingMedien: [],       // [{ id, name, art }]
    mediaConsentOpen: false, // Consent-Sheet sichtbar?
    mediaUploading: false,   // läuft gerade ein Upload?
    // PROJ-44: Report-Sheet
    reportOpen: false,       // Report-Sheet sichtbar?
    reportVariante: 'uebergabe', // gewählte Variante
    reportVarianten: [],     // [{key, label, dateiname}] — geladen via /report/varianten
  };
  window.RepairAppState = State; // Debug-Hook

  /* ===================== VORGANG / CHAT (API-Vertrag) ===================== */
  function initVorgang() {
    return fetch('/api/vorgang', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lang: State.lang }),
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (res) {
        if (res && res.vorgang_id) {
          State.vorgangId = res.vorgang_id;
          try { history.replaceState(null, '', '?v=' + encodeURIComponent(res.vorgang_id)); } catch (e) {}
        }
        return State.vorgangId;
      })
      .catch(function () { return null; });
  }

  function sendeNachricht(text) {
    text = (text || '').trim();
    var medienIds = State.pendingMedien.map(function (m) { return m.id; });
    // Backend verlangt Text (empty→400). Bei reinen Anhängen einen kurzen
    // Default-Text mitsenden, damit Senden mit Bild + leerem Text funktioniert.
    if (!text && medienIds.length) text = t('chat.attachDefaultText');
    if (!text || State.pending || State.abgebrochen || State.mediaUploading) return;

    function doSend(vorgangId) {
      var pending = State.pendingMedien.slice();
      State.verlauf.push({ rolle: 'user', text: text, medien: pending });
      State.draft = '';
      State.error = null;
      State.pending = true;
      State.pendingMedien = []; // optimistisch leeren — bei Fehler wiederherstellen
      render();
      var body = { vorgang_id: vorgangId, text: text };
      if (medienIds.length) body.medienIds = medienIds;
      fetch('/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
        .then(function (r) { return r.json().catch(function () { return { code: 'ai_error' }; }); })
        .then(function (data) {
          State.pending = false;
          if (!data || data.code) {
            State.error = data || { code: 'ai_error' };
            State.pendingMedien = pending; // Anhänge erneut anbieten
            render();
            return;
          }
          if (data.vorgang_id && !State.vorgangId) State.vorgangId = data.vorgang_id;
          State.abgebrochen = !!data.abgebrochen;
          State.verlauf.push({
            rolle: 'assistant',
            text: data.antwort_text || '',
            karten: data.karten || [],
            abgebrochen: !!data.abgebrochen,
          });
          render();
        })
        .catch(function () {
          State.pending = false;
          State.error = { code: 'ai_error' };
          State.pendingMedien = pending; // Anhänge erneut anbieten
          render();
        });
    }

    if (State.vorgangId) {
      doSend(State.vorgangId);
    } else {
      // Vorgang fehlt (z. B. Anlage beim Start fehlgeschlagen) → jetzt anlegen.
      initVorgang().then(function (id) {
        if (!id) {
          State.verlauf.push({ rolle: 'user', text: text });
          State.draft = '';
          State.error = { code: 'no_vorgang' };
          render();
          return;
        }
        doSend(id);
      });
    }
  }

  function neuerVorgang() {
    State.verlauf = [];
    State.draft = '';
    State.error = null;
    State.pending = false;
    State.abgebrochen = false;
    State.vorgangId = null;
    State.pendingMedien = [];
    State.mediaConsentOpen = false;
    State.mediaUploading = false;
    State._pendingFiles = null;
    try { history.replaceState(null, '', location.pathname); } catch (e) {}
    render();
    initVorgang().then(function () { render(); });
  }

  /* ===================== MEDIEN-ANHANG (PROJ-31 Frontend) ===================== */
  // Medien-Art aus dem MIME-Typ ableiten (Backend kennt foto|dokument).
  function medienArt(file) {
    if (file && file.type === 'application/pdf') return 'dokument';
    if (file && /^image\//.test(file.type)) return 'foto';
    return 'dokument';
  }

  // Eine Datei an POST /api/vorgang/<vid>/medien hochladen → Promise({id,art,…}|null).
  function uploadEine(vorgangId, file) {
    var fd = new FormData();
    fd.append('file', file);
    return fetch('/api/vorgang/' + encodeURIComponent(vorgangId) + '/medien', {
      method: 'POST', body: fd,
    })
      .then(function (r) { return r.json().catch(function () { return null; }); })
      .then(function (res) {
        if (res && res.id) {
          return { id: res.id, name: file.name || (res.art || 'Anhang'), art: res.art || medienArt(file) };
        }
        return null;
      })
      .catch(function () { return null; });
  }

  // Dateiauswahl verarbeiten: Consent prüfen, Vorgang sicherstellen, hochladen.
  function verarbeiteDateien(fileList) {
    var files = [];
    for (var i = 0; i < (fileList ? fileList.length : 0); i++) files.push(fileList[i]);
    if (!files.length) return;
    if (State.abgebrochen) return;

    // Consent-Gate (PROJ-27): vor dem ersten Upload Einwilligung einholen.
    // Auswahl zwischenspeichern, damit der Upload nach Zustimmung weiterläuft.
    if (!State.medienConsent) {
      State._pendingFiles = files;
      State.mediaConsentOpen = true;
      render();
      return;
    }

    function start(vorgangId) {
      if (!vorgangId) { toast(t('chat.attachFail')); return; }
      State.mediaUploading = true;
      render();
      Promise.all(files.map(function (f) { return uploadEine(vorgangId, f); }))
        .then(function (results) {
          State.mediaUploading = false;
          var ok = false;
          results.forEach(function (m) {
            if (m) { State.pendingMedien.push(m); ok = true; }
          });
          if (!ok) toast(t('chat.attachFail'));
          render();
        });
    }

    if (State.vorgangId) start(State.vorgangId);
    else initVorgang().then(start);
  }

  function entfernePendingMedium(id) {
    State.pendingMedien = State.pendingMedien.filter(function (m) { return m.id !== id; });
    render();
  }

  // Consent-Sheet-Aktionen
  function onMediaConsentAccept() {
    State.medienConsent = true;
    State.mediaConsentOpen = false;
    // Zwischengespeicherte Auswahl jetzt automatisch hochladen.
    var queued = State._pendingFiles;
    State._pendingFiles = null;
    if (queued && queued.length) {
      verarbeiteDateien(queued);
    } else {
      render();
    }
  }
  function onMediaConsentDecline() {
    State.mediaConsentOpen = false;
    State._pendingFiles = null; // verworfene Auswahl nicht aufheben
    render();
  }

  /* ===================== PROJ-44: REPORT-HANDLER ===================== */

  function onReport() {
    if (!State.vorgangId) return;
    // Varianten laden, falls noch leer
    if (!State.reportVarianten.length) {
      fetch('/api/vorgang/' + encodeURIComponent(State.vorgangId) + '/report/varianten')
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (res) {
          if (res && Array.isArray(res.varianten)) {
            State.reportVarianten = res.varianten;
            State.reportVariante = res.default || 'uebergabe';
          }
          State.reportOpen = true;
          render();
        })
        .catch(function () {
          State.reportOpen = true;
          render();
        });
    } else {
      State.reportOpen = true;
      render();
    }
  }

  function onReportClose() {
    State.reportOpen = false;
    render();
  }

  function onReportVariante(key) {
    State.reportVariante = key;
    render();
  }

  // Sprechender Dateiname: <dateiname-der-variante>_<vorgang-id>.<ext> (AK PROJ-44:
  // enthält Vorgang-ID UND Variante). dateiname kommt aus /report/varianten;
  // Fallback auf den feststehenden Default, falls die Liste noch nicht geladen ist.
  function reportDateiname(ext) {
    var name = 'reparatur-uebergabe';
    (State.reportVarianten || []).forEach(function (v) {
      if (v && v.key === State.reportVariante && v.dateiname) name = v.dateiname;
    });
    return name + '_' + State.vorgangId + '.' + ext;
  }

  function onReportDownloadPdf() {
    if (!State.vorgangId) return;
    var url = '/api/vorgang/' + encodeURIComponent(State.vorgangId) +
      '/report.pdf?variante=' + encodeURIComponent(State.reportVariante);
    fetch(url)
      .then(function (res) {
        if (!res.ok) {
          // 503: PDF nicht verfügbar
          toast(t('report.pdfFail'));
          return null;
        }
        return res.blob();
      })
      .then(function (blob) {
        if (!blob) return;
        var objUrl = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = objUrl;
        a.download = reportDateiname('pdf');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(objUrl); }, 10000);
      })
      .catch(function () { toast(t('report.pdfFail')); });
  }

  function onReportDownloadMd() {
    if (!State.vorgangId) return;
    var url = '/api/vorgang/' + encodeURIComponent(State.vorgangId) +
      '/report.md?variante=' + encodeURIComponent(State.reportVariante);
    fetch(url)
      .then(function (res) { return res.ok ? res.blob() : null; })
      .then(function (blob) {
        if (!blob) { toast(t('toast.textFail')); return; }
        var objUrl = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = objUrl;
        a.download = reportDateiname('md');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(objUrl); }, 10000);
      })
      .catch(function () { toast(t('toast.textFail')); });
  }

  function onReportDownloadTxt() {
    if (!State.vorgangId) return;
    var url = '/api/vorgang/' + encodeURIComponent(State.vorgangId) +
      '/report.txt?variante=' + encodeURIComponent(State.reportVariante);
    fetch(url)
      .then(function (res) { return res.ok ? res.blob() : null; })
      .then(function (blob) {
        if (!blob) { toast(t('toast.textFail')); return; }
        var objUrl = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = objUrl;
        a.download = reportDateiname('txt');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(objUrl); }, 10000);
      })
      .catch(function () { toast(t('toast.textFail')); });
  }

  function onReportCopy() {
    if (!State.vorgangId) return;
    var url = '/api/vorgang/' + encodeURIComponent(State.vorgangId) +
      '/report.txt?variante=' + encodeURIComponent(State.reportVariante);
    fetch(url)
      .then(function (res) { return res.ok ? res.text() : null; })
      .then(function (text) {
        if (!text) { toast(t('toast.textFail')); return; }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text)
            .then(function () { toast(t('report.copyOk')); })
            .catch(function () { toast(t('toast.copyUnsupported')); });
        } else {
          toast(t('toast.copyUnsupported'));
        }
      })
      .catch(function () { toast(t('toast.textFail')); });
  }

  /* ===================== UI-SETTER ===================== */
  function setDraft(v) { State.draft = v; }   // kein Re-Render — Fokus erhalten
  function onSend() { sendeNachricht(State.draft); }

  /* ===================== RENDER / MOUNT ===================== */
  function render() {
    if (!State.appEl) return;
    var screen = window.ChatScreen({
      verlauf: State.verlauf,
      draft: State.draft,
      pending: State.pending,
      error: State.error,
      abgebrochen: State.abgebrochen,
      setDraft: setDraft,
      onSend: onSend,
      onRestart: neuerVorgang,
      // frage-Karte: Antwort auf eine Rückfrage als nächster Chat-Turn
      onAntwort: function (text) { sendeNachricht(text); },
      // PROJ-31: Anhang-Fluss
      pendingMedien: State.pendingMedien,
      mediaUploading: State.mediaUploading,
      mediaConsentOpen: State.mediaConsentOpen,
      onAttach: verarbeiteDateien,
      onRemovePending: entfernePendingMedium,
      onMediaConsentAccept: onMediaConsentAccept,
      onMediaConsentDecline: onMediaConsentDecline,
      // PROJ-44: Report-Sheet
      vorgangId: State.vorgangId,
      reportOpen: State.reportOpen,
      reportVariante: State.reportVariante,
      reportVarianten: State.reportVarianten,
      onReport: onReport,
      onReportClose: onReportClose,
      onReportVariante: onReportVariante,
      onReportDownloadPdf: onReportDownloadPdf,
      onReportDownloadMd: onReportDownloadMd,
      onReportDownloadTxt: onReportDownloadTxt,
      onReportCopy: onReportCopy,
    });
    State.appEl.replaceChildren(screen);
    // Nach dem Rendern ans Ende scrollen + Eingabe fokussieren.
    try {
      var body = State.appEl.querySelector('.rk-body');
      if (body) body.scrollTop = body.scrollHeight;
      if (!State.pending && !State.abgebrochen) {
        var inp = State.appEl.querySelector('.rk-chat-input');
        if (inp) inp.focus();
      }
    } catch (e) {}
  }

  function buildPhone() {
    var theme = THEMES[State.themeId];
    var vars = Object.assign({}, DEFAULT_VARS, theme.vars);
    var app = h('div', {
      class: 'rk-app rk-theme-' + theme.id + ' rk-case-' + theme.flags.labelCase,
      style: { fontSize: 'var(--font-size)' },
    });
    // Theme-Variablen direkt auf die App-Spalte setzen (vorher am .rk-phone).
    for (var v in vars) {
      if (Object.prototype.hasOwnProperty.call(vars, v)) app.style.setProperty(v, vars[v]);
    }
    State.appEl = app;
    var root = document.getElementById('phone-root');
    root.replaceChildren(app);
    render();
  }

  function buildThemeSwitch() {
    var wrap = document.getElementById('theme-switch');
    if (!wrap) return;
    var order = ['solide', 'werkstatt', 'mutig'];
    function paint() {
      var btns = wrap.querySelectorAll('button[data-id]');
      for (var i = 0; i < btns.length; i++) {
        var on = btns[i].getAttribute('data-id') === State.themeId;
        btns[i].className = 'rk-themebtn' + (on ? ' rk-themebtn-on' : '');
        btns[i].setAttribute('aria-selected', on ? 'true' : 'false');
      }
    }
    order.forEach(function (id) {
      var btn = h('button', {
        class: 'rk-themebtn', 'data-id': id, role: 'tab',
        onClick: function () { State.themeId = id; buildPhone(); paint(); },
      }, THEMES[id].label);
      wrap.appendChild(btn);
    });
    paint();
  }

  // Deutsch-only: Sprach-Umschalter ausgeblendet (wie zuvor).
  function buildLangSwitch() {
    var wrap = document.getElementById('lang-switch');
    if (!wrap) return;
    wrap.innerHTML = '';
    wrap.style.display = 'none';
  }

  /* ===================== INIT ===================== */
  function init() {
    buildThemeSwitch();
    buildLangSwitch();
    buildPhone();
    // Beim Start einen Vorgang anlegen (POST /api/vorgang).
    initVorgang().then(function () { render(); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
