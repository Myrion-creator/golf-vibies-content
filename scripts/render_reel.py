#!/usr/bin/env python3
"""Build a 9:16 Reel from three rendered frames.

Usage: render_reel.py spec.json out.mp4
Spec: {"frames": [ {spec for render_post.mjs}, ... ]}
"""
import json, subprocess, sys, pathlib, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FFMPEG = "/usr/bin/ffmpeg"
SEG, XF = 3.5, 0.5          # Sekunden pro Bild, Länge der Überblendung

def main():
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text())
    out = pathlib.Path(sys.argv[2])
    frames = spec["frames"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        segs = []
        for i, f in enumerate(frames):
            f = {**f, "kind": "story", "layout": "center"}
            sp = tmp / f"f{i}.json"; sp.write_text(json.dumps(f, ensure_ascii=False))
            png = tmp / f"f{i}.png"
            subprocess.run(["node", str(ROOT/"scripts"/"render_post.mjs"), str(sp), str(png)],
                           check=True, capture_output=True)
            seg = tmp / f"s{i}.mp4"
            # langsamer Zoom, damit das Bild nicht tot steht
            subprocess.run([FFMPEG, "-y", "-loop", "1", "-i", str(png), "-t", str(SEG),
                "-vf", f"zoompan=z='min(zoom+0.0009,1.09)':d={int(SEG*30)}:s=1080x1920:fps=30,format=yuv420p",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", str(seg)],
                check=True, capture_output=True)
            segs.append(seg)

        # Überblenden
        inputs, fc, last = [], [], None
        for i, s in enumerate(segs):
            inputs += ["-i", str(s)]
        for i in range(1, len(segs)):
            a = last or "0:v"
            off = SEG*i - XF*i
            lbl = f"x{i}"
            fc.append(f"[{a}][{i}:v]xfade=transition=fade:duration={XF}:offset={off}[{lbl}]")
            last = lbl
        total = SEG*len(segs) - XF*(len(segs)-1)
        cmd = [FFMPEG, "-y", *inputs,
               "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-filter_complex", ";".join(fc),
               "-map", f"[{last}]", "-map", f"{len(segs)}:a",
               "-t", str(total), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "128k",
               "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True, capture_output=True)
    print(f"{out}  {total:.1f}s")

if __name__ == "__main__":
    main()
