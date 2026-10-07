#!/usr/bin/env python3
"""Direkt auf Instagram veröffentlichen — ohne Metricool, ohne Drittanbieter.

    python3 scripts/ig_publish.py --type post  --media <URL> --caption-file content/posts/x/caption.md
    python3 scripts/ig_publish.py --type reel  --media <URL> --caption-file ... --cover <URL>
    python3 scripts/ig_publish.py --type story --media <URL>
    python3 scripts/ig_publish.py --type carousel --media <URL> <URL> ... --caption-file ...

Das Medium muss unter einer öffentlich erreichbaren URL liegen; Instagram lädt es
selbst herunter. Dafür dient das media/-Verzeichnis dieses Repos auf GitHub.

Ablauf laut Graph-API: Container anlegen → bei Video auf FINISHED warten →
veröffentlichen → Permalink holen.
"""
import argparse
import pathlib
import sys
import time

from ig_api import GraphError, call, credentials

MEDIA_TYPE = {"post": None, "carousel": None, "reel": "REELS", "story": "STORIES"}
POLL_EVERY, POLL_MAX = 5, 300  # Sekunden


def is_video(url: str) -> bool:
    return url.lower().split("?")[0].endswith((".mp4", ".mov"))


def container(uid: str, token: str, *, kind: str, url: str, caption=None,
              alt=None, cover=None, is_child=False) -> str:
    p = {"caption": caption, "alt_text": alt}
    if is_child:
        p["is_carousel_item"] = "true"
        p.pop("caption")
    if kind in ("reel", "story") or is_video(url):
        p["video_url"] = url
        p["media_type"] = MEDIA_TYPE[kind] or "REELS"
        if cover:
            p["cover_url"] = cover
    else:
        p["image_url"] = url
        if kind == "story":
            p["media_type"] = "STORIES"
    return call(f"{uid}/media", p, method="POST", token=token)["id"]


def wait_until_ready(cid: str, token: str) -> None:
    """Video-Container brauchen Verarbeitungszeit. Blockiert bis FINISHED."""
    waited = 0
    while waited < POLL_MAX:
        r = call(cid, {"fields": "status_code,status"}, token=token)
        code = r.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise GraphError(f"Instagram konnte das Medium nicht verarbeiten: {r.get('status','')}")
        print(f"  verarbeitet… ({code}, {waited}s)", file=sys.stderr)
        time.sleep(POLL_EVERY)
        waited += POLL_EVERY
    raise GraphError(f"Container nach {POLL_MAX}s nicht fertig — Abbruch, nichts veröffentlicht.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--type", required=True, choices=list(MEDIA_TYPE))
    ap.add_argument("--media", required=True, nargs="+", metavar="URL")
    ap.add_argument("--caption-file")
    ap.add_argument("--caption")
    ap.add_argument("--alt")
    ap.add_argument("--cover", help="Titelbild-URL für Reels")
    ap.add_argument("--dry-run", action="store_true", help="nur prüfen, nichts senden")
    a = ap.parse_args()

    uid, token = credentials()

    caption = a.caption
    if a.caption_file:
        caption = pathlib.Path(a.caption_file).read_text().rstrip("\n")
    if caption and len(caption) > 2200:
        raise SystemExit(f"Caption ist {len(caption)} Zeichen lang, Instagram erlaubt 2200.")
    if a.type == "story" and caption:
        print("Hinweis: Storys haben keine Caption — Text wird ignoriert.", file=sys.stderr)
        caption = None
    if a.type == "carousel" and not 2 <= len(a.media) <= 10:
        raise SystemExit("Ein Karussell braucht 2 bis 10 Medien.")
    if a.type != "carousel" and len(a.media) != 1:
        raise SystemExit(f"--type {a.type} erwartet genau eine Medien-URL.")

    if a.dry_run:
        print(f"OK  typ={a.type}  medien={len(a.media)}  caption={len(caption or '')} Zeichen")
        return

    try:
        if a.type == "carousel":
            kids = []
            for u in a.media:
                print(f"Container für {u.rsplit('/',1)[-1]}…", file=sys.stderr)
                cid = container(uid, token, kind="post", url=u, is_child=True, alt=a.alt)
                if is_video(u):
                    wait_until_ready(cid, token)
                kids.append(cid)
            cid = call(f"{uid}/media", {"media_type": "CAROUSEL",
                                        "children": ",".join(kids),
                                        "caption": caption},
                       method="POST", token=token)["id"]
        else:
            cid = container(uid, token, kind=a.type, url=a.media[0],
                            caption=caption, alt=a.alt, cover=a.cover)
            if is_video(a.media[0]):
                wait_until_ready(cid, token)

        media_id = call(f"{uid}/media_publish", {"creation_id": cid},
                        method="POST", token=token)["id"]
        link = call(media_id, {"fields": "permalink"}, token=token).get("permalink", "")
        print(f"\nVeröffentlicht.\n  media_id {media_id}\n  {link}")
    except GraphError as e:
        print(f"\nGraph-API meldet:\n  {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
