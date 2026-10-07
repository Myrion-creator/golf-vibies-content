# Bauanleitung: Instagram-Brücke von null

Diese Datei beschreibt, wie die Brücke aufgebaut ist, damit Claude Code sie in einem
leeren Projekt nachbauen kann. Sie enthält die Verträge der Bausteine und die
Fallstricke, die beim ersten Bau Zeit gekostet haben.

---

## 1 — Was gebaut wird

Eine Kette, die Social-Media-Beiträge erzeugt und veröffentlicht, ohne bezahlten
Zwischendienst:

```
Claude  ──1── Grafik oder Video rendern (lokal)
        ──2── Medium in ein öffentliches Git-Repo pushen
        ──3── Instagram Graph API: Container anlegen → veröffentlichen
```

Schritt 2 ist nötig, weil Instagram Medien **nicht entgegennimmt**, sondern sie sich
unter einer öffentlich erreichbaren URL selbst abholt.

Es gibt bewusst keinen eigenen Server. Alles läuft als Skript in einer Sitzung.

---

## 2 — Voraussetzungen

**Konten**

1. Instagram **Profikonto** (Business oder Creator), kein Privatkonto
2. Eine **Facebook-Seite**, mit diesem Konto verbunden. Meta nutzt sie als
   Authentifizierungsanker, auch wenn nie auf Facebook gepostet wird. Ohne sie gibt die
   Graph-API das Instagram-Konto nicht heraus und der Audiokatalog antwortet mit 403.
3. Eigene **Meta-App** auf developers.facebook.com im **Entwicklungsmodus**, das
   Instagram-Konto darin als **Instagram Tester**, Einladung in den Instagram-
   Einstellungen angenommen.
4. Öffentliches **Git-Repo** als Medienspeicher.

**App-Review ist nicht nötig**, solange nur auf das eigene Konto veröffentlicht wird.
Sie wird erst verlangt, wenn eine App für fremde Konten postet.

**Werkzeuge**

| | wofür | Prüfen mit |
|---|---|---|
| Node + Playwright | Grafiken rendern | `node -e "require('playwright')"` |
| ffmpeg | Videos bauen | `ffmpeg -version` |
| Python 3 | API-Aufrufe | nur Standardbibliothek |

---

## 3 — Dateistruktur

```
brand.json                  Stimme, Farben, Hashtags, Formate — eine Quelle der Wahrheit
scripts/
  ig_api.py                 Graph-Aufrufe, Fehlerbehandlung, Zugangsdaten
  ig_token.py               Token holen und erneuern, IG_USER_ID finden
  ig_publish.py             Post, Karussell, Reel, Story veröffentlichen
  render_post.mjs           JSON-Spec → JPEG/PNG in Instagram-Maßen
  render_reel.py            drei Standbilder → MP4
content/posts/<slug>/       spec.json, caption.md, meta.json
media/                      gerenderte Dateien, öffentlich
```

`meta.json` hält pro Beitrag Status, Termin, Medien-URL und die vergebene Medien-ID.
Ohne das weiß eine spätere Sitzung nicht, was schon veröffentlicht wurde, und postet doppelt.

---

## 4 — Die Bausteine

### 4.1 `ig_api.py`

Eine Funktion `call(path, params, method, token)` gegen
`https://graph.facebook.com/<version>/<path>`. Version aus `GRAPH_VERSION`,
Standard `v23.0`.

**Fehler müssen ausgepackt werden.** Die Graph-API antwortet bei Fehlern mit HTTP 4xx
und einem JSON-Körper, den `urllib` als Exception wegwirft. Ohne `HTTPError.read()`
steht am Ende nur „HTTP 400" statt der Ursache. Zusätzlich `error_user_msg` ausgeben,
falls vorhanden — dort steht oft der eigentliche Hinweis.

Zugangsdaten aus `IG_USER_ID` und `IG_ACCESS_TOKEN`, mit einer Fehlermeldung, die sagt,
wie man sie bekommt.

### 4.2 `ig_token.py`

Drei Modi:

| Modus | Aufruf |
|---|---|
| `--exchange <SHORT> --app-id --app-secret` | kurzlebiges Token → langlebiges, 60 Tage |
| `--whoami` | listet Facebook-Seiten und das daran hängende Instagram-Konto |
| `--refresh` | verlängert ein langlebiges Token um weitere 60 Tage |

Alle drei gehen gegen `oauth/access_token` mit `grant_type=fb_exchange_token`.
`--whoami` fragt `me/accounts?fields=id,name,instagram_business_account{id,username}`.

Das Token **nie ins Repo**. Als Secret der Umgebung hinterlegen.

### 4.3 `ig_publish.py`

Der Veröffentlichungsablauf der Graph-API hat drei Schritte:

```
POST /<IG_USER_ID>/media           → creation_id        Container anlegen
GET  /<creation_id>?fields=status_code                  nur bei Video: auf FINISHED warten
POST /<IG_USER_ID>/media_publish   → media_id           veröffentlichen
GET  /<media_id>?fields=permalink                       Link zurückgeben
```

Parameter je Typ:

| Typ | Parameter |
|---|---|
| Bild | `image_url`, `caption`, `alt_text` |
| Reel | `video_url`, `media_type=REELS`, optional `cover_url` |
| Story | `image_url` oder `video_url`, `media_type=STORIES`, **keine Caption** |
| Karussell | je Kind `is_carousel_item=true`, dann Eltern-Container mit `media_type=CAROUSEL` und `children=<ids>` |

Vor dem Senden prüfen: Caption ≤ 2200 Zeichen, Karussell 2–10 Medien, Story ohne Text.
Ein `--dry-run` spart echte Fehlversuche.

**Video-Container brauchen Verarbeitungszeit.** Ohne Warteschleife schlägt
`media_publish` mit einem irreführenden Fehler fehl. Alle 5 Sekunden abfragen, bei
`ERROR` abbrechen, nach 5 Minuten aufgeben — und dann nichts veröffentlichen.

### 4.4 `render_post.mjs`

JSON-Spec → Bild. Formate: `post` 1080×1350, `square` 1080×1080,
`story`/`reel_cover` 1080×1920.

Spec-Felder: `kind`, `kicker`, `headline`, `subheadline`, `footer`, `bg`, `accent`,
`photo`, `headlineSize`, `layout` (`center` oder `bottom-left`).

Schriftgrößen relativ zur Höhe skalieren, damit ein Layout in allen Formaten trägt.

### 4.5 `render_reel.py`

Drei Standbilder über `render_post.mjs` (kind `story`), je 3,5 s mit langsamem
`zoompan`, mit `xfade` 0,5 s überblendet, stille AAC-Tonspur. Ergebnis 9,5 s,
1080×1920, H.264.

Aufbau der drei Bilder: **Behauptung → Begründung → Konsequenz.**

---

## 5 — Fallstricke

Jeder Punkt hat beim ersten Bau Zeit gekostet.

**Rendering**

- `chromium --headless --screenshot` liefert **nicht** die Fenstergröße als Bildgröße.
  Der sichtbare Bereich war 1264 statt 1350 px hoch, der Rest blieb leer. Playwright mit
  `setViewportSize` + `page.screenshot` statt des nackten Chromium-Aufrufs.
- `\n` in einer Headline wird nur mit `white-space: pre-line` zum Zeilenumbruch,
  sonst erscheint es als Text.
- Vor `page.screenshot` auf `document.fonts.ready` warten, sonst rendert die
  Ersatzschrift.
- **Jedes gerenderte Bild ansehen, bevor es rausgeht.** Ein vertauschter Parameter
  schrieb die Schriftgröße als Untertitel ins Bild — „56" stand mitten im Reel. Keine
  Prüfung von Dateigröße oder Rückgabewert hätte das gefunden.
- Profilbilder **rund zuschneiden und auf 32 px herunterrechnen** prüfen. So klein zeigt
  Instagram sie neben jedem Post. Ein Schriftzug ist dort nie lesbar.

**Instagram**

- Medien müssen **öffentlich** erreichbar sein. `raw.githubusercontent.com` liefert MP4
  als `application/octet-stream` — das stört nicht, Instagram lädt es trotzdem.
- Gleicher Dateiname nach einer Änderung kann eine alte, zwischengespeicherte Fassung
  ausliefern. Neuen Namen vergeben (`-v2`, `-en`).
- **Storys tragen keine Caption.** Text im Feld wird verworfen.
- Das **Veröffentlichungslimit** steht in Metas Doku an einer Stelle mit 100 und an
  anderer mit 50 Beiträgen pro rollenden 24 Stunden. Verlässlich ist nur
  `GET /<IG_USER_ID>/content_publishing_limit` — liefert `quota_usage` und `quota_total`
  für das konkrete Konto. **Vor Massenveröffentlichungen abfragen.**
- Kein Mitternachts-Reset: Das Fenster rollt.
- **Auf fremden Profilen kommentieren geht nicht.** Die API erlaubt nur Kommentare und
  Antworten auf eigenen Beiträgen. Werkzeuge, die es anbieten, fahren
  Browser-Automatisierung gegen die Nutzungsbedingungen.
- **Zeitplanung kann die Graph-API nicht.** Sie veröffentlicht sofort. Für Termine
  braucht es einen eigenen Zeitgeber — cron, GitHub Actions oder einen Planungsdienst.
- Der **Instagram-Audiokatalog** antwortet mit 403, wenn keine Facebook-Seite verbunden
  ist. Dann gehen Reels stumm raus, was messbar schlechter läuft.

**TikTok**

- TikToks Content Posting API verlangt einen **eigenen Audit** zusätzlich zur
  Entwickler-Registrierung. Ohne ihn ist jeder Direktbeitrag auf `SELF_ONLY` gezwungen.
- Ohne Audit bleibt der Upload-Weg: Das Video landet als Entwurf im TikTok-Posteingang,
  veröffentlichen muss der Kontoinhaber von Hand.

**Inhalt**

- Zweisprachige Captions verdoppeln die Länge und reißen das 2200-Zeichen-Limit.
- Behauptungen über reale Personen **vor dem Schreiben prüfen.** Beispiel: Der berühmte
  Nike-Jonglier-Spot entstand in vier Takes, nicht in einem — die verbreitete Version
  ist falsch.
- Rotierende Textbausteine passen nicht automatisch zur Frage. „Nenn deine Zahl" unter
  einer Ja/Nein-Frage wirkt maschinell. Nach dem Fragetyp auswählen.

---

## 6 — Verifikation

In dieser Reihenfolge, jeder Schritt einzeln:

1. `ig_token.py --whoami` zeigt Seite und `IG_USER_ID` → Konten korrekt verbunden
2. `curl -sI <medien-url> | head -1` liefert `200` → Medium erreichbar
3. `ig_publish.py --dry-run` → Caption und Medienzahl gültig
4. `GET /<IG_USER_ID>/content_publishing_limit` → Kontingent frei
5. Ein echter Testbeitrag → Permalink öffnen und ansehen
6. `meta.json` nachtragen → nächste Sitzung postet nicht doppelt

Kein Schritt darf übersprungen werden, weil der vorige „eigentlich klappen müsste".
Veröffentlichung scheitert oft still.
