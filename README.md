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

## Zweiter Weg: direkt über die Instagram-Graph-API

Ohne Metricool, ohne laufende Kosten. Drei Skripte in `scripts/`, nur Standardbibliothek:

| Datei | Zweck |
|---|---|
| `ig_api.py` | Graph-Aufrufe, Fehlerbehandlung, Zugangsdaten aus der Umgebung |
| `ig_token.py` | langlebiges Token holen und erneuern, `IG_USER_ID` finden |
| `ig_publish.py` | Post, Karussell, Reel und Story veröffentlichen |

### Voraussetzungen

1. Instagram **Profikonto** (Business oder Creator)
2. Eine **Facebook-Seite**, die mit diesem Konto verbunden ist — Meta nutzt sie als
   Authentifizierungsanker, auch wenn nie auf Facebook gepostet wird
3. Eigene **Meta-App** im Entwicklungsmodus auf developers.facebook.com,
   das Instagram-Konto darin als **Instagram Tester** hinterlegt und die Einladung
   in den Instagram-Einstellungen angenommen

Solange nur auf das eigene Konto veröffentlicht wird, ist **keine App-Review nötig**.
Die wird erst verlangt, wenn eine App für fremde Konten postet.

### Einrichten

```bash
# Token umtauschen (kurzlebig aus dem Graph API Explorer -> langlebig, 60 Tage)
python3 scripts/ig_token.py --exchange <SHORT_TOKEN> --app-id <ID> --app-secret <SECRET>

# Konto-ID herausfinden
IG_ACCESS_TOKEN=<LANG> python3 scripts/ig_token.py --whoami
```

Dann `IG_USER_ID` und `IG_ACCESS_TOKEN` als Secrets der Umgebung hinterlegen —
**nicht ins Repo committen.** Vor Ablauf der 60 Tage erneuern mit `--refresh`.

### Veröffentlichen

```bash
python3 scripts/ig_publish.py --type reel \
  --media https://raw.githubusercontent.com/<OWNER>/<REPO>/main/media/reel-mulligans.mp4 \
  --caption-file content/posts/hot-mulligans/caption.md

python3 scripts/ig_publish.py --type post --media <URL> --caption-file <DATEI> --alt "<Beschreibung>"
python3 scripts/ig_publish.py --type story --media <URL>
python3 scripts/ig_publish.py --type carousel --media <URL1> <URL2> --caption-file <DATEI>
```

`--dry-run` prüft Caption-Länge und Medienzahl, ohne etwas zu senden.

### Grenzen

- **Veröffentlicht sofort.** Zeitplanung kann die Graph-API nicht; dafür braucht es
  entweder Metricool oder einen eigenen Zeitgeber (cron, GitHub Actions).
- **TikTok geht so nicht.** TikToks Content Posting API verlangt einen eigenen Audit.
  Ohne ihn landet alles auf „nur ich" oder als Entwurf im TikTok-Posteingang.
- **Medien brauchen eine öffentliche URL.** Instagram lädt sie selbst herunter —
  dafür dient `media/` in diesem öffentlichen Repo.

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
