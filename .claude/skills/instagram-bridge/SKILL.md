---
name: instagram-bridge
description: Instagram-Brücke für den Account @golf.vibies — Feed lesen und analysieren, Posts entwerfen, Grafiken rendern, Medien über GitHub veröffentlichen und Posts über Metricool auf Instagram planen. Nutze diese Skill, wenn es um golf.vibies, Instagram-Posts, Reels, Stories, Captions, Redaktionsplan oder Social-Analytics geht.
---

# Instagram-Brücke: golf.vibies

Die Brücke hat drei Glieder. Du bedienst alle drei.

```
Cowork  ──1── Grafik rendern (lokal, Playwright)
        ──2── Bild committen → öffentliche raw.githubusercontent-URL
        ──3── Metricool MCP → Instagram @golf.vibies
```

## Feste Werte

| | |
|---|---|
| Metricool `blogId` | `7272560` |
| Zeitzone | `Europe/Zurich` |
| Handle | `@golf.vibies` |
| Medien-Basis-URL | `https://raw.githubusercontent.com/<OWNER>/<REPO>/main/media/` |

`brand.json` im Repo-Root hält Stimme, Farben, Hashtags und Formate. **Lies sie, bevor du Text oder Grafik schreibst.**

## Lesen / Analysieren

- `getBrandSettings` — Brands und verbundene Netzwerke.
- `getAnalyticsDataByMetrics` — braucht `brandId`, `from`, `to` und Feld-IDs:
  - Posts: `IGPO02` Datum, `IGPO03` Text, `IGPO06` URL, `IGPO07` Typ, `IGPO13` Likes, `IGPO08` Kommentare, `IGPO14` Reach, `IGPO28` Views, `IGPO15` Saves, `IGPO29` neue Follower
  - Reels: `IGRE…` · Stories: `IGST…` · Konto-Entwicklung: `IGEV01` Follower, `IGEV43/44` gewonnen/verloren
  - Wettbewerber: `IGCP…` / `IGCR…` · Hashtags: `IGHT…`
  - Volle Liste: `getAnalyticsAvailableMetrics` mit `network: "instagram"`. Felder mit „Deprecated" im Label nie verwenden.
- `getBestTimeToPostByNetwork` — Zeitfenster, wenn kein Termin vorgegeben ist.
- `getScheduledPosts` — was schon geplant ist. **Immer prüfen, bevor du neu planst**, sonst doppelst du Slots.

Kommen nur Nullzeilen zurück, hat Metricool für den Zeitraum noch keine Daten. Das sagen, nicht als „0 Reichweite" interpretieren.

## Posten

### 1 — Entwerfen
`python3 scripts/new_post.py <slug>` legt `content/posts/<slug>/` mit `spec.json`, `caption.md`, `meta.json` an.

Caption: Hook in max. 2 Zeilen, dann Substanz, dann CTA, dann 8–12 Hashtags. Max. 2200 Zeichen. Kein Clickbait, Du-Form.

### 2 — Grafik rendern
`node scripts/render_post.mjs content/posts/<slug>/spec.json media/<slug>.jpg`

Formate: `post` 1080×1350 · `square` 1080×1080 · `story`/`reel_cover` 1080×1920.
`photo` in der Spec nimmt eine Bild-URL als Hintergrund; ohne sie rendert ein Farbverlauf.
**Vor dem Veröffentlichen das Bild mit Read ansehen.** Zu lange Headlines brechen das Layout.

### 3 — Medien veröffentlichen
Bild nach `media/` committen und pushen. Die URL ist erst nach dem Push erreichbar — danach prüfen:
`curl -sI <url> | head -1` muss `200` liefern. Metricool holt die Datei selbst; ein 404 lässt den Post stillschweigend scheitern.

### 4 — In Metricool planen
`createScheduledPost` mit `blogId`, `date` (ISO 8601 mit Offset, nie in der Vergangenheit) und `info`:

```json
{
  "autoPublish": true,
  "draft": false,
  "text": "<Caption>",
  "media": ["https://raw.githubusercontent.com/<OWNER>/<REPO>/main/media/<slug>.jpg"],
  "mediaAltText": ["<Bildbeschreibung>"],
  "providers": [{"network": "instagram"}],
  "publicationDate": {"dateTime": "2026-10-09T18:10:00", "timezone": "Europe/Zurich"},
  "instagramData": {"type": "POST", "isAiGenerated": false},
  "shortener": false,
  "smartLinkData": {"ids": []},
  "descendants": [],
  "firstCommentText": "",
  "hasNotReadNotes": false
}
```

Danach `metricool_post_id`, `scheduled_for` und `media_url` in `meta.json` nachtragen, `status` auf `scheduled`.

### Regeln, die Instagram erzwingt
- `POST` braucht mindestens ein Bild (mehrere = Karussell), `REEL`/`TRIAL_REEL` ein Video, `STORY` Bild oder Video.
- Stories haben keine Caption: ist Story das einzige Netzwerk, `text` weglassen.
- `isAiGenerated: true` nur bei tatsächlich KI-erzeugten Bildern/Videos. Template-Renderings aus `render_post.mjs` sind es nicht.
- `mediaAltText` immer füllen — Barrierefreiheit und Reichweite.

## Freigabe

Der Kontoinhaber hat **Auto-Publish** gewählt: geplante Posts gehen ohne weitere Rückfrage live. Trotzdem:
- Caption und gerendertes Bild **vor** dem Planen im Chat zeigen.
- Beim allerersten Post des Accounts und bei allem, was eine Marke, Person oder einen Preis nennt, einmal rückfragen.
- `draft: true` setzen, wenn der Nutzer „Entwurf", „erst mal ansehen" o. ä. sagt.
- Ändern statt neu anlegen: `updateScheduledPost` braucht `id` **und** `uuid` aus `getScheduledPosts` und den vollständigen, unveränderten Rest von `info`. Die `id` ändert sich bei jedem Update.
