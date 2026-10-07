#!/usr/bin/env python3
"""Zugangsdaten für die direkte Instagram-Brücke besorgen und erneuern.

Drei Schritte, einmalig:

  1) Kurzlebiges Token im Graph API Explorer holen, dann umtauschen:
       python3 scripts/ig_token.py --exchange <SHORT_TOKEN> --app-id <ID> --app-secret <SECRET>
     Ergebnis: langlebiges Token, 60 Tage gültig.

  2) Instagram-Konto-ID herausfinden:
       IG_ACCESS_TOKEN=<LANG> python3 scripts/ig_token.py --whoami

  3) Beides als Secrets der Cloud-Umgebung hinterlegen: IG_USER_ID, IG_ACCESS_TOKEN

Später, vor Ablauf der 60 Tage:
       IG_ACCESS_TOKEN=<LANG> python3 scripts/ig_token.py --refresh
"""
import argparse
import datetime
import sys

from ig_api import GraphError, call


def exchange(short_token: str, app_id: str, app_secret: str) -> None:
    r = call("oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    show_token(r)


def refresh(token: str) -> None:
    """Ein langlebiges Token gegen ein frisches tauschen (verlängert um 60 Tage)."""
    r = call("oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "fb_exchange_token": token,
    }, token=None)
    show_token(r)


def show_token(r: dict) -> None:
    tok = r.get("access_token", "")
    secs = r.get("expires_in")
    print("\nIG_ACCESS_TOKEN=" + tok)
    if secs:
        until = datetime.datetime.now() + datetime.timedelta(seconds=int(secs))
        print(f"\nGültig bis etwa {until:%d.%m.%Y} ({int(secs)//86400} Tage).")
    print("Als Secret der Cloud-Umgebung hinterlegen, nicht ins Repo committen.")


def whoami(token: str) -> None:
    """Listet Facebook-Seiten und das daran hängende Instagram-Profikonto."""
    pages = call("me/accounts", {"fields": "id,name,instagram_business_account{id,username}"},
                 token=token).get("data", [])
    if not pages:
        print("Keine Facebook-Seite gefunden.\n"
              "Das Instagram-Konto muss ein Profikonto sein UND mit einer Facebook-Seite\n"
              "verbunden, sonst gibt die Graph-API es nicht heraus.")
        return
    print(f"{len(pages)} Facebook-Seite(n):\n")
    for p in pages:
        ig = p.get("instagram_business_account")
        print(f"  Seite: {p['name']}  (id {p['id']})")
        if ig:
            print(f"    IG_USER_ID={ig['id']}   @{ig.get('username','?')}")
        else:
            print("    kein Instagram-Profikonto verbunden")
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exchange", metavar="SHORT_TOKEN")
    ap.add_argument("--app-id")
    ap.add_argument("--app-secret")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--whoami", action="store_true")
    a = ap.parse_args()

    import os
    token = os.environ.get("IG_ACCESS_TOKEN")

    try:
        if a.exchange:
            if not (a.app_id and a.app_secret):
                ap.error("--exchange braucht --app-id und --app-secret")
            exchange(a.exchange, a.app_id, a.app_secret)
        elif a.refresh:
            if not token:
                ap.error("--refresh braucht IG_ACCESS_TOKEN in der Umgebung")
            refresh(token)
        elif a.whoami:
            if not token:
                ap.error("--whoami braucht IG_ACCESS_TOKEN in der Umgebung")
            whoami(token)
        else:
            ap.print_help()
    except GraphError as e:
        print(f"\nGraph-API meldet:\n  {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
