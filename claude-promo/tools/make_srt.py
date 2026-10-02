"""Export the SUBS table in index.html as bilingual SRT subtitles.

    python3 tools/make_srt.py > narration.srt
"""
import json
import pathlib
import re

src = (pathlib.Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
block = re.search(r"const SUBS = \[(.*?)\n\];", src, re.S).group(1)
rows = [json.loads("[" + line.strip().rstrip(",")[1:-1] + "]") for line in block.strip().splitlines()]


def ts(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


for i, (a, b, zh, en) in enumerate(rows, 1):
    print(f"{i}\n{ts(a)} --> {ts(b)}\n{zh}\n{en}\n")
