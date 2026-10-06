#!/usr/bin/env python3
"""Scaffold a post folder: content/posts/<slug>/{spec.json,caption.md,meta.json}.

Usage: new_post.py <slug> [--kind post|square|story|reel_cover]
"""
import json, sys, pathlib, datetime, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--kind", default="post",
                    choices=["post", "square", "story", "reel_cover"])
    a = ap.parse_args()

    brand = json.loads((ROOT / "brand.json").read_text())
    d = ROOT / "content" / "posts" / a.slug
    if d.exists():
        sys.exit(f"exists: {d}")
    d.mkdir(parents=True)

    (d / "spec.json").write_text(json.dumps({
        "kind": a.kind,
        "kicker": "",
        "headline": "",
        "footer": f"@{brand['handle']}",
        "bg": brand["visual"]["bg"],
        "accent": brand["visual"]["accent"],
        "photo": ""
    }, indent=2, ensure_ascii=False) + "\n")

    (d / "caption.md").write_text("<!-- Hook (max 2 Zeilen) -->\n\n\n<!-- Body -->\n\n\n<!-- CTA -->\n"
                                  + brand["caption"]["cta"] + "\n\n<!-- Hashtags -->\n"
                                  + " ".join(brand["caption"]["hashtags"]) + "\n")

    (d / "meta.json").write_text(json.dumps({
        "slug": a.slug,
        "created": datetime.date.today().isoformat(),
        "status": "draft",
        "instagram_type": "POST" if a.kind in ("post", "square") else "STORY",
        "scheduled_for": None,
        "media_url": None,
        "metricool_post_id": None,
        "isAiGenerated": False
    }, indent=2) + "\n")

    print(d)

if __name__ == "__main__":
    main()
