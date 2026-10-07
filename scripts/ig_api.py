#!/usr/bin/env python3
"""Gemeinsame Hilfen für die direkte Instagram-Graph-API-Brücke.

Kein Drittanbieter, keine Abhängigkeiten ausser der Standardbibliothek.
Zugangsdaten kommen aus Umgebungsvariablen:

    IG_USER_ID        numerische ID des Instagram-Profikontos
    IG_ACCESS_TOKEN   langlebiges Zugriffstoken (60 Tage)
    GRAPH_VERSION     optional, Standard v23.0
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com"


def version() -> str:
    return os.environ.get("GRAPH_VERSION", "v23.0")


class GraphError(RuntimeError):
    """Fehler, den die Graph-API selbst gemeldet hat."""


def call(path: str, params: dict, method: str = "GET", token: str | None = None) -> dict:
    """Ein Aufruf gegen die Graph-API. Gibt das geparste JSON zurück."""
    params = {k: v for k, v in params.items() if v is not None}
    if token:
        params["access_token"] = token
    url = f"{GRAPH}/{version()}/{path.lstrip('/')}"
    data = None
    if method == "POST":
        data = urllib.parse.urlencode(params).encode()
    else:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body)["error"]
            raise GraphError(
                f"{err.get('type','HTTPError')} {err.get('code','')}: {err.get('message','')}"
                + (f"\n  Hinweis: {err['error_user_msg']}" if "error_user_msg" in err else "")
            ) from None
        except (ValueError, KeyError):
            raise GraphError(f"HTTP {e.code}: {body[:400]}") from None


def credentials() -> tuple[str, str]:
    """Liest IG_USER_ID und IG_ACCESS_TOKEN, mit verständlichem Fehler."""
    uid = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    missing = [n for n, v in (("IG_USER_ID", uid), ("IG_ACCESS_TOKEN", token)) if not v]
    if missing:
        raise SystemExit(
            "Fehlende Umgebungsvariablen: " + ", ".join(missing) + "\n"
            "In den Einstellungen der Cloud-Umgebung als Secret hinterlegen.\n"
            "IG_USER_ID findest du mit:  python3 scripts/ig_token.py --whoami"
        )
    return uid, token
