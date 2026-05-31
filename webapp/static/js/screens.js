/* screens.js — die einzelnen Bildschirme der Repair-App als Vanilla-JS-DOM-Fabriken.
   Port von repair-screens.jsx + Stufe-1-Erweiterungen (PROJ-1…10).
   Liest Bausteine aus window (ui.js). Lokaler UI-State (Sheets, Result-Phase,
   Protokoll-Aufklappen, Drafts) wird von app.js gehalten und über Setter-Callbacks
   + props hereingereicht. */
(function () {
  'use strict';

  var h = window.h;
  var Screen = window.Screen, AppBar = window.AppBar, IconBtn = window.IconBtn;
  var BigButton = window.BigButton, GhostButton = window.GhostButton, AnswerChip = window.AnswerChip;
  var ProgressDots = window.ProgressDots, levelMeta = window.levelMeta, LightRow = window.LightRow;
  var Slot = window.Slot, Sheet = window.Sheet, TrustBadge = window.TrustBadge;
  var normTrustLevel = window.normTrustLevel;

  /* ---- i18n helper (PROJ-24) — delegates to app.js catalog via window.RKt ---- */
  function t(key, params) {
    return (window.RKt && window.RKt(key, params)) || key;
  }

  /* ---- Vertrauen aus state.trust ODER device.confidence ableiten (PROJ-25) ---- */
  function deriveTrust(trust, device) {
    var tr = trust || {};
    var conf = (device && device.confidence) || {};
    return {
      level: tr.level || normTrustLevel(conf.level),
      source: tr.source || conf.source || 'kuratiert',
      reason: tr.reason || conf.note || '',
    };
  }

  /* ---- Icons ---- */
  function BackIcon() {
    return h('svg', { width: '20', height: '20', viewBox: '0 0 20 20', fill: 'none' },
      h('path', { d: 'M12.5 4.5 7 10l5.5 5.5', stroke: 'currentColor', 'stroke-width': '1.7', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
  }
  function DocIcon() {
    return h('svg', { width: '19', height: '19', viewBox: '0 0 20 20', fill: 'none' },
      h('rect', { x: '4.5', y: '2.8', width: '11', height: '14.4', rx: '2', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('path', { d: 'M7.3 6.6h5.4M7.3 9.6h5.4M7.3 12.6h3.2', stroke: 'currentColor', 'stroke-width': '1.5', 'stroke-linecap': 'round' }));
  }
  function SpeakIcon() {
    return h('svg', { width: '18', height: '18', viewBox: '0 0 20 20', fill: 'none' },
      h('path', { d: 'M4 8v4h2.5L10 15V5L6.5 8H4Z', fill: 'currentColor' }),
      h('path', { d: 'M12.5 7.5a3.4 3.4 0 0 1 0 5M14.4 5.4a6 6 0 0 1 0 9.2', stroke: 'currentColor', 'stroke-width': '1.4', 'stroke-linecap': 'round' }));
  }

  function deviceTitle(device) {
    return h('span', { class: 'rk-bar-device' }, h('span', {}, device.emoji), device.name);
  }

  function docBtn(onClick) {
    return IconBtn({ onClick: onClick, label: t('common.protokoll'), children: DocIcon() });
  }

  /* ===================== START ===================== */
  function StartScreen(props) {
    var lang = props.lang || 'de';

    // PROJ-27: Voice-Ergebnis in Freitext einfügen
    function handleVoiceResult(transcript) {
      if (props.setDraft) props.setDraft(transcript);
      // In das Input-Feld schreiben falls vorhanden
      var inp = document.querySelector('.rk-input-ph[type=”text”]');
      if (inp) { inp.value = transcript; }
    }

    // LEGACY (Stufe 1/2) — StartScreen ist im Chat-Flow nicht mehr der Einstieg;
    // der aktive Einstieg ist ChatScreen (app.js, POST /api/vorgang + /api/chat).
    var input = h('div', { class: 'rk-input' },
      h('input', {
        class: 'rk-input-ph', type: 'text',
        placeholder: t('start.placeholder'),
        value: props.draft || '',
        style: { flex: '1', minWidth: '0', border: '0', background: 'transparent', outline: 'none', font: 'inherit', color: 'inherit' },
        onInput: function (e) { props.setDraft(e.target.value); },
        onKeydown: function (e) { if (e.key === 'Enter') { e.preventDefault(); props.onDiagnose(); } }
      }),
      h('span', { class: 'rk-input-mic', onClick: function () { props.onDiagnose(); } }, '🎙️')
    );

    // PROJ-27: echte Modalitäts-Buttons (MediaPanel)
    var mediaPanel = window.MediaPanel ? window.MediaPanel({
      medienConsent: props.medienConsent,
      medien: props.medien || [],
      lang: lang,
      setMediaConsentOpen: props.setMediaConsentOpen,
      uploadMedium: props.uploadMedium,
      uploadDokument: props.uploadDokument,
      removeMedium: props.removeMedium,
      onVoiceResult: handleVoiceResult,
      onBarcodeResult: function (val) {
        if (props.setDraft) props.setDraft(val);
      },
    }) : null;

    var consentGate = ConsentGateOverlay({
      show: !!props.showConsentGate,
      onErteilen: props.onConsentErteilen,
      onAblehnen: props.onConsentAblehnen,
    });

    // Hero "Was ist / kaputt?" — am Leerzeichen umbrechen für den <br>
    var heroFull = t('start.hero');
    var heroParts = heroFull.split(' ');
    var heroLine2 = heroParts.length > 1 ? heroParts.pop() : '';
    var heroLine1 = heroParts.join(' ');

    var children = [
      consentGate,
      h('div', { class: 'rk-brand' },
        h('span', { class: 'rk-brand-mark' }, '🔧'),
        h('span', { class: 'rk-brand-name' }, t('start.brand'))
      ),
      heroLine2
        ? h('h1', { class: 'rk-hero' }, heroLine1, h('br', {}), heroLine2)
        : h('h1', { class: 'rk-hero' }, heroFull),
      h('p', { class: 'rk-hero-sub' }, t('start.heroSub')),
      input,
      props.error
        ? h('p', { class: 'rk-q-hint', role: 'alert', style: { color: 'var(--stop)' } }, props.error)
        : null,
      // PROJ-31: aktiver, nicht-blockierender Hinweis, ein Foto/Dokument beizufügen.
      h('p', { class: 'rk-foto-hint' }, t('start.fotoHint')),
      mediaPanel
    ];

    return Screen({ bar: null, children: children });
  }

  /* ===================== EIGENTUM (PROJ-1) ===================== */
  function OwnershipScreen(props) {
    var device = props.device;
    var own = props.ownership || {};
    var opts = [
      { key: 'yes', label: t('owner.yes') },
      { key: 'no', label: t('owner.no') },
      { key: 'unknown', label: t('owner.unknown') },
    ];
    var consentGate = ConsentGateOverlay({
      show: !!props.showConsentGate,
      onErteilen: props.onConsentErteilen,
      onAblehnen: props.onConsentAblehnen,
    });
    var consentStatus = ConsentStatus({ consent: props.consent, onRevoke: props.onConsentRevoke });

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: BigButton({ variant: 'primary', onClick: props.onContinue, children: t('common.weiter') }),
      children: [
        consentGate,
        h('div', { class: 'rk-eyebrow' }, t('common.aufnahme')),
        h('h2', { class: 'rk-q rk-q-tight rk-owner-q' }, t('owner.q')),
        h('p', { class: 'rk-q-hint' }, t('owner.hint')),
        h('div', { class: 'rk-owner' },
          h('div', { class: 'rk-answers' }, opts.map(function (o) {
            return AnswerChip({
              active: own.isOwner === o.key,
              onClick: function () { props.setIsOwner(o.key); },
              children: o.label
            });
          })),
          own.isOwner === 'no' ? h('div', { class: 'rk-owner-followup' },
            h('p', { class: 'rk-q-hint' }, t('owner.followupHint')),
            h('input', {
              class: 'rk-owner-input', type: 'text',
              placeholder: t('owner.ownerPlaceholder'),
              value: props.draftOwner || '',
              onInput: function (e) { props.setDraftOwner(e.target.value); }
            }),
            h('input', {
              class: 'rk-owner-input', type: 'text',
              placeholder: t('owner.costPlaceholder'),
              value: props.draftCostBearer || '',
              onInput: function (e) { props.setDraftCostBearer(e.target.value); }
            })
          ) : null
        ),
        consentStatus
      ]
    });
  }

  /* ===================== TRIAGE (+ Freitext PROJ-2) ===================== */
  function TriageScreen(props) {
    var device = props.device, index = props.index;
    var q = device.triage[index];
    var n = device.triage.length;
    var ftVal = props.freitext || '';

    function charcount(v) {
      return h('div', { class: 'rk-charcount' + (v.length >= 500 ? ' rk-charcount-over' : ''), id: 'rk-charcount-' + index },
        v.length + '/500');
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: h('div', { class: 'rk-triage-foot' }, t('triage.foot', { i: index + 1, n: n })),
      children: [
        ProgressDots({ n: n, i: index }),
        h('div', { class: 'rk-eyebrow' }, t('triage.eyebrow')),
        h('h2', { class: 'rk-q' }, q.q),
        h('p', { class: 'rk-q-hint' }, q.hint),
        h('div', { class: 'rk-answers' }, q.options.map(function (o) {
          return AnswerChip({ onClick: function () { props.onAnswer(q.q, o.a, o.tag); }, children: o.a });
        })),
        h('div', { class: 'rk-triage-text-wrap' },
          h('textarea', {
            class: 'rk-triage-text', maxlength: '500', rows: '2',
            placeholder: t('triage.textPlaceholder'),
            onInput: function (e) {
              var v = e.target.value;
              props.setFreitext(index, v);
              var c = document.getElementById('rk-charcount-' + index);
              if (c) { c.textContent = v.length + '/500'; c.className = 'rk-charcount' + (v.length >= 500 ? ' rk-charcount-over' : ''); }
            }
          }, ftVal),
          charcount(ftVal)
        ),
        h('button', { class: 'rk-freeanswer', onClick: function () { props.onAnswer(q.q, t('triage.freiTag'), t('triage.freiTag')); } },
          h('span', {}, t('triage.frei')),
          h('span', { class: 'rk-input-mic' }, '🎙️')
        )
      ]
    });
  }

  /* ===================== AMPEL ===================== */
  function AmpelScreen(props) {
    var device = props.device;
    var stop = device.accentPath === 'stop';
    var activeLight = props.activeLight;
    var defekte = props.defekte || [];
    var gesamtFazit = props.gesamtFazit || null;
    var hasMultiDefekte = defekte.length >= 2;

    var children = [
      h('div', { class: 'rk-eyebrow' }, t('ampel.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight' }, t('ampel.title')),
    ];

    // Mehrfachdefekte: je-Defekt-Ampeln (PROJ-21) — bleibt permanent sichtbar
    if (hasMultiDefekte && window.GesamtFazitBlock) {
      children.push(window.GesamtFazitBlock({ defekte: defekte, gesamtFazit: gesamtFazit }));
    }

    // Standard-Ampelkarte (Einzelfall oder Fallback)
    children.push(
      h('div', { class: 'rk-ampelcard' }, device.lights.map(function (l) {
        return LightRow({ light: l, onInfo: function () { props.setActiveLight(l); } });
      }))
    );

    children.push(
      h('div', { class: 'rk-verdict ' + (stop ? 'rk-verdict-stop' : 'rk-verdict-go') },
        h('div', { class: 'rk-verdict-title' }, (stop ? '🔴 ' : '🟢 ') + device.verdictTitle),
        h('p', { class: 'rk-verdict-body' }, device.verdictBody)
      ),
      (function () {
        var tr = deriveTrust(props.trust, device);
        return TrustBadge(tr.level, tr.source, tr.reason, { onClick: function () { props.setConf(true); }, strong: stop });
      })(),
      // PROJ-31: Vermerk, dass Bildmaterial in die Diagnose eingeflossen ist.
      (props.visionMark && props.visionMark.einbezogen)
        ? h('div', { class: 'rk-vision-mark' }, t('vision.included'))
        : null,
      h('div', { class: 'rk-aiwarn ' + (stop ? 'rk-aiwarn-strong' : '') },
        (stop ? t('common.aiWarnStrong') : '') + t('common.aiWarn')
      )
    );

    // Lotse-Steuerleiste (PROJ-18)
    if (props.lotseOptionen && props.lotseOptionen.length) {
      children.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }

    children.push(
      Sheet({
        open: !!activeLight, onClose: function () { props.setActiveLight(null); },
        title: activeLight ? (activeLight.icon + ' ' + activeLight.key) : '',
        children: activeLight ? [
          h('p', { class: 'rk-sheet-note', style: { color: levelMeta(activeLight.level).ink } }, activeLight.note),
          h('div', { class: 'rk-sheet-level' },
            h('span', { class: 'rk-light-face', style: { background: levelMeta(activeLight.level).dot } }),
            levelMeta(activeLight.level).face + ' ' + t('ampel.sheetBewertung') + levelLabel(activeLight.level)
          )
        ] : null
      }),
      Sheet({
        open: props.conf, onClose: function () { props.setConf(false); }, title: t('ampel.confTitle'),
        children: [
          h('p', { class: 'rk-sheet-note' }, t('ampel.confSource'), h('b', {}, device.confidence.source)),
          h('p', { class: 'rk-sheet-note' }, t('ampel.confLevel'), h('b', {}, device.confidence.level)),
          h('p', { class: 'rk-sheet-note' }, device.confidence.note),
          h('div', { class: 'rk-sheet-hr' }),
          h('p', { class: 'rk-sheet-fine' }, t('ampel.confFine'))
        ]
      })
    );

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: BigButton({ variant: 'primary', onClick: props.onContinue, children: t('ampel.footer') }),
      children: children
    });
  }

  /* ---- lokalisiertes Ampel-Stufen-Label (levelMeta liefert nur DE) ---- */
  function levelLabel(level) {
    if (level === 'gut') return t('level.gut');
    if (level === 'mittel') return t('level.mittel');
    return t('level.stop');
  }

  /* ===================== UNKLAR-PFAD (PROJ-4) ===================== */
  function UnclearScreen(props) {
    var device = props.device;
    var dangerous = device && device.accentPath === 'stop';
    var paths = [
      { key: 'pro', e: '🏪', t: t('unclear.proT'), s: t('unclear.proS') },
      { key: 'local', e: '🤝', t: t('unclear.localT'), s: t('unclear.localS') },
      { key: 'community', e: '💬', t: t('unclear.communityT'), s: t('unclear.communityS') },
    ];
    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: device ? deviceTitle(device) : h('span', {}, t('unclear.titleShort')),
        right: docBtn(props.onProtocol)
      }),
      footer: GhostButton({ full: true, onClick: props.onAmpel, children: t('unclear.footer') }),
      children: [
        h('div', { class: 'rk-unclear' },
          h('div', { class: 'rk-unclear-emoji' }, '🤔'),
          h('h2', { class: 'rk-unclear-title' }, t('unclear.title')),
          h('p', { class: 'rk-unclear-body' }, t('unclear.body')),
          dangerous ? h('div', { class: 'rk-aiwarn rk-aiwarn-strong' }, t('unclear.dangerWarn')) : null,
          h('div', { class: 'rk-unclear-paths' }, paths.map(function (p) {
            return BigButton({
              variant: (dangerous && p.key === 'pro') ? 'primary' : 'soft',
              recommend: dangerous && p.key === 'pro',
              emoji: p.e, sub: p.s,
              onClick: function () { props.onForward(p.key); },
              children: p.t
            });
          })),
          h('button', { class: 'rk-share-line', onClick: props.onProtocol }, DocIcon(), t('unclear.share'))
        )
      ]
    });
  }

  /* ===================== VERGLEICH (PROJ-5) ===================== */
  function CompareBlock(compare, trust, device) {
    if (!compare) return null;
    var estTag = compare.geschaetzt
      ? h('span', { class: 'rk-est-tag' }, t('compare.geschaetzt'))
      : null;
    var defs = [
      { key: 'repair', e: '🛠️', t: t('compare.repair'), reco: 'repair' },
      { key: 'pro', e: '🏪', t: t('compare.pro'), reco: 'pro' },
      { key: 'neu', e: '🆕', t: t('compare.neu'), reco: 'neu' },
      { key: 'entsorgung', e: '♻️', t: t('compare.entsorgung'), reco: 'entsorgung' },
    ];
    function cell(label, value) {
      var v = value == null || value === '' ? '—' : value;
      var na = (typeof v === 'string' && v.indexOf('—') === 0);
      return h('div', { class: 'rk-compare-row' + (na ? ' rk-compare-na' : '') },
        h('span', { class: 'rk-compare-k' }, label),
        h('span', {}, v));
    }
    var cols = defs.map(function (d) {
      var p = compare[d.key] || {};
      var isReco = compare.empfehlung === d.reco;
      var children = [
        h('div', { class: 'rk-compare-head' }, h('span', {}, d.e + ' ' + d.t), isReco ? h('span', { class: 'rk-compare-reco' }, t('compare.reco')) : null),
        cell(t('compare.geld'), p.geld),
        cell(t('compare.zeit'), p.zeit),
        cell(t('compare.umwelt'), p.umwelt || p.oekologie),
      ];
      if (d.key === 'neu' && p.versteckt && p.versteckt.length) {
        children.push(
          h('div', { class: 'rk-compare-hidden' },
            h('div', { class: 'rk-compare-k' }, t('compare.versteckt')),
            p.versteckt.map(function (x) { return h('div', { class: 'rk-compare-hidden-item' }, '• ' + x); })
          )
        );
      } else if (p.hinweis) {
        children.push(h('div', { class: 'rk-compare-hidden-item' }, p.hinweis));
      }
      return h('div', { class: 'rk-compare-path' + (isReco ? ' rk-compare-reco' : '') }, children);
    });
    var estTrust = compare.geschaetzt
      ? (function () {
        var tr = deriveTrust(trust, device);
        return TrustBadge('mittel', tr.source || t('compare.trustSource'), tr.reason || t('compare.trustReason'));
      })()
      : null;
    return h('div', {},
      h('div', { class: 'rk-eyebrow' }, t('compare.eyebrow'), estTag),
      h('div', { class: 'rk-compare-4' }, cols),
      estTrust,
      compare.begruendung ? h('div', { class: 'rk-compare-begruendung' }, '💡 ' + compare.begruendung) : null
    );
  }

  /* ===================== FÖRDERUNG (PROJ-6) ===================== */
  function FoerderBlock(foerder) {
    var head = h('div', { class: 'rk-foerder-head' }, t('foerder.head'));
    if (foerder == null) {
      return h('div', { class: 'rk-foerder' }, head, h('div', { class: 'rk-foerder-empty' }, t('foerder.loading')));
    }
    if (!foerder.length) {
      return h('div', { class: 'rk-foerder' }, head,
        h('div', { class: 'rk-foerder-empty' }, t('foerder.empty')));
    }
    var items = foerder.map(function (f) {
      var status = f.status || 'aktuell';
      var badgeCls = 'rk-foerder-badge';
      // FIX E: Status-Klasse zusätzlich am Item-Container (Background-Tint)
      var itemCls = 'rk-foerder-item';
      if (status === 'veraltet') { badgeCls += ' rk-foerder-stale'; itemCls += ' rk-foerder-stale'; }
      else if (status === 'ausgelaufen') { badgeCls += ' rk-foerder-expired'; itemCls += ' rk-foerder-expired'; }
      var statusLabel = status === 'ausgelaufen' ? t('foerder.statusAusgelaufen') : status === 'veraltet' ? t('foerder.statusVeraltet') : t('foerder.statusAktuell');
      return h('div', { class: itemCls },
        h('div', { class: 'rk-foerder-name' }, f.bezeichnung, h('span', { class: badgeCls }, statusLabel)),
        h('div', { class: 'rk-foerder-meta' }, (f.region ? f.region + ' · ' : '') + (f.traeger || '')),
        f.beschreibung ? h('p', { class: 'rk-foerder-meta' }, f.beschreibung) : null,
        h('div', { class: 'rk-foerder-meta' }, t('foerder.stand') + (f.stand || t('foerder.unbekannt')) + t('foerder.gueltigBis') + (f.gueltigBis || t('foerder.unbefristet'))),
        f.quelle ? h('a', { class: 'rk-foerder-src', href: f.quelle, target: '_blank', rel: 'noopener noreferrer' }, t('foerder.quelle')) : null,
        h('div', { class: 'rk-foerder-disclaimer' }, t('foerder.disclaimer'))
      );
    });
    return h('div', { class: 'rk-foerder' }, head, items);
  }

  /* ===================== ENTSCHEIDUNG (PROJ-5 + PROJ-6) ===================== */
  // device.recommend (self|local|pro|replace) → 4-Pfad-Empfehlungsschlüssel (repair|pro|neu|entsorgung)
  function recoKey(device) {
    var c = device.compare || {};
    if (c.empfehlung) return c.empfehlung;
    var r = device.recommend;
    if (r === 'self') return 'repair';
    if (r === 'local' || r === 'pro') return 'pro';
    if (r === 'replace') return 'neu';
    return 'repair';
  }

  function DecisionScreen(props) {
    var device = props.device;
    var stop = device.accentPath === 'stop';
    var reco = recoKey(device);
    // 4 Pfade konsistent zur compare-Optik (repair/pro/neu/entsorgung)
    var paths = [
      { key: 'self', reco: 'repair', e: '🛠️', t: t('decision.selfT'), s: t('decision.selfS') },
      { key: 'pro', reco: 'pro', e: '🏪', t: t('decision.proT'), s: t('decision.proS') },
      { key: 'neu', reco: 'neu', e: '🆕', t: t('decision.neuT'), s: t('decision.neuS') },
      { key: 'entsorgung', reco: 'entsorgung', e: '♻️', t: t('decision.entsorgungT'), s: t('decision.entsorgungS') },
    ];
    var decisionChildren = [
      h('div', { class: 'rk-eyebrow' }, t('decision.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight' }, t('decision.title')),
      h('p', { class: 'rk-q-hint' }, stop ? t('decision.hintStop') : t('decision.hintGo')),
      CompareBlock(device.compare, props.trust, device),
      FoerderBlock(props.foerder),
      h('div', { class: 'rk-paths' }, paths.map(function (p) {
        return BigButton({
          variant: p.reco === reco ? 'primary' : 'soft',
          recommend: p.reco === reco,
          emoji: p.e, sub: p.s,
          onClick: function () { props.onChoose(p.key); },
          children: p.t
        });
      }))
    ];
    if (props.lotseOptionen && props.lotseOptionen.length) {
      decisionChildren.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }
    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      children: decisionChildren
    });
  }

  /* ===================== FÄHIGKEITS-RÜCKFRAGE (PROJ-3) ===================== */
  function SkillAskScreen(props) {
    var device = props.device;
    var skill = props.skill;
    // key bleibt DE (State-Wert); t/s lokalisiert
    var levels = [
      { key: 'Anfänger', e: '🌱', t: t('skill.anfaengerT'), s: t('skill.anfaengerS') },
      { key: 'Geübt', e: '🔧', t: t('skill.geuebtT'), s: t('skill.geuebtS') },
    ];
    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      children: [
        h('div', { class: 'rk-eyebrow' }, t('skill.eyebrow')),
        h('h2', { class: 'rk-q rk-q-tight' }, t('skill.title')),
        h('p', { class: 'rk-q-hint' }, t('skill.hint')),
        h('div', { class: 'rk-skillask' }, levels.map(function (l) {
          return BigButton({
            variant: skill === l.key ? 'primary' : 'soft',
            emoji: l.e, sub: l.s,
            onClick: function () { props.onPick(l.key); },
            children: l.t
          });
        })),
        h('div', { class: 'rk-skill-out' },
          h('p', { class: 'rk-q-hint' }, t('skill.outHint')),
          GhostButton({ full: true, onClick: function () { props.onOut('pro'); }, children: t('skill.outPro') }),
          GhostButton({ full: true, onClick: function () { props.onOut('local'); }, children: t('skill.outLocal') }),
          GhostButton({ full: true, onClick: function () { props.onOut('replace'); }, children: t('skill.outReplace') })
        )
      ]
    });
  }

  /* ===================== GARANTIE-GATE (PROJ-7) ===================== */
  function GateScreen(props) {
    var device = props.device;
    var w = props.warranty || {};
    var age = w.purchaseAge || '';
    var answered = !!w.asked || age !== '';
    var inWarranty = answered && age !== '>2J'; // unbekannt/jung => vorsorglich warnen
    var ages = [
      { key: '<6M', label: t('gate.age6m') },
      { key: '6-24M', label: t('gate.age624') },
      { key: '>2J', label: t('gate.age2j') },
      { key: 'unbekannt', label: t('gate.ageUnknown') },
    ];
    var children = [
      h('div', { class: 'rk-eyebrow' }, t('gate.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight rk-gate-q' }, t('gate.q')),
      h('p', { class: 'rk-q-hint' }, t('gate.hint')),
      h('div', { class: 'rk-gate' },
        h('div', { class: 'rk-answers' }, ages.map(function (a) {
          return AnswerChip({ active: age === a.key, onClick: function () { props.onAnswer(a.key); }, children: a.label });
        }))
      )
    ];

    if (answered && age === '>2J') {
      children.push(h('div', { class: 'rk-gate-alt' }, t('gate.alt')));
    } else if (inWarranty) {
      children.push(
        h('div', { class: 'rk-gate-warn' },
          h('b', {}, t('gate.warnLead')),
          t('gate.warnBody')),
        h('div', { class: 'rk-gate-actions' },
          BigButton({ variant: 'primary', emoji: '📮', sub: t('gate.reklamationSub'), onClick: props.onReklamation, children: t('gate.reklamation') }),
          h('button', { class: 'rk-ghost rk-full rk-gate-proceed', onClick: props.onProceed }, t('gate.proceed'))
        )
      );
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: answered ? null : h('div', { class: 'rk-triage-foot' }, t('gate.skipFoot')),
      children: children.concat(answered ? [] : [
        GhostButton({ full: true, onClick: function () { props.onAnswer('unbekannt'); }, children: t('common.ueberspringen') })
      ])
    });
  }

  /* ===================== REPARATUR-BEGLEITUNG (+ Sicherheit PROJ-8) ===================== */
  function RepairScreen(props) {
    var device = props.device, index = props.index, depth = props.depth;
    var step = device.steps[index];
    var n = device.steps.length;
    var last = index === n - 1;
    var body = depth === 'Geübt' ? step.pro : step.beginner;

    var bar = AppBar({
      left: IconBtn({ onClick: props.onPrev, label: t('common.zurueck'), children: BackIcon() }),
      title: h('span', { class: 'rk-bar-step' }, t('repair.step', { i: index + 1, n: n })),
      right: docBtn(props.onProtocol)
    });

    // PROJ-8: Sicherheits-Bestätigung vor dem Schritt (gefährlicher Schritt, noch nicht bestätigt)
    if (props.needsConfirm) {
      return Screen({
        bar: bar,
        children: [
          h('div', { class: 'rk-confirm' },
            h('div', { class: 'rk-confirm-warn' },
              h('b', {}, t('repair.dangerLead')),
              t('repair.dangerBody')),
            h('h2', { class: 'rk-step-title' }, step.title),
            h('div', { class: 'rk-confirm-q' }, t('repair.confirmQ')),
            h('button', {
              class: 'rk-confirm-row' + (props.confirmAdult ? ' rk-answer-on' : ''),
              onClick: function () { props.setConfirmAdult(!props.confirmAdult); }
            }, (props.confirmAdult ? '☑' : '☐') + ' ' + t('repair.confirmAdult')),
            h('button', {
              class: 'rk-confirm-row' + (props.confirmConfident ? ' rk-answer-on' : ''),
              onClick: function () { props.setConfirmConfident(!props.confirmConfident); }
            }, (props.confirmConfident ? '☑' : '☐') + ' ' + t('repair.confirmConfident')),
            h('p', { class: 'rk-sheet-fine' }, t('repair.confirmFine')),
            h('div', { class: 'rk-confirm-actions' },
              h('button', { class: 'rk-nav rk-nav-primary rk-confirm-proceed', onClick: function () { props.onConfirm(props.confirmAdult, props.confirmConfident); } }, t('repair.confirmProceed')),
              // FIX C: Profi-Alternative trägt rk-confirm-alt (Contract §6)
              h('button', { class: 'rk-ghost rk-full rk-confirm-alt', onClick: props.onExit }, t('repair.confirmAlt'))
            )
          )
        ]
      });
    }

    var callout = null;
    if (step.danger) {
      callout = h('div', { class: 'rk-callout rk-callout-danger' }, t('repair.calloutDanger'));
    } else if (step.safety) {
      callout = h('div', { class: 'rk-callout rk-callout-safety' },
        (step.title === 'Stecker ziehen' ? t('repair.calloutSafetyPlug') : t('repair.calloutSafety')));
    }

    var navrow = h('div', { class: 'rk-navrow' },
      index > 0 ? h('button', { class: 'rk-nav rk-nav-ghost', onClick: props.onPrev }, t('repair.navZurueck')) : h('span', {}),
      h('button', { class: 'rk-nav rk-nav-primary', onClick: last ? props.onFinish : props.onNext },
        last ? (step.handoff ? t('repair.navHandoff') : t('repair.navFinish')) : t('repair.navWeiter'))
    );

    return Screen({
      bar: bar,
      footer: h('div', { class: 'rk-repair-foot' },
        GhostButton({ onClick: props.onExit, children: t('repair.exit') }),
        navrow
      ),
      children: [
        h('div', { class: 'rk-repair-tools' },
          h('div', { class: 'rk-depth' },
            h('button', { class: depth === 'Anfänger' ? 'on' : '', onClick: function () { props.onDepth('Anfänger'); } }, t('repair.depthAnfaenger')),
            h('button', { class: depth === 'Geübt' ? 'on' : '', onClick: function () { props.onDepth('Geübt'); } }, t('repair.depthGeuebt'))
          ),
          h('button', { class: 'rk-speak' }, SpeakIcon(), t('repair.vorlesen'))
        ),
        Slot({ label: step.slot, h: 158 }),
        callout,
        h('h2', { class: 'rk-step-title' }, step.title),
        h('p', { class: 'rk-step-body' }, body),
        step.handoff ? h('div', { class: 'rk-handoff' }, t('repair.handoff')) : null,
        // PROJ-14: Beschaffungs-Einstieg innerhalb des Repair-Flows (Schicht B)
        props.onParts ? h('button', { class: 'rk-share-line', onClick: props.onParts }, t('repair.parts')) : null
      ]
    });
  }

  /* ===================== RÜCKBLICK (Selbst-Reparatur) ===================== */
  function ResultScreen(props) {
    var device = props.device;
    var phase = props.phase || 'ask';
    if (phase === 'ask') {
      return Screen({
        bar: AppBar({ left: h('span', {}), title: deviceTitle(device), right: docBtn(props.onProtocol) }),
        children: [
          h('div', { class: 'rk-result-center' },
            h('div', { class: 'rk-result-emoji' }, '🤞'),
            h('h2', { class: 'rk-result-q' }, t('result.askQ')),
            h('p', { class: 'rk-q-hint', style: { textAlign: 'center' } }, t('result.askHint')),
            h('div', { class: 'rk-result-btns' },
              h('button', { class: 'rk-nav rk-nav-primary rk-big-yes', onClick: function () { props.setPhase('yes'); } }, t('result.yes')),
              h('button', { class: 'rk-nav rk-nav-ghost rk-big-no', onClick: function () { props.setPhase('no'); } }, t('result.no'))
            )
          )
        ]
      });
    }
    if (phase === 'yes') {
      return Screen({
        bar: AppBar({ left: h('span', {}), title: deviceTitle(device), right: docBtn(props.onProtocol) }),
        footer: GhostButton({ full: true, onClick: props.onRestart, children: t('common.startseite') }),
        children: [
          h('div', { class: 'rk-win' },
            h('div', { class: 'rk-result-emoji' }, '🎉'),
            h('h2', { class: 'rk-result-q' }, t('result.winQ')),
            h('p', { class: 'rk-q-hint', style: { textAlign: 'center' } }, device.success.line),
            h('div', { class: 'rk-impact' },
              h('div', { class: 'rk-impact-cell' }, h('span', { class: 'rk-impact-num' }, device.success.saved), h('span', { class: 'rk-impact-lab' }, t('result.savedLab'))),
              h('div', { class: 'rk-impact-cell' }, h('span', { class: 'rk-impact-num' }, device.success.co2), h('span', { class: 'rk-impact-lab' }, t('result.co2Lab'))),
              h('div', { class: 'rk-impact-cell' }, h('span', { class: 'rk-impact-num' }, '1'), h('span', { class: 'rk-impact-lab' }, t('result.deviceLab')))
            ),
            h('p', { class: 'rk-win-foot' }, t('result.winFoot')),
            h('button', { class: 'rk-share-line', onClick: props.onProtocol }, DocIcon(), t('result.winShare'))
          )
        ]
      });
    }
    // phase === 'no'
    return Screen({
      bar: AppBar({ left: h('span', {}), title: deviceTitle(device), right: docBtn(props.onProtocol) }),
      footer: BigButton({ variant: 'primary', emoji: '🏪', sub: t('result.proSub'), onClick: props.onPro, children: t('result.proFinish') }),
      children: [
        h('div', { class: 'rk-win' },
          h('div', { class: 'rk-result-emoji' }, '🧭'),
          h('h2', { class: 'rk-result-q' }, t('result.noQ')),
          h('p', { class: 'rk-q-hint', style: { textAlign: 'center' } }, t('result.noHint'))
        )
      ]
    });
  }

  /* ===================== WEG-ERGEBNIS (lokal / profi / ersetzen / reklamation / community) ===================== */
  function PathScreen(props) {
    var device = props.device;
    var map = {
      local: { e: '🤝', t: t('path.localT'), body: t('path.localBody'), slot: t('path.localSlot') },
      pro: { e: '🏪', t: t('path.proT'), body: t('path.proBody'), slot: t('path.proSlot') },
      replace: { e: '♻️', t: t('path.replaceT'), body: t('path.replaceBody'), slot: t('path.replaceSlot') },
      reklamation: { e: '📮', t: t('path.reklamationT'), body: t('path.reklamationBody'), slot: t('path.reklamationSlot') },
      community: { e: '💬', t: t('path.communityT'), body: t('path.communityBody'), slot: t('path.communitySlot') },
    };
    var info = map[props.path] || map.pro;
    var pathChildren = [
      h('div', { class: 'rk-result-emoji', style: { marginTop: '6px' } }, info.e),
      h('h2', { class: 'rk-result-q', style: { textAlign: 'left' } }, info.t),
      h('p', { class: 'rk-q-hint' }, info.body),
      Slot({ label: info.slot, h: 150 }),
      h('button', { class: 'rk-share-line', onClick: props.onProtocol }, DocIcon(), t('result.winShare'))
    ];
    if (props.lotseOptionen && props.lotseOptionen.length) {
      pathChildren.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }
    return Screen({
      bar: AppBar({ left: h('span', {}), title: device ? deviceTitle(device) : h('span', {}), right: docBtn(props.onProtocol) }),
      footer: GhostButton({ full: true, onClick: props.onRestart, children: t('common.startseite') }),
      children: pathChildren
    });
  }

  /* ===================== UNIVERSELLE TRIAGE (PROJ-26) =====================
     5 gerätunabhängige Fragen, gleiche Mechanik + Freitext wie PROJ-2. */
  function UnivTriageScreen(props) {
    var device = props.device;
    var fragen = props.fragen || [];
    var index = props.index;
    var n = fragen.length;
    if (!n) {
      return Screen({
        bar: AppBar({
          left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
          title: device ? deviceTitle(device) : h('span', {}, t('common.aufnahme')),
          right: docBtn(props.onProtocol)
        }),
        footer: GhostButton({ full: true, onClick: props.onSkip, children: t('common.ueberspringenArrow') }),
        children: [
          h('div', { class: 'rk-eyebrow' }, t('common.aufnahme')),
          h('p', { class: 'rk-q-hint' }, t('univ.loading'))
        ]
      });
    }
    var q = fragen[index];
    var ftVal = props.freitext || '';
    function charcount(v) {
      return h('div', { class: 'rk-charcount' + (v.length >= 500 ? ' rk-charcount-over' : ''), id: 'rk-univ-charcount-' + index },
        v.length + '/500');
    }
    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: device ? deviceTitle(device) : h('span', {}, t('common.aufnahme')),
        right: docBtn(props.onProtocol)
      }),
      footer: h('div', { class: 'rk-triage-foot' }, t('univ.foot', { i: index + 1, n: n })),
      children: [
        ProgressDots({ n: n, i: index }),
        h('div', { class: 'rk-eyebrow' }, t('univ.eyebrow')),
        h('div', { class: 'rk-univ' },
          h('h2', { class: 'rk-q rk-univ-q' }, q.q),
          q.hint ? h('p', { class: 'rk-q-hint' }, q.hint) : null,
          h('div', { class: 'rk-answers' }, (q.options || []).map(function (o) {
            return AnswerChip({ onClick: function () { props.onAnswer(q.q, o.a, o.tag); }, children: o.a });
          })),
          h('div', { class: 'rk-triage-text-wrap' },
            h('textarea', {
              class: 'rk-triage-text', maxlength: '500', rows: '2',
              placeholder: t('triage.textPlaceholder'),
              onInput: function (e) {
                var v = e.target.value;
                props.setFreitext(index, v);
                var c = document.getElementById('rk-univ-charcount-' + index);
                if (c) { c.textContent = v.length + '/500'; c.className = 'rk-charcount' + (v.length >= 500 ? ' rk-charcount-over' : ''); }
              }
            }, ftVal),
            charcount(ftVal)
          ),
          h('button', { class: 'rk-freeanswer', onClick: function () { props.onAnswer(q.q, t('triage.freiTag'), t('triage.freiTag')); } },
            h('span', {}, t('triage.frei')),
            h('span', { class: 'rk-input-mic' }, '🎙️')
          )
        )
      ]
    });
  }

  /* ---- gemeinsamer Quellen-/Demo-Hinweis für kuratierte Service-Daten ---- */
  function curatedTrust(item) {
    var quelle = (item && item.quelle) || t('svc.curatedDefault');
    return TrustBadge('mittel', quelle, t('svc.curatedReason', { quelle: quelle }));
  }
  function svcEmpty(hinweis) {
    return h('div', { class: 'rk-svc-empty' }, hinweis || t('svc.empty'));
  }
  function locField(props) {
    return h('div', {},
      h('label', { class: 'rk-loc-label', for: 'rk-loc-input' }, t('svc.locLabel')),
      h('div', { class: 'rk-loc-row', style: { display: 'flex', gap: 'var(--gap)' } },
        h('input', {
          class: 'rk-loc-input', id: 'rk-loc-input', type: 'text',
          placeholder: t('svc.locPlaceholder'),
          value: props.ort || '',
          onInput: function (e) { props.setOrt(e.target.value); },
          onKeydown: function (e) { if (e.key === 'Enter') { e.preventDefault(); props.onSearch(); } }
        }),
        h('button', { class: 'rk-svc-select', onClick: props.onSearch }, t('svc.suchen'))
      )
    );
  }

  /* ===================== VERMITTLUNG (PROJ-11) ===================== */
  function VermittlungScreen(props) {
    var device = props.device;
    var data = props.anbieter;
    var selected = (props.vermittlung && props.vermittlung.selected) || '';
    var typLabel = { repaircafe: t('verm.typRepaircafe'), werkstatt: t('verm.typWerkstatt'), profi: t('verm.typProfi') };
    var typOrder = ['repaircafe', 'werkstatt', 'profi'];

    var body;
    if (data == null) {
      body = h('p', { class: 'rk-q-hint' }, t('verm.loading'));
    } else {
      var items = data.items || [];
      if (!items.length) {
        body = svcEmpty(data.hinweis);
      } else {
        var groups = typOrder.map(function (typ) {
          var inGroup = items.filter(function (it) { return it.typ === typ; });
          if (!inGroup.length) return null;
          return h('div', { class: 'rk-svc' },
            h('div', { class: 'rk-svc-head rk-typ-' + typ }, typLabel[typ] || typ),
            h('div', { class: 'rk-svc-list' }, inGroup.map(function (it) {
              var isFree = it.typ === 'repaircafe';
              var sel = selected === it.id;
              return h('div', { class: 'rk-svc-card rk-typ-' + typ + (sel ? ' rk-svc-card-sel' : '') },
                h('div', { class: 'rk-svc-name' }, it.name,
                  h('span', { class: 'rk-svc-typ rk-typ-' + typ }, typLabel[it.typ] || it.typ),
                  it.kuratiert ? h('span', { class: 'rk-svc-badge' }, t('verm.demo')) : null),
                h('div', { class: 'rk-svc-meta' },
                  (it.adresse ? it.adresse + ', ' : '') + (it.plz ? it.plz + ' ' : '') + (it.ort || '') +
                  (it.entfernung ? ' · ' + it.entfernung : '')),
                it.spezialisierung ? h('div', { class: 'rk-svc-meta' }, t('verm.schwerpunkt') + it.spezialisierung) : null,
                it.oeffnungszeiten ? h('div', { class: 'rk-svc-meta' }, '🕑 ' + it.oeffnungszeiten) : null,
                it.kontakt ? h('div', { class: 'rk-svc-meta' }, '☎ ' + it.kontakt) : null,
                isFree
                  ? h('div', { class: 'rk-svc-cost rk-svc-free' }, t('verm.free') + (it.kostenhinweis || t('verm.freeDefault')))
                  : h('div', { class: 'rk-svc-cost' }, '💶 ' + (it.kostenhinweis || t('verm.costDefault'))),
                h('div', { class: 'rk-svc-src' }, curatedTrust(it)),
                h('button', {
                  class: 'rk-svc-select' + (sel ? ' rk-answer-on' : ''),
                  onClick: function () { props.onSelect(it.id); }
                }, sel ? t('verm.selected') : t('verm.select'))
              );
            }))
          );
        });
        body = h('div', {}, groups);
      }
    }

    var vermChildren = [
      h('div', { class: 'rk-eyebrow' }, t('verm.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight' }, t('verm.title')),
      h('p', { class: 'rk-svc-intro' }, t('verm.intro')),
      locField(props),
      body,
      GhostButton({ full: true, onClick: props.onRestart, children: t('common.startseite') })
    ];
    if (props.lotseOptionen && props.lotseOptionen.length) {
      vermChildren.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: GhostButton({ full: true, onClick: props.onProtocol, children: t('common.protokollTeilen') }),
      children: vermChildren
    });
  }

  /* ===================== ENTSORGUNG (PROJ-12) ===================== */
  function EntsorgungScreen(props) {
    var device = props.device;
    var data = props.entsorgung;
    var selected = (props.entsorgungSel && props.entsorgungSel.selected) || '';
    var artLabel = { wertstoffhof: t('ents.artWertstoffhof'), ruecknahme: t('ents.artRuecknahme'), sammelstelle: t('ents.artSammelstelle') };

    var body;
    if (data == null) {
      body = h('p', { class: 'rk-q-hint' }, t('ents.loading'));
    } else {
      var items = data.items || [];
      if (!items.length) {
        body = svcEmpty(data.hinweis || t('ents.emptyDefault'));
      } else {
        body = h('div', { class: 'rk-svc-list' }, items.map(function (it) {
          var sel = selected === it.id;
          return h('div', { class: 'rk-disp' + (sel ? ' rk-svc-card-sel' : '') },
            h('div', { class: 'rk-svc-name' }, it.name || (artLabel[it.art] || it.art),
              h('span', { class: 'rk-disp-art' }, artLabel[it.art] || it.art)),
            it.adresse ? h('div', { class: 'rk-svc-meta' }, '📍 ' + it.adresse + (it.ort ? ', ' + it.ort : '')) : null,
            it.annahmezeiten ? h('div', { class: 'rk-disp-zeiten' }, '🕑 ' + it.annahmezeiten) : null,
            it.rohstoff ? h('div', { class: 'rk-disp-rohstoff' }, t('ents.rohstoffe') + it.rohstoff) : null,
            it.hinweise ? h('div', { class: 'rk-svc-meta' }, it.hinweise) : null,
            h('div', { class: 'rk-disp-kosten' }, '💶 ' + (it.kosten || t('ents.kostenDefault'))),
            h('div', { class: 'rk-svc-src' }, curatedTrust(it)),
            h('button', {
              class: 'rk-svc-select' + (sel ? ' rk-answer-on' : ''),
              onClick: function () { props.onSelect(it.id); }
            }, sel ? t('ents.selected') : t('ents.select'))
          );
        }));
      }
    }

    var entsChildren = [
      h('div', { class: 'rk-eyebrow' }, t('ents.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight' }, t('ents.title')),
      h('p', { class: 'rk-svc-intro' }, t('ents.intro')),
      locField(props),
      body,
      GhostButton({ full: true, onClick: props.onRestart, children: t('common.startseite') })
    ];
    if (props.lotseOptionen && props.lotseOptionen.length) {
      entsChildren.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: GhostButton({ full: true, onClick: props.onProtocol, children: t('common.protokollTeilen') }),
      children: entsChildren
    });
  }

  /* ===================== PRODUKTSUCHE / ALTERNATIVEN (PROJ-13) ===================== */
  function ProduktsucheScreen(props) {
    var device = props.device;
    var data = props.alternativen;
    var selected = (props.produktsuche && props.produktsuche.selected) || '';

    function setupDots(n) {
      n = Math.max(0, Math.min(3, n || 0));
      var s = '';
      for (var i = 0; i < 3; i++) s += i < n ? '●' : '○';
      return s;
    }

    var body;
    if (data == null) {
      body = h('p', { class: 'rk-q-hint' }, t('prod.loading'));
    } else {
      var items = data.items || [];
      if (!items.length) {
        body = svcEmpty(data.hinweis || t('prod.emptyDefault'));
      } else {
        body = h('div', { class: 'rk-alt' }, items.map(function (it) {
          var sel = selected === it.id;
          var v = it.vergleich || {};
          return h('div', { class: 'rk-alt-card' + (sel ? ' rk-svc-card-sel' : '') },
            h('div', { class: 'rk-alt-modell' }, it.modell,
              it.preis ? h('span', { class: 'rk-svc-cost' }, '💶 ' + it.preis) : null),
            h('div', { class: 'rk-alt-spec' },
              (it.ausstattung ? it.ausstattung : '') +
              (it.energieklasse ? t('prod.energieklasse') + it.energieklasse : '') +
              (it.lieferzeit ? ' · ' + it.lieferzeit : '')),
            h('div', { class: 'rk-alt-vergleich' },
              h('div', { class: 'rk-compare-row' }, h('span', { class: 'rk-compare-k' }, t('compare.geld')), h('span', {}, v.geld || '—')),
              h('div', { class: 'rk-compare-row' }, h('span', { class: 'rk-compare-k' }, t('compare.zeit')), h('span', {}, v.zeit || '—')),
              h('div', { class: 'rk-compare-row' }, h('span', { class: 'rk-compare-k' }, t('compare.umwelt')), h('span', {}, v.umwelt || '—'))
            ),
            h('div', { class: 'rk-alt-setup' }, t('prod.setup') + setupDots(it.einrichtung)),
            h('div', { class: 'rk-svc-src' }, curatedTrust(it)),
            h('button', {
              class: 'rk-svc-select' + (sel ? ' rk-answer-on' : ''),
              onClick: function () { props.onSelect(it.id); }
            }, sel ? t('prod.selected') : t('prod.select'))
          );
        }));
        if (data.breakEven) {
          body = h('div', {}, body, h('div', { class: 'rk-alt-breakeven' }, '📊 ' + data.breakEven));
        }
      }
    }

    var prodChildren = [
      h('div', { class: 'rk-eyebrow' }, t('prod.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight' }, t('prod.title')),
      h('p', { class: 'rk-svc-intro' }, t('prod.intro')),
      body,
      GhostButton({ full: true, onClick: props.onRestart, children: t('common.startseite') })
    ];
    if (props.lotseOptionen && props.lotseOptionen.length) {
      prodChildren.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: GhostButton({ full: true, onClick: props.onProtocol, children: t('common.protokollTeilen') }),
      children: prodChildren
    });
  }

  /* ===================== BESCHAFFUNG / ERSATZTEILE (PROJ-14, D8) ===================== */
  function BeschaffungScreen(props) {
    var device = props.device;
    var data = props.ersatzteile;
    var kept = (props.beschaffung && props.beschaffung.parts) || [];

    var body;
    if (data == null) {
      body = h('p', { class: 'rk-q-hint' }, t('besch.loading'));
    } else {
      var items = data.items || [];
      if (!items.length) {
        body = svcEmpty(data.hinweis || t('besch.emptyDefault'));
      } else {
        body = h('div', {}, items.map(function (it) {
          var isKept = kept.indexOf(it.id) >= 0;
          var oos = !it.verfuegbarkeit || /nicht lieferbar|nicht verfügbar|ausverkauft/i.test('' + it.verfuegbarkeit);
          var bo = it.bestelloption || {};
          return h('div', { class: 'rk-parts-item' + (isKept ? ' rk-svc-card-sel' : '') },
            h('div', { class: 'rk-svc-name' }, it.teil,
              h('span', { class: 'rk-parts-price' }, '💶 ' + (it.preis || '—'))),
            it.passendFuer ? h('div', { class: 'rk-svc-meta' }, t('besch.passendFuer') + it.passendFuer) : null,
            oos
              ? h('div', { class: 'rk-parts-oos' }, '⚠️ ' + (it.verfuegbarkeit || t('besch.oosDefault')) +
                (it.alternativHinweis ? ' — ' + it.alternativHinweis : (it.hersteller ? t('besch.herstellerAnfrage') + it.hersteller : '')))
              : h('div', { class: 'rk-parts-stock' }, '✅ ' + it.verfuegbarkeit + (it.versand ? ' · ' + it.versand : '')),
            h('div', { class: 'rk-svc-src' }, curatedTrust(it)),
            // Bestelloption NACHGELAGERT, klar als Affiliate gekennzeichnet, nie vorausgewählt (D8)
            (bo.verfuegbar)
              ? h('div', { class: 'rk-order-opt' },
                h('span', { class: 'rk-affiliate' }, t('besch.affiliate')),
                h('span', { class: 'rk-svc-meta' }, (bo.partner ? bo.partner : t('besch.partnerDefault'))),
                h('div', { class: 'rk-order-disclaimer' }, bo.hinweis || t('besch.orderDisclaimer')))
              : null,
            h('button', {
              class: 'rk-parts-keep' + (isKept ? ' rk-answer-on' : ''),
              onClick: function () { props.onKeep(it.id); }
            }, isKept ? t('besch.kept') : t('besch.keep'))
          );
        }));
      }
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('common.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: GhostButton({ full: true, onClick: props.onBack, children: t('besch.backToRepair') }),
      children: [
        h('div', { class: 'rk-parts' },
          h('div', { class: 'rk-parts-head' }, t('besch.head')),
          h('p', { class: 'rk-svc-intro' }, t('besch.intro')),
          body,
          GhostButton({ full: true, onClick: props.onProtocol, children: t('common.protokollTeilen') })
        )
      ]
    });
  }

  /* ===================== PROTOKOLL (Steckbrief + Export PROJ-1/2/3/4/7/8/10) ===================== */
  function ownerText(ownership) {
    if (!ownership || ownership.isOwner == null) return t('common.nichtAngegeben');
    if (ownership.isOwner === 'yes') return t('proto.ownGehoertMir');
    if (ownership.isOwner === 'unknown') return t('proto.ownZuKlaeren');
    // no
    var who = (ownership.owner && ownership.owner.trim()) ? ownership.owner.trim() : t('common.nichtAngegeben');
    return t('proto.ownGehoertNicht', { who: who });
  }
  function costText(ownership) {
    if (!ownership) return t('common.nichtAngegeben');
    return (ownership.costBearer && ownership.costBearer.trim()) ? ownership.costBearer.trim() : t('common.nichtAngegeben');
  }

  function ProtocolContent(props) {
    var device = props.device, answers = props.answers || [];
    var why = props.why;
    var ownership = props.ownership || {};
    var skill = props.skill;
    var warranty = props.warranty || {};
    var diagnosis = props.diagnosis || null;
    var safetyConfirms = props.safetyConfirms || {};
    var confirmKeys = Object.keys(safetyConfirms);
    var summary = device.lights.map(function (l) { return l.icon + ' ' + levelMeta(l.level).face; }).join('   ');

    // Stufe-2 Auswahlen (PROJ-11/12/13/14) — falls gesetzt, mit Labels aus den geladenen Listen auflösen
    function resolve(list, id) {
      if (!id || !list || !list.items) return null;
      var hit = list.items.filter(function (x) { return x.id === id; })[0];
      return hit || { id: id };
    }
    var vermittlung = props.vermittlung || {};
    var entsorgungSel = props.entsorgungSel || {};
    var produktsuche = props.produktsuche || {};
    var beschaffung = props.beschaffung || {};
    var trust = props.trust || null;
    var pickedAnbieter = resolve(props.anbieter, vermittlung.selected);
    var pickedEntsorgung = resolve(props.entsorgung, entsorgungSel.selected);
    var pickedAlt = resolve(props.alternativen, produktsuche.selected);
    var keptParts = (beschaffung.parts || []).map(function (pid) {
      return resolve(props.ersatzteile, pid) || { id: pid };
    });
    function svcLine(item, fallbackLabel) {
      if (!item) return null;
      var label = item.name || item.modell || item.teil || fallbackLabel || item.id;
      return h('div', { class: 'rk-proto-val' }, label +
        (item.quelle ? t('proto.quelleLabel') + item.quelle + (item.kuratiert ? t('proto.kuratierteDemo') : '') : ''));
    }
    var hasStufe2 = pickedAnbieter || pickedEntsorgung || pickedAlt || keptParts.length;

    var warrantyLine = t('proto.nichtErfasst');
    if (warranty.asked || warranty.purchaseAge) {
      warrantyLine = t('proto.kauf') + (warranty.purchaseAge || t('foerder.unbekannt')) +
        (warranty.choice ? t('proto.wahl') + (warranty.choice === 'reklamation' ? t('proto.wahlReklamation') : t('proto.wahlSelbst')) : '');
    }

    return h('div', { class: 'rk-proto' },
      h('div', { class: 'rk-proto-head' },
        h('span', { class: 'rk-proto-e' }, device.emoji),
        h('div', {},
          h('div', { class: 'rk-proto-name' }, device.name),
          h('div', { class: 'rk-proto-detail' }, device.detail)
        )
      ),
      diagnosis && diagnosis.status === 'unclear'
        ? h('div', { class: 'rk-aiwarn rk-aiwarn-strong' }, t('proto.unclearWarn'))
        : null,
      h('div', { class: 'rk-proto-sec' }, t('proto.symptom')),
      h('div', { class: 'rk-proto-val' }, device.blurb),
      h('div', { class: 'rk-proto-sec' }, t('proto.tested')),
      h('div', { class: 'rk-proto-tags' },
        answers.length
          ? answers.map(function (a) { return h('span', { class: 'rk-proto-tag' }, a.tag || a.a); })
          : h('span', { class: 'rk-proto-tag rk-proto-tag-muted' }, t('proto.nothingYet'))
      ),
      // PROJ-2: Freitexte je Frage
      answers.filter(function (a) { return a && a.freitext; }).length
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.ownWords')),
          answers.map(function (a) {
            return a && a.freitext
              ? h('div', { class: 'rk-proto-val' }, h('b', {}, '„' + a.q + "“ "), '— ' + a.freitext)
              : null;
          })
        ) : null,
      h('div', { class: 'rk-proto-sec' }, t('proto.causeAmpel')),
      h('div', { class: 'rk-proto-val' }, device.verdictTitle),
      h('div', { class: 'rk-proto-ampel' }, summary),
      h('button', { class: 'rk-proto-why', onClick: function () { props.setWhy(!why); } },
        (why ? '▾' : '▸') + t('proto.why')),
      why ? h('div', { class: 'rk-proto-reason' },
        h('p', {}, device.verdictBody),
        h('p', { class: 'rk-sheet-fine' }, t('proto.whyQuelle') + device.confidence.source + t('proto.whySicherheit') + device.confidence.level + t('proto.whyKiIrrt'))
      ) : null,
      // PROJ-3 / PROJ-7
      h('div', { class: 'rk-proto-sec' }, t('proto.koennenGarantie')),
      h('div', { class: 'rk-proto-val' }, t('proto.selbsteinschaetzung') + (skill || t('common.nichtAngegeben'))),
      h('div', { class: 'rk-proto-val' }, t('proto.gewaehrleistung') + warrantyLine),
      // PROJ-1: Eigentum dynamisch
      h('div', { class: 'rk-proto-owner' }, t('proto.geraetLabel'), h('b', {}, ownerText(ownership)), t('proto.kostenLabel'), h('b', {}, costText(ownership))),
      // FIX A — PROJ-1 AC8 (D14): Rücksprache-Hinweis bei fremdem Gerät
      ownership.isOwner === 'no'
        ? h('div', { class: 'rk-aiwarn rk-aiwarn-strong' }, t('proto.fremdWarn'))
        : null,
      // FIX D — PROJ-8 AC8: gegebene Sicherheits-Bestätigungen sichtbar machen
      confirmKeys.length
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.sicherheitsBestaetigungen')),
          confirmKeys.map(function (k) {
            var c = safetyConfirms[k] || {};
            return h('div', { class: 'rk-proto-val' },
              t('proto.schritt') + (parseInt(k, 10) + 1) + t('proto.volljaehrig') + (c.adult === 'yes' ? t('proto.ja') : t('proto.nein')) +
              t('proto.zugetraut') + (c.confident === 'yes' ? t('proto.ja') : t('proto.nein')));
          })
        ) : null,
      // PROJ-25: durchgängige Vertrauens-/Quellenzeile des Vorgangs
      trust && (trust.level || trust.source)
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.vertrauenQuelle')),
          TrustBadge(trust.level || 'mittel', trust.source || (device.confidence && device.confidence.source) || 'kuratiert', trust.reason || ''))
        : null,
      // PROJ-11/12/13/14: gewählte Service-Wege (nur falls gesetzt)
      hasStufe2
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.wegeBeschaffung')),
          pickedAnbieter ? h('div', {}, h('div', { class: 'rk-proto-val' }, h('b', {}, t('proto.anbieterLabel'))), svcLine(pickedAnbieter)) : null,
          pickedEntsorgung ? h('div', {}, h('div', { class: 'rk-proto-val' }, h('b', {}, t('proto.entsorgungLabel'))), svcLine(pickedEntsorgung)) : null,
          pickedAlt ? h('div', {}, h('div', { class: 'rk-proto-val' }, h('b', {}, t('proto.altLabel'))), svcLine(pickedAlt)) : null,
          keptParts.length
            ? h('div', {},
              h('div', { class: 'rk-proto-val' }, h('b', {}, t('proto.ersatzteileLabel'))),
              keptParts.map(function (p) { return svcLine(p); }),
              h('div', { class: 'rk-foerder-disclaimer' }, t('proto.affiliateDisclaimer')))
            : null
        ) : null,
      // PROJ-22: Consent-Status
      (props.consent && props.consent.status !== 'offen')
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.einwilligung')),
          h('div', { class: 'rk-proto-val' },
            (props.consent.status === 'erteilt' ? '✅ ' : props.consent.status === 'abgelehnt' ? '❌ ' : '↩️ ') +
            (t('consent.status.' + props.consent.status) || props.consent.status || '') +
            (props.consent.zeitpunkt ? ' · ' + props.consent.zeitpunkt.substring(0, 19).replace('T', ' ') : '')
          ),
          (props.consent.status === 'erteilt' && props.onConsentRevoke)
            ? h('button', { class: 'rk-consent-revoke', onClick: props.onConsentRevoke }, t('consent.widerrufen'))
            : null
        ) : null,
      // PROJ-19: Rückruf
      (props.rueckruf && props.rueckruf.hit)
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.rueckruf')),
          h('div', { class: 'rk-proto-val' }, (props.rueckruf.art || 'rueckruf') + ': ' + (props.rueckruf.grund || '')),
          props.rueckruf.quelle ? h('div', { class: 'rk-proto-val' }, t('proto.whyQuelle') + props.rueckruf.quelle) : null,
          props.rueckruf.stand ? h('div', { class: 'rk-proto-val' }, t('foerder.stand') + props.rueckruf.stand) : null
        ) : null,
      // PROJ-20: Datenlöschung
      (props.abgabe === 'dritte')
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.datenloeschung')),
          h('div', { class: 'rk-proto-val' },
            '💾 ' + t('wipe.backup') + ': ' + ((props.datenloeschung && props.datenloeschung.backup) ? '✓' : '–') +
            ' · 🗑️ ' + t('wipe.loeschen') + ': ' + ((props.datenloeschung && props.datenloeschung.loeschen) ? '✓' : '–') +
            ' · 🔓 ' + t('wipe.abmelden') + ': ' + ((props.datenloeschung && props.datenloeschung.abmelden) ? '✓' : '–') +
            ((props.datenloeschung && props.datenloeschung.bewusstUebersprungen) ? t('proto.bewusstUebersprungen') : '')
          )
        ) : null,
      // PROJ-21: Mehrfachdefekte
      (props.defekte && props.defekte.length >= 2)
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.mehrfachdefekte', { n: props.defekte.length })),
          props.defekte.map(function (d) {
            return h('div', { class: 'rk-proto-val' }, d.name || d.id);
          }),
          props.gesamtFazit
            ? h('div', { class: 'rk-proto-val' },
              t('proto.gesamt') + (props.gesamtFazit.recommend || '') +
              (props.gesamtFazit.knackpunktId ? t('proto.knackpunkt') + props.gesamtFazit.knackpunktId : ''))
            : null
        ) : null,
      // PROJ-23: Schwungrad
      (props.schwungrad && props.schwungrad.beigetragen)
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.schwungrad')),
          h('div', { class: 'rk-proto-val' }, t('proto.beitragId') + (props.schwungrad.beitragId || '—')),
          props.schwungrad.ausgeschlossen && props.schwungrad.ausgeschlossen.length
            ? h('div', { class: 'rk-proto-val' }, t('proto.ausgeschlossen') + props.schwungrad.ausgeschlossen.join(', '))
            : null
        ) : null,
      // PROJ-27: Medien-Anhänge
      (props.medien && props.medien.length)
        ? h('div', {},
          h('div', { class: 'rk-proto-sec' }, t('proto.medien', { n: props.medien.length })),
          props.medien.map(function (m) {
            return h('div', { class: 'rk-proto-val' }, (m.art || '?') + ' · ' + (m.ref || m.id || ''));
          })
        ) : null,
      // PROJ-10: echte Export-Buttons
      h('div', { class: 'rk-proto-share' },
        h('button', { class: 'rk-share-btn', onClick: props.onExportText }, h('span', {}, '💬'), t('proto.exportText')),
        h('button', { class: 'rk-share-btn', onClick: props.onExportPdf }, h('span', {}, '📄'), t('proto.exportPdf')),
        h('button', { class: 'rk-share-btn', onClick: props.onExportLink }, h('span', {}, '🔗'), t('proto.exportLink'))
      ),
      props.linkUrl ? h('div', { class: 'rk-link-box' },
        h('div', { class: 'rk-link-url' }, props.linkUrl),
        h('button', { class: 'rk-share-btn', onClick: props.onCopyLink }, h('span', {}, '📋'), t('proto.exportKopieren')),
        h('div', { class: 'rk-link-note' }, t('proto.linkNote'))
      ) : null
    );
  }

  /* ===================== STUFE-3 HELPER ===================== */

  /* ---- Steuerleiste (PROJ-18) ---- */
  function SteerBar(props) {
    var opts = props.lotseOptionen || [];
    if (!opts.length && !props.showDefault) return null;
    // Default-Optionen falls keine geladen
    var items = opts.length ? opts : [
      { label: t('steer.profi'), ereignis: 'wechsel', ziel: 'vermittlung' },
      { label: t('steer.entsorgen'), ereignis: 'wechsel', ziel: 'entsorgung' },
      { label: t('steer.abbrechen'), ereignis: 'abbruch', ziel: '' },
    ];
    return h('div', { class: 'rk-steer' }, items.map(function (opt) {
      var isPrimary = opt.ereignis === 'weiter';
      var isAbort = opt.ereignis === 'abbruch';
      return h('button', {
        class: 'rk-steer-btn' + (isPrimary ? ' rk-steer-primary' : isAbort ? ' rk-steer-abort' : ' rk-steer-secondary'),
        onClick: function () { if (props.onLotseAktion) props.onLotseAktion(opt.ereignis, opt.ziel); },
      }, opt.label);
    }));
  }

  /* ---- Consent-Gate-Overlay (PROJ-22) ---- */
  function ConsentGateOverlay(props) {
    if (!props.show) return null;
    return h('div', { class: 'rk-consent' },
      h('div', { class: 'rk-consent-head' }, t('consent.titel')),
      h('div', { class: 'rk-consent-body' }, t('consent.body')),
      h('div', { class: 'rk-consent-train' }, t('consent.trainingshinweis')),
      h('div', { class: 'rk-consent-ref' }, t('consent.verweis')),
      h('div', { class: 'rk-consent-btns' },
        h('button', { class: 'rk-consent-yes', onClick: props.onErteilen }, t('consent.erteilen')),
        h('button', { class: 'rk-consent-no', onClick: props.onAblehnen }, t('consent.ablehnen'))
      )
    );
  }

  /* ---- Consent-Widerruf-Control (PROJ-22) ---- */
  function ConsentStatus(props) {
    var consent = props.consent || {};
    if (!consent.status || consent.status === 'offen') return null;
    var label = t('consent.status.' + consent.status) || consent.status;
    return h('div', { class: 'rk-consent-status' },
      h('span', {}, label + (consent.zeitpunkt ? ' (' + consent.zeitpunkt.substring(0, 10) + ')' : '')),
      (consent.status === 'erteilt')
        ? h('button', { class: 'rk-consent-revoke', onClick: props.onRevoke }, t('consent.widerrufen'))
        : null
    );
  }

  /* ---- Only-DE badge (PROJ-24) ---- */
  function OnlyDeBadge(lang, nurDeutsch) {
    if (lang !== 'en' || !nurDeutsch) return null;
    return h('span', { class: 'rk-onlyde' }, t('onlyde'));
  }

  /* ===================== RECALL SCREEN (PROJ-19) ===================== */
  function RecallScreen(props) {
    var device = props.device;
    var r = props.rueckruf || {};
    var art = r.art || 'rueckruf';
    var artCls = art === 'sicherheitsmangel' ? 'rk-recall-sicherheitsmangel' : 'rk-recall-rueckruf';
    var titel = t('recall.titel.' + art);

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('nav.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: h('div', { class: 'rk-recall-continue' },
        h('button', { class: 'rk-ghost rk-full', onClick: props.onContinue }, t('recall.weiter'))
      ),
      children: [
        h('div', { class: 'rk-recall ' + artCls },
          h('div', { class: 'rk-recall-badge' }, titel),
          h('p', { class: 'rk-recall-grund' },
            h('b', {}, t('recall.grund.label')), ' ', r.grund || ''),
          r.quelle ? h('p', { class: 'rk-recall-quelle' },
            h('b', {}, t('recall.quelle.label')), ' ', r.quelle) : null,
          (r.stand || r.gueltigBis) ? h('p', { class: 'rk-recall-stand' },
            h('b', {}, t('recall.stand.label')), ' ',
            (r.stand || '') + (r.gueltigBis ? ' / ' + r.gueltigBis : '')) : null,
          r.vorgehen ? h('p', { class: 'rk-recall-vorgehen' },
            h('b', {}, t('recall.vorgehen.label')), ' ', r.vorgehen) : null,
          h('div', { class: 'rk-aiwarn rk-aiwarn-strong' }, t('recall.hinweis')),
          // modellUnsicher: kein harter Treffer
          r.modellUnsicher
            ? h('div', { class: 'rk-recall-unsure' }, t('recall.unsicher'))
            : null
        )
      ]
    });
  }

  /* ===================== DIAG SCREEN (PROJ-17 — kuratierte Diagnose-Schleife) ===================== */
  function DiagScreen(props) {
    var device = props.device;
    var fz = props.fehlerzustand || {};
    var kandidaten = fz.kandidaten || [];
    var gewaehlt = fz.gewaehlt || '';
    var abgrenzung = fz.abgrenzung || { offen: [], beantwortet: {} };
    var beantwortet = abgrenzung.beantwortet || {};
    var offeneFragen = abgrenzung.offen || [];

    // Kandidaten nach Konfidenz sortieren
    var sorted = kandidaten.slice().sort(function (a, b) {
      var rank = { hoch: 0, mittel: 1, niedrig: 2 };
      return (rank[a.konfidenz] || 1) - (rank[b.konfidenz] || 1);
    });

    // Kandidat ausgeblendet durch Abgrenzungsantworten?
    function isOut(kand) {
      // einfache Heuristik: wenn ein Kandidat-Tag einer beantworteten Frage widerspricht
      return false; // erweiterbar
    }

    function konfidenzLabel(k) {
      return t('diag.konfidenz.' + (k || 'mittel'));
    }
    function herkunftLabel(h_) {
      if (h_ === 'kuratiert') return t('diag.herkunft.kuratiert');
      return t('diag.herkunft.ki');
    }

    var children = [
      h('div', { class: 'rk-eyebrow' }, t('diag.eyebrow')),
      h('h2', { class: 'rk-q rk-q-tight rk-diag-head' }, t('diag.titel')),
    ];

    // Kandidatenliste
    if (sorted.length) {
      children.push(h('div', { class: 'rk-diag' },
        sorted.map(function (k) {
          var sel = gewaehlt === k.id;
          var out = isOut(k);
          var cls = 'rk-diag-cand' + (sel ? ' rk-diag-cand-sel' : '') + (out ? ' rk-diag-cand-out' : '');
          return h('div', { class: cls,
            onClick: function () { if (!out) props.onSelectCandidate(k.id); }
          },
            h('div', { class: 'rk-diag-cause' }, k.ursache || k.id),
            h('div', { class: 'rk-diag-src' },
              h('span', {}, herkunftLabel(k.herkunft)),
              ' · ',
              h('span', {}, konfidenzLabel(k.konfidenz)),
              k.quelle ? h('span', {}, ' · ' + k.quelle) : null
            ),
            TrustBadge(
              k.konfidenz === 'hoch' ? 'hoch' : k.konfidenz === 'niedrig' ? 'niedrig' : 'mittel',
              k.herkunft === 'kuratiert' ? t('diag.herkunft.kuratiert') : t('diag.kiShort'),
              k.quelle || ''
            )
          );
        })
      ));
    }

    // Offene Abgrenzungsfragen
    if (offeneFragen.length > 0) {
      var frage = offeneFragen[0]; // jeweils eine Frage
      var beantw = beantwortet[frage.q];
      children.push(
        h('div', { class: 'rk-diag-frage' },
          h('div', { class: 'rk-eyebrow' }, t('diag.abgrenzung')),
          h('p', { class: 'rk-q' }, frage.q),
          h('div', { class: 'rk-answers' }, (frage.options || []).map(function (o) {
            return AnswerChip({
              active: beantw === o.a,
              onClick: function () { props.onAbgrenzung(frage.q, o.a, o.tag); },
              children: h('span', { class: 'rk-diag-opt' }, o.a)
            });
          }))
        )
      );
    }

    // Weiter/Unklar
    children.push(
      h('div', { class: 'rk-diag' },
        BigButton({
          variant: gewaehlt ? 'primary' : 'soft',
          onClick: props.onWeiter,
          children: t('diag.weiter')
        }),
        h('button', { class: 'rk-ghost rk-full rk-diag-unclear', onClick: props.onUnklar },
          t('diag.unklar'))
      )
    );

    if (props.lotseOptionen && props.lotseOptionen.length) {
      children.push(SteerBar({ lotseOptionen: props.lotseOptionen, onLotseAktion: props.onLotseAktion }));
    }

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('nav.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      children: children
    });
  }

  /* ===================== WIPE SCREEN (PROJ-20 — Datenlöschung) ===================== */
  function WipeScreen(props) {
    var device = props.device;
    var dl = props.datenloeschung || {};
    var allDone = dl.backup && dl.loeschen && dl.abmelden;
    var anyDone = dl.backup || dl.loeschen || dl.abmelden;
    var steps = [
      { field: 'backup', label: t('wipe.backup') },
      { field: 'loeschen', label: t('wipe.loeschen') },
      { field: 'abmelden', label: t('wipe.abmelden') },
    ];

    return Screen({
      bar: AppBar({
        left: IconBtn({ onClick: props.onBack, label: t('nav.zurueck'), children: BackIcon() }),
        title: deviceTitle(device),
        right: docBtn(props.onProtocol)
      }),
      footer: h('div', { class: 'rk-wipe-disp' },
        BigButton({ variant: allDone ? 'primary' : 'soft', onClick: props.onWeiter, children: t('wipe.weiter') }),
        !anyDone
          ? h('button', { class: 'rk-ghost rk-full rk-wipe-skip', onClick: props.onSkip }, t('wipe.skip'))
          : null
      ),
      children: [
        h('div', { class: 'rk-eyebrow' }, t('wipe.eyebrow')),
        h('div', { class: 'rk-wipe' },
          h('h2', { class: 'rk-q rk-q-tight' }, t('wipe.titel')),
          h('p', { class: 'rk-q-hint rk-wipe-head' }, t('wipe.hinweis')),
          h('div', {},
            steps.map(function (step) {
              var on = !!dl[step.field];
              return h('button', {
                class: 'rk-wipe-step' + (on ? ' rk-wipe-on' : ''),
                onClick: function () { props.onToggle(step.field); }
              },
                h('span', { class: 'rk-wipe-check' }, on ? '☑' : '☐'),
                h('span', {}, step.label)
              );
            })
          ),
          (!anyDone)
            ? h('div', { class: 'rk-wipe-warn' }, t('wipe.warn'))
            : null
        )
      ]
    });
  }

  /* ===================== MEDIA CONSENT SHEET (PROJ-27) ===================== */
  function MediaConsentSheet(props) {
    var sheet = h('div', { class: 'rk-sheet' },
      h('div', { class: 'rk-sheet-grip' }),
      h('div', { class: 'rk-sheet-title' }, t('media.consent.titel')),
      h('div', { class: 'rk-sheet-body' },
        h('div', { class: 'rk-media-consent' },
          h('p', { class: 'rk-sheet-note' }, t('media.consent.body')),
          h('div', { class: 'rk-consent-btns' },
            h('button', { class: 'rk-consent-yes', onClick: props.onAccept }, t('media.consent.ok')),
            h('button', { class: 'rk-consent-no', onClick: props.onDecline }, t('media.consent.nein'))
          )
        )
      )
    );
    sheet.addEventListener('click', function (e) { e.stopPropagation(); });
    var scrim = h('div', { class: 'rk-sheet-scrim' }, sheet);
    return scrim;
  }

  /* ===================== MEDIA PANEL (PROJ-27, eingebettet in StartScreen) ===================== */
  function MediaPanel(props) {
    var medienConsent = props.medienConsent;
    var medien = props.medien || [];
    var lang = props.lang || 'de';

    // Barcode-Detect-Support
    var hasBarcodeDetector = typeof window.BarcodeDetector !== 'undefined';
    // Speech-Support
    var hasSpeech = typeof window.webkitSpeechRecognition !== 'undefined' || typeof window.SpeechRecognition !== 'undefined';
    // Camera-Support
    var hasCamera = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

    function capturePhoto() {
      if (!medienConsent) { props.setMediaConsentOpen(true); return; }
      var input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/jpeg,image/png,image/webp';
      input.capture = 'environment';
      input.onchange = function () {
        var file = input.files && input.files[0];
        if (!file) return;
        props.uploadMedium(file, 'foto', null);
      };
      input.click();
    }

    // PROJ-31: Dokument/PDF beifügen (Typenschild, Rechnung, Anleitung).
    function captureDokument() {
      if (!medienConsent) { props.setMediaConsentOpen(true); return; }
      var input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/jpeg,image/png,image/webp,application/pdf';
      input.onchange = function () {
        var file = input.files && input.files[0];
        if (!file) return;
        if (props.uploadDokument) props.uploadDokument(file, null);
        else props.uploadMedium(file, 'dokument', null);
      };
      input.click();
    }

    function captureVoice() {
      if (!medienConsent) { props.setMediaConsentOpen(true); return; }
      var SpeechRec = window.webkitSpeechRecognition || window.SpeechRecognition;
      if (!SpeechRec) {
        toast(t('media.unavail'));
        return;
      }
      var rec = new SpeechRec();
      rec.lang = lang === 'en' ? 'en-US' : 'de-DE';
      rec.interimResults = false;
      rec.maxAlternatives = 1;

      // Live-Indikator
      var indicator = document.getElementById('rk-voice-indicator');
      if (indicator) indicator.style.display = 'block';

      rec.onresult = function (e) {
        var transcript = e.results[0][0].transcript;
        if (indicator) indicator.style.display = 'none';
        // Erkannten Text zur Korrektur anzeigen
        var corrEl = document.getElementById('rk-voice-correct-el');
        if (corrEl) {
          corrEl.style.display = 'block';
          corrEl.querySelector('.rk-voice-correct-text') && (corrEl.querySelector('.rk-voice-correct-text').textContent = transcript);
        }
        // Text in das Diagnose-Feld einfügen
        if (props.onVoiceResult) props.onVoiceResult(transcript);
      };
      rec.onerror = function () {
        if (indicator) indicator.style.display = 'none';
        toast(t('media.unavail'));
      };
      rec.onend = function () {
        if (indicator) indicator.style.display = 'none';
      };
      rec.start();
    }

    function scanBarcode() {
      if (!medienConsent) { props.setMediaConsentOpen(true); return; }
      if (!hasBarcodeDetector) {
        toast(t('media.unavail'));
        return;
      }
      var input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = function () {
        var file = input.files && input.files[0];
        if (!file) return;
        var url = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function () {
          var detector = new window.BarcodeDetector();
          detector.detect(img).then(function (barcodes) {
            URL.revokeObjectURL(url);
            if (barcodes && barcodes.length > 0) {
              var val = barcodes[0].rawValue;
              if (props.onBarcodeResult) props.onBarcodeResult(val);
              toast(t('media.scanResult') + ' ' + val);
            } else {
              toast(t('media.unavail'));
            }
          }).catch(function () {
            URL.revokeObjectURL(url);
            toast(t('media.unavail'));
          });
        };
        img.src = url;
      };
      input.click();
    }

    var btns = [
      h('button', {
        class: 'rk-cap-btn rk-cap-photo' + (!hasCamera && !medienConsent ? ' rk-cap-unavail' : ''),
        onClick: capturePhoto,
        title: t('media.foto'),
      }, '📷'),
      h('button', {
        class: 'rk-cap-btn rk-cap-doc',
        onClick: captureDokument,
        title: t('media.dokument'),
      }, '📄'),
      h('button', {
        class: 'rk-cap-btn rk-cap-voice' + (!hasSpeech ? ' rk-cap-unavail' : ''),
        onClick: captureVoice,
        title: t('media.sprache'),
      }, '🎙️'),
      h('button', {
        class: 'rk-cap-btn rk-cap-scan' + (!hasBarcodeDetector ? ' rk-cap-unavail' : ''),
        onClick: scanBarcode,
        title: t('media.barcode'),
      }, '🔖'),
    ];

    var voiceIndicator = h('div', {
      id: 'rk-voice-indicator', class: 'rk-voice-live',
      style: { display: 'none' }
    }, t('media.voiceLive'));

    var voiceCorrect = h('div', {
      id: 'rk-voice-correct-el', class: 'rk-voice-correct',
      style: { display: 'none' }
    },
      h('span', {}, t('media.voiceCorrect')),
      h('span', { class: 'rk-voice-correct-text' }, '')
    );

    var scanResult = h('div', { class: 'rk-scan-result', style: { display: 'none' } }, '');
    var qualityWarn = h('div', { class: 'rk-quality-warn', style: { display: 'none' } }, t('media.qualityWarn'));

    var toTextBtn = h('button', {
      class: 'rk-to-text rk-ghost',
      onClick: function () { if (props.onToText) props.onToText(); },
    }, t('media.toText'));

    // Medien-Vorschau
    var grid = medien.length
      ? h('div', { class: 'rk-media-grid' },
        medien.map(function (m) {
          var icon = '🎙️';
          if (m.art === 'foto') icon = '📷';
          else if (m.art === 'video') icon = '🎬';
          else if (m.art === 'dokument') icon = (m.mime === 'application/pdf') ? '📄' : '🖼️';
          return h('div', { class: 'rk-media-item' },
            h('div', { class: 'rk-media-thumb' }, h('span', { class: 'rk-media-art' }, icon)),
            h('button', { class: 'rk-media-remove', onClick: function () { if (props.removeMedium) props.removeMedium(m.id); } }, '✕')
          );
        })
      )
      : null;

    return h('div', { class: 'rk-media' },
      h('div', { class: 'rk-cap-row' }, btns),
      voiceIndicator,
      voiceCorrect,
      scanResult,
      qualityWarn,
      grid,
      toTextBtn
    );
  }

  /* ===================== MEHRFACHDEFEKTE GESAMT-FAZIT BLOCK (PROJ-21) ===================== */
  function GesamtFazitBlock(props) {
    var defekte = props.defekte || [];
    var gesamtFazit = props.gesamtFazit;
    if (!defekte.length) return null;

    // Einzelampeln (immer sichtbar bei >=2)
    var ampelListe = defekte.length >= 2
      ? h('div', { class: 'rk-defekt-list' }, defekte.map(function (d, i) {
        var lights = d.lights || [];
        return h('div', { class: 'rk-defekt-rank', 'data-rank': i + 1 },
          h('div', { class: 'rk-diag-cause' }, d.name || d.id),
          h('div', { class: 'rk-ampelcard' }, lights.map(function (l) {
            return LightRow({ light: l, onInfo: function () {} });
          }))
        );
      }))
      : null;

    // Gesamt-Fazit (nur bei >=2)
    var fazitBlock = (defekte.length >= 2 && gesamtFazit)
      ? h('div', { class: 'rk-fazit' },
        h('div', { class: 'rk-fazit-head' }, t('fazit.titel')),
        h('div', { class: 'rk-fazit-reco' }, gesamtFazit.recommend || ''),
        gesamtFazit.knackpunktId
          ? h('div', { class: 'rk-fazit-knack' },
            h('b', {}, t('fazit.knackpunkt')), ' ', gesamtFazit.knackpunktId)
          : null,
        gesamtFazit.begruendung
          ? h('div', { class: 'rk-fazit-why' },
            h('b', {}, t('fazit.begruendung')), ' ', gesamtFazit.begruendung)
          : null
      )
      : null;

    return h('div', {}, ampelListe, fazitBlock);
  }

  /* =====================================================================
     CHAT-FLOW (PROJ-37) — Konversations-Renderer mit eingebetteten Karten
     ===================================================================== */

  var UI = window.UI || {};

  // Fester, unbedingter Vertrauens-Footer (D3/A5) — hängt an JEDER Assistenz-
  // Bubble, unabhängig vom Modell-Output. `strong` verstärkt ihn optisch (bei
  // einer hinweis-Karte mit schwere=kritisch).
  function trustFooter(strong) {
    return h('div', { class: 'rk-chat-trust' + (strong ? ' rk-chat-trust-strong' : '') },
      'ℹ Hinweis: Die KI kann Fehler machen — im Zweifel Fachkraft fragen.');
  }

  // Eine Karte -> passende UI.*-Komponente (Task 8).
  // ctx (optional): { frageInteraktiv, onAntwort, onFrageAttach, pendingMedien }
  function renderKarte(k, ctx) {
    if (!k || !k.typ) return null;
    var d = k.daten || {};
    ctx = ctx || {};
    switch (k.typ) {
      case 'aufnahme':  return UI.Aufnahme ? UI.Aufnahme(d) : null;
      case 'diagnose':  return UI.Diagnose ? UI.Diagnose(d) : null;
      case 'ampel':     return UI.Ampel ? UI.Ampel(d) : null;
      case 'vergleich': return UI.Vergleich ? UI.Vergleich(d) : null;
      case 'schritte':  return UI.Schritte ? UI.Schritte(d) : null;
      case 'hinweis':   return UI.Hinweis ? UI.Hinweis(d) : null;
      case 'anbieter':  return UI.Anbieter ? UI.Anbieter(d) : null;
      case 'ersatzteil':return UI.Ersatzteil ? UI.Ersatzteil(d) : null;
      case 'erfolg':    return UI.Erfolg ? UI.Erfolg(d) : null;
      case 'frage':     return UI.Frage ? UI.Frage(d, {
        interaktiv: !!ctx.frageInteraktiv,
        onAntwort: ctx.onAntwort,
        onAttach: ctx.onFrageAttach,
        pendingMedien: ctx.pendingMedien,
      }) : null;
      default:          return document.createComment('unbekannte karte: ' + k.typ);
    }
  }

  // true, wenn die Karten dieses Turns eine kritische hinweis-Karte enthalten
  // → Vertrauens-Footer verstärken.
  function hatKritischenHinweis(karten) {
    return (karten || []).some(function (k) {
      return k && k.typ === 'hinweis' && k.daten && k.daten.schwere === 'kritisch';
    });
  }

  // Position der jüngsten frage-Karte ermitteln (turnIdx, kartenIdx) — nur sie
  // wird interaktiv gerendert; ältere frage-Karten bleiben read-only.
  function letzteFrageKarte(verlauf) {
    var pos = null;
    (verlauf || []).forEach(function (m, ti) {
      if (m.rolle !== 'assistant') return;
      (m.karten || []).forEach(function (k, ki) {
        if (k && k.typ === 'frage') pos = { ti: ti, ki: ki };
      });
    });
    return pos;
  }

  // Rendert den kompletten Verlauf (User- + Assistenz-Bubbles).
  // opts (optional): { frageAktiv, onAntwort, onFrageAttach, pendingMedien }
  function renderVerlauf(verlauf, opts) {
    opts = opts || {};
    var feed = h('div', { class: 'rk-chat-feed' });
    var letzteFrage = opts.frageAktiv ? letzteFrageKarte(verlauf) : null;
    (verlauf || []).forEach(function (m, ti) {
      if (m.rolle === 'user') {
        var ubody = [h('div', { class: 'rk-bubble-text' }, m.text || '')];
        // PROJ-31: gesendete Anhänge als kleine Marker an der User-Bubble.
        if (m.medien && m.medien.length) {
          ubody.push(h('div', { class: 'rk-bubble-medien' }, m.medien.map(function (md) {
            var ic = md.art === 'foto' ? '📷' : (md.art === 'dokument' ? '📄' : '📎');
            return h('span', { class: 'rk-bubble-medium', title: md.name || '' }, ic + ' ' + (md.name || md.art || ''));
          })));
        }
        feed.appendChild(h('div', { class: 'rk-bubble rk-bubble-user' }, ubody));
        return;
      }
      // Assistenz-Bubble
      var inner = [];
      var karten = m.karten || [];
      // Enthält der Turn eine frage-Karte, IST die Karte die Frage — den Prosa-Text
      // dann nicht zusätzlich rendern (sonst Dopplung: Frage als Text UND als Karte).
      var hatFrage = karten.some(function (k) { return k && k.typ === 'frage'; });
      if (m.text && !hatFrage) inner.push(h('div', { class: 'rk-bubble-text' }, m.text));
      if (karten.length) {
        var kartenWrap = h('div', { class: 'rk-chat-cards' });
        karten.forEach(function (k, ki) {
          var istInteraktiveFrage = !!(letzteFrage && letzteFrage.ti === ti && letzteFrage.ki === ki);
          var el = renderKarte(k, {
            frageInteraktiv: istInteraktiveFrage,
            onAntwort: opts.onAntwort,
            onFrageAttach: opts.onFrageAttach,
            pendingMedien: opts.pendingMedien,
          });
          if (el) kartenWrap.appendChild(el);
        });
        inner.push(kartenWrap);
      }
      // R3: unbedingter Vertrauens-Footer an JEDER Assistenz-Bubble
      inner.push(trustFooter(hatKritischenHinweis(karten)));
      if (m.abgebrochen) {
        inner.push(h('div', { class: 'rk-chat-ended' }, 'Vorgang beendet.'));
      }
      feed.appendChild(h('div', { class: 'rk-bubble rk-bubble-ai' }, inner));
    });
    return feed;
  }

  // Fehler-Bubble (data.code aus /api/chat) — eigene, klar erkennbare Darstellung.
  function renderFehler(data) {
    var code = (data && data.code) || 'error';
    var msg = (data && data.error) || {
      empty: 'Bitte beschreibe kurz, was los ist.',
      no_vorgang: 'Der Vorgang wurde nicht gefunden — bitte neu starten.',
      no_backend: 'Die KI-Diagnose ist gerade nicht erreichbar (kein Backend konfiguriert).',
      ai_error: 'Bei der KI-Anfrage ist etwas schiefgelaufen — bitte erneut versuchen.',
    }[code] || 'Es ist ein Fehler aufgetreten.';
    return h('div', { class: 'rk-bubble rk-bubble-ai rk-bubble-error' },
      h('div', { class: 'rk-bubble-text' }, '⚠️ ' + msg),
      h('div', { class: 'rk-chat-code' }, code)
    );
  }

  // Chat-Bildschirm: scrollbarer Verlauf (Body) + Eingabe-Zeile (Footer).
  function ChatScreen(props) {
    props = props || {};
    var feed = renderVerlauf(props.verlauf || [], {
      // frage interaktiv, solange keine Anfrage läuft und der Vorgang nicht beendet ist
      frageAktiv: !props.pending && !props.abgebrochen && !props.mediaUploading,
      onAntwort: props.onAntwort,
      onFrageAttach: props.onAttach,
      pendingMedien: props.pendingMedien,
    });
    if (props.error) feed.appendChild(renderFehler(props.error));
    if (props.pending) {
      feed.appendChild(h('div', { class: 'rk-bubble rk-bubble-ai rk-bubble-pending' },
        h('div', { class: 'rk-thinking-dots', role: 'status', 'aria-label': 'Antwort wird erstellt' },
          h('i', {}), h('i', {}), h('i', {}))
      ));
    }

    var busy = props.pending || props.mediaUploading;

    var input = h('input', {
      class: 'rk-chat-input', type: 'text',
      placeholder: t('start.placeholder'),
      value: props.draft || '',
      disabled: busy ? true : null,
      onInput: function (e) { if (props.setDraft) props.setDraft(e.target.value); },
      onKeydown: function (e) {
        if (e.key === 'Enter') { e.preventDefault(); if (props.onSend) props.onSend(); }
      },
    });

    // PROJ-31: verstecktes File-Input + Anhang-Button (Foto/Dokument).
    // change-Listener imperativ (h() kennt nur onClick/onInput/onKeydown).
    var fileInput = h('input', {
      type: 'file', accept: 'image/jpeg,image/png,image/webp,application/pdf',
      multiple: true, style: { display: 'none' },
    });
    fileInput.addEventListener('change', function (e) {
      if (props.onAttach) props.onAttach(e.target.files);
      e.target.value = ''; // gleiche Datei erneut wählbar machen
    });
    var attachBtn = h('button', {
      class: 'rk-chat-attach', 'aria-label': t('chat.attach'), title: t('chat.attach'),
      disabled: busy ? true : null,
      onClick: function () { fileInput.click(); },
    }, '📎');

    var sendBtn = h('button', {
      class: 'rk-chat-send', 'aria-label': t('nav.weiter'),
      disabled: busy ? true : null,
      onClick: function () { if (props.onSend) props.onSend(); },
    }, '➤');

    var bar = AppBar({
      left: h('span', { class: 'rk-brand', style: { marginBottom: '0' } },
        h('span', { class: 'rk-brand-mark' }, '🔧')),
      title: h('span', {}, t('start.brand')),
      right: props.abgebrochen
        ? IconBtn({ onClick: props.onRestart, label: t('nav.startseite'), children: h('span', {}, '↺') })
        : h('span', {}),
    });

    // PROJ-31: Chips der noch nicht gesendeten Anhänge (über der Eingabezeile).
    var pendingMedien = props.pendingMedien || [];
    function mediumIcon(art) {
      if (art === 'foto') return '📷';
      if (art === 'dokument') return '📄';
      if (art === 'video') return '🎬';
      return '📎';
    }
    var chips = pendingMedien.length
      ? h('div', { class: 'rk-chat-chips' }, pendingMedien.map(function (m) {
        return h('div', { class: 'rk-chat-chip', title: m.name || '' },
          h('span', { class: 'rk-chat-chip-icon' }, mediumIcon(m.art)),
          h('span', { class: 'rk-chat-chip-name' }, m.name || mediumIcon(m.art)),
          h('button', {
            class: 'rk-chat-chip-x', 'aria-label': t('chat.attachRemove'),
            onClick: function () { if (props.onRemovePending) props.onRemovePending(m.id); },
          }, '✕')
        );
      }))
      : null;

    // Hinweis vor dem Senden + Upload-Status.
    var attachNote = null;
    if (props.mediaUploading) {
      attachNote = h('div', { class: 'rk-chat-attach-note' }, t('chat.attachUploading'));
    } else if (pendingMedien.length) {
      attachNote = h('div', { class: 'rk-chat-attach-note' }, t('chat.attachHint'));
    }

    var inputrow = h('div', { class: 'rk-chat-inputbox' },
      chips,
      attachNote,
      h('div', { class: 'rk-chat-inputrow' }, fileInput, attachBtn, input, sendBtn)
    );

    // PROJ-27 Consent-Sheet vor dem ersten Upload.
    var consentSheet = props.mediaConsentOpen && window.MediaConsentSheet
      ? window.MediaConsentSheet({
        onAccept: props.onMediaConsentAccept,
        onDecline: props.onMediaConsentDecline,
      })
      : null;

    return Screen({
      bar: bar,
      footer: props.abgebrochen
        ? GhostButton({ full: true, onClick: props.onRestart, children: t('nav.startseite') })
        : inputrow,
      children: [
        // Begrüßung, solange noch kein Verlauf existiert
        (!props.verlauf || !props.verlauf.length) && !props.pending
          ? h('div', { class: 'rk-chat-hello' },
            h('h1', { class: 'rk-hero' }, t('start.hero')),
            h('p', { class: 'rk-hero-sub' }, t('start.heroSub')))
          : null,
        feed,
        consentSheet,
      ],
    });
  }

  /* ===================== EXPORT — WINDOW-ASSIGNMENT (alle Screens) ===================== */
  Object.assign(window, {
    renderVerlauf: renderVerlauf, renderKarte: renderKarte, renderFehler: renderFehler,
    ChatScreen: ChatScreen,
    StartScreen: StartScreen, OwnershipScreen: OwnershipScreen, TriageScreen: TriageScreen,
    AmpelScreen: AmpelScreen, UnclearScreen: UnclearScreen, DecisionScreen: DecisionScreen,
    SkillAskScreen: SkillAskScreen, GateScreen: GateScreen, RepairScreen: RepairScreen,
    ResultScreen: ResultScreen, PathScreen: PathScreen, ProtocolContent: ProtocolContent,
    UnivTriageScreen: UnivTriageScreen, VermittlungScreen: VermittlungScreen,
    EntsorgungScreen: EntsorgungScreen, ProduktsucheScreen: ProduktsucheScreen,
    BeschaffungScreen: BeschaffungScreen,
    // Stufe-3
    RecallScreen: RecallScreen, DiagScreen: DiagScreen, WipeScreen: WipeScreen,
    MediaConsentSheet: MediaConsentSheet, MediaPanel: MediaPanel,
    GesamtFazitBlock: GesamtFazitBlock, SteerBar: SteerBar,
    ConsentGateOverlay: ConsentGateOverlay, ConsentStatus: ConsentStatus,
  });
})();
