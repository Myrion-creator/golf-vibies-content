# Instagram-Brücke · @golf.vibies

Verbindet Claude Cowork mit dem Instagram-Account **@golf.vibies**: Feed und Kennzahlen lesen,
Posts entwerfen, Grafiken rendern, veröffentlichen.

```
┌─────────────┐   render    ┌──────────┐   git push   ┌───────────────────────┐
│   Cowork    │ ──────────► │  media/  │ ───────────► │ raw.githubusercontent │
│  (Claude)   │             │          │              │   (öffentliche URL)   │
└──────┬──────┘             └──────────┘              └───────────┬───────────┘
       │                                                          │ holt Datei
       │  createScheduledPost (MCP)   ┌───────────┐               │
       └────────────────────────────► │ Metricool │ ◄─────────────┘
                                      └─────┬─────┘
                        Analytics (lesen)   │ veröffentlicht
                        ◄───────────────────┼──────────────► Instagram @golf.vibies
```

Es gibt bewusst **keinen eigenen Server**. Metricool hält das Instagram-Token und besitzt die
Meta-App-Freigabe; GitHub liefert die öffentlichen Medien-URLs, die Metricool verlangt.

## Aufbau

| Pfad | Zweck |
|---|---|
| `brand.json` | Stimme, Farben, Hashtags, Formate, Metricool-`blogId` |
| `scripts/render_post.mjs` | JSON-Spec → JPEG/PNG in Instagram-Maßen (Playwright) |
| `scripts/new_post.py` | legt ein Post-Verzeichnis an |
| `content/posts/<slug>/` | `spec.json` (Grafik), `caption.md` (Text), `meta.json` (Status) |
| `media/` | gerenderte Bilder — **öffentlich**, das ist der Sinn |
| `.claude/skills/instagram-bridge/` | Anleitung, die Cowork automatisch lädt |

## Benutzen

Im Alltag redest du einfach mit Cowork: *„Entwirf drei Posts zum Thema Putting für nächste Woche."*
Die Skill wird automatisch geladen und kennt `blogId`, Zeitzone, Formate und Freigaberegeln.

Von Hand:

```bash
python3 scripts/new_post.py putting-drill
# spec.json und caption.md ausfüllen
node scripts/render_post.mjs content/posts/putting-drill/spec.json media/putting-drill.jpg
git add media content && git commit -m "post: putting-drill" && git push
curl -sI https://raw.githubusercontent.com/<OWNER>/<REPO>/main/media/putting-drill.jpg | head -1
```

Danach plant Cowork den Post über Metricool ein.

## Grenzen

- **Metricool veröffentlicht, nicht wir.** Was Metricool für Instagram nicht unterstützt, geht auch hier nicht.
- **Medien sind öffentlich**, sobald sie gepusht sind — vor dem Veröffentlichungstermin sichtbar.
  Nichts in `media/` ablegen, was nicht ohnehin auf Instagram landet. Metricool zieht beim
  Einplanen eine eigene Kopie, die URL muss danach nicht bestehen bleiben.
- **Kommentare, DMs, Follower-Aktionen** sind nicht angebunden. Metricool bietet dafür
  eine Inbox, die über diese MCP-Tools nicht erreichbar ist.
- **Analytics hängen an Metricools Abholrhythmus**, nicht an Instagram live.
- **Auto-Publish ist aktiv.** Geplante Posts gehen ohne weitere Rückfrage live.

## Einrichtung neu aufsetzen

1. Instagram-Business-Account in Metricool verbinden (→ `blogId`, steht in `brand.json`).
2. Metricool-Connector in Claude verbinden.
3. Dieses Repo **öffentlich** anlegen — `raw.githubusercontent.com` liefert sonst kein Bild aus.
4. `brand.json` und die Platzhalter `<OWNER>/<REPO>` in README und Skill anpassen.
