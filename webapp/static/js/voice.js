/* voice.js — Mikrofon-Aufnahme + Whisper-Transkription.
   Selbstständig, UI-frei, State-frei. Exportiert window.VoiceRecorder.
   Stil: IIFE, var, kein ES-Module, kein import (wie ui.js). */
(function () {
  'use strict';

  /* Interner Zustand — nur zwischen starten() und stoppenUndTranskribieren()/abbrechen(). */
  var _recorder = null;    // MediaRecorder-Instanz
  var _stream = null;      // MediaStream (Mikrofon-Tracks)
  var _chunks = [];        // dataavailable-Puffer
  var _laeuft = false;     // true zwischen starten() und Stopp

  /* ---- Hilfsfunktionen -------------------------------------------------- */

  /** Gibt den bestmöglichen Audio-MIME-Type zurück. */
  function _bestMime() {
    if (typeof window !== 'undefined' &&
        typeof window.MediaRecorder !== 'undefined' &&
        typeof window.MediaRecorder.isTypeSupported === 'function') {
      var prefer = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/mp4'
      ];
      for (var i = 0; i < prefer.length; i++) {
        if (window.MediaRecorder.isTypeSupported(prefer[i])) {
          return prefer[i];
        }
      }
    }
    return ''; // Browser-Default
  }

  /** Alle Tracks des Streams stoppen (Mikrofon-LED aus). */
  function _streamFreigeben() {
    if (_stream) {
      var tracks = _stream.getTracks ? _stream.getTracks() : [];
      for (var i = 0; i < tracks.length; i++) {
        tracks[i].stop();
      }
      _stream = null;
    }
  }

  /** Internen Aufnahme-Zustand vollständig zurücksetzen. */
  function _zustandReset() {
    _recorder = null;
    _chunks = [];
    _laeuft = false;
    _streamFreigeben();
  }

  /* ---- Öffentliche API -------------------------------------------------- */

  var VoiceRecorder = {

    /**
     * true, wenn der Browser MediaRecorder und getUserMedia unterstützt.
     * Wirft nie eine Exception.
     */
    verfuegbar: function () {
      try {
        return !!(
          typeof navigator !== 'undefined' &&
          navigator.mediaDevices &&
          typeof navigator.mediaDevices.getUserMedia === 'function' &&
          typeof window !== 'undefined' &&
          typeof window.MediaRecorder !== 'undefined'
        );
      } catch (e) {
        return false;
      }
    },

    /**
     * true, solange eine Aufnahme läuft (zwischen starten() und
     * stoppenUndTranskribieren()/abbrechen()).
     */
    aufnahmeLaeuft: function () {
      return _laeuft;
    },

    /**
     * Startet die Mikrofon-Aufnahme.
     * Resolve: Aufnahme läuft.
     * Reject: Error mit .code ∈ {'no_support','no_permission','fehler'}.
     * Doppeltes Starten wird verhindert.
     */
    starten: function () {
      return new Promise(function (resolve, reject) {
        /* Browser-Support prüfen */
        if (!VoiceRecorder.verfuegbar()) {
          var noSup = new Error('MediaRecorder oder getUserMedia nicht verfügbar');
          noSup.code = 'no_support';
          return reject(noSup);
        }

        /* Doppeltes Starten verhindern */
        if (_laeuft) {
          return resolve();
        }

        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
          _stream = stream;
          _chunks = [];

          var mime = _bestMime();
          var recOpts = mime ? { mimeType: mime } : {};
          var rec;
          try {
            rec = new window.MediaRecorder(stream, recOpts);
          } catch (e) {
            _streamFreigeben();
            var fe = new Error('MediaRecorder konnte nicht erstellt werden: ' + e.message);
            fe.code = 'fehler';
            return reject(fe);
          }

          rec.addEventListener('dataavailable', function (ev) {
            if (ev.data && ev.data.size > 0) {
              _chunks.push(ev.data);
            }
          });

          rec.addEventListener('start', function () {
            _laeuft = true;
            resolve();
          });

          rec.addEventListener('error', function (ev) {
            _zustandReset();
            var re = new Error('MediaRecorder-Fehler: ' + (ev.error ? ev.error.message : 'unbekannt'));
            re.code = 'fehler';
            reject(re);
          });

          _recorder = rec;

          /* timeslice 250 ms: chunks kommen regelmäßig, letzter Chunk beim stop-Event */
          rec.start(250);

        }).catch(function (err) {
          _streamFreigeben();
          var mapped;
          if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError' ||
                      err.name === 'PermissionDeniedError')) {
            mapped = new Error('Mikrofon-Zugriff verweigert');
            mapped.code = 'no_permission';
          } else if (err && (err.name === 'NotFoundError' || err.name === 'NotSupportedError' ||
                             err.name === 'TypeError')) {
            mapped = new Error('Kein Mikrofon gefunden oder nicht unterstützt');
            mapped.code = 'no_support';
          } else {
            mapped = new Error(err ? err.message : 'Unbekannter Fehler');
            mapped.code = 'fehler';
          }
          reject(mapped);
        });
      });
    },

    /**
     * Bricht die laufende Aufnahme ab ohne Upload.
     * Tracks werden gestoppt (Mikrofon-LED aus), Zustand zurückgesetzt.
     */
    abbrechen: function () {
      if (_recorder && _recorder.state !== 'inactive') {
        try { _recorder.stop(); } catch (e) { /* ignorieren */ }
      }
      _zustandReset();
    },

    /**
     * Stoppt die Aufnahme, transkribiert via /api/transkription.
     * opts = { lang: 'de'|'en' }
     * Gibt Promise<{text, source, hinweis, ok}> zurück — wirft NIE.
     * ok = (source === 'whisper' && text nicht leer).
     * Stream wird immer freigegeben, auch im Fehlerfall.
     */
    stoppenUndTranskribieren: function (opts) {
      opts = opts || {};
      var lang = (opts.lang === 'en') ? 'en' : 'de';

      return new Promise(function (resolve) {
        /* Wenn gar nichts läuft: sauber zurückmelden */
        if (!_recorder || !_laeuft) {
          _zustandReset();
          return resolve({
            text: '',
            source: 'hinweis',
            hinweis: 'Keine aktive Aufnahme',
            ok: false
          });
        }

        var recRef = _recorder;
        var chunksRef = _chunks;

        /* Auf stop-Event warten, dann Blob bauen und hochladen */
        recRef.addEventListener('stop', function onStop() {
          recRef.removeEventListener('stop', onStop);

          /* Stream immer freigeben */
          _streamFreigeben();
          _laeuft = false;
          _recorder = null;
          _chunks = [];

          /* Blob aus gesammelten Chunks */
          var mimeType = recRef.mimeType || '';
          var blob;
          try {
            blob = new Blob(chunksRef, mimeType ? { type: mimeType } : {});
          } catch (e) {
            return resolve({
              text: '',
              source: 'hinweis',
              hinweis: 'Audio-Daten konnten nicht zusammengesetzt werden',
              ok: false
            });
          }

          /* Upload als multipart FormData, Feld "file" */
          var fd = new FormData();
          /* Dateiname mit passender Endung für Whisper-Typ-Erkennung */
          var ext = mimeType.indexOf('ogg') !== -1 ? 'ogg'
                  : mimeType.indexOf('mp4') !== -1 ? 'mp4'
                  : 'webm';
          fd.append('file', blob, 'aufnahme.' + ext);

          var url = '/api/transkription?lang=' + encodeURIComponent(lang);

          fetch(url, { method: 'POST', body: fd })
            .then(function (resp) {
              return resp.json();
            })
            .then(function (data) {
              var text = (data && data.text) ? data.text : '';
              var source = (data && data.source) ? data.source : 'hinweis';
              var hinweis = (data && data.hinweis) ? data.hinweis : undefined;
              var ok = (source === 'whisper' && !!(text && text.trim()));
              resolve({ text: text, source: source, hinweis: hinweis, ok: ok });
            })
            .catch(function (err) {
              resolve({
                text: '',
                source: 'hinweis',
                hinweis: 'Transkription nicht verfügbar: ' + (err && err.message ? err.message : 'Netzwerkfehler'),
                ok: false
              });
            });
        });

        /* Recorder stoppen — löst das stop-Event aus (nach letztem dataavailable) */
        try {
          recRef.stop();
        } catch (e) {
          /* Falls stop() fehlschlägt: Stream freigeben und Fehler melden */
          _streamFreigeben();
          _laeuft = false;
          _recorder = null;
          _chunks = [];
          resolve({
            text: '',
            source: 'hinweis',
            hinweis: 'Aufnahme konnte nicht gestoppt werden',
            ok: false
          });
        }
      });
    }
  };

  /* An window hängen (wie ui.js, screens.js, app.js) */
  if (typeof window !== 'undefined') {
    window.VoiceRecorder = VoiceRecorder;
  }

}());
