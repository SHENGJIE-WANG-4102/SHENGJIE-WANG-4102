"""Download Google Fonts subsets containing only the glyphs used by index.html.

Writes fonts/*.woff2 and fonts/fonts.css so the page renders the same offline.
Re-run after changing any on-screen text.
"""
import pathlib
import re
import string
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "fonts"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

FAMILIES = [
    ("Inter Tight", "wght@400;500;600;700;800;900"),
    ("Noto Sans SC", "wght@400;500;700;900"),
    ("JetBrains Mono", "wght@400;500;700"),
]


def page_chars() -> str:
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    # JS strings use \uXXXX escapes for curly quotes; decode them too.
    extra = "".join(chr(int(h, 16)) for h in re.findall(r"\\u([0-9a-fA-F]{4})", src))
    chars = set(src) | set(extra) | set(string.printable.strip()) | set("“”‘’—–→·…▶−×≈✓● ")
    return "".join(sorted(c for c in chars if c.isprintable()))


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.woff2"):
        old.unlink()
    text = page_chars()
    css_out = []
    for family, axes in FAMILIES:
        q = urllib.parse.urlencode({"family": f"{family}:{axes}", "text": text, "display": "block"})
        css = get(f"https://fonts.googleapis.com/css2?{q}").decode()
        # Variable fonts come back as the same file for every weight: keep one
        # file per (style, content) and declare it with a weight range.
        faces: dict[tuple[str, bytes], list[int]] = {}
        for block in re.findall(r"@font-face\s*{[^}]*}", css):
            style = re.search(r"font-style:\s*(\w+)", block).group(1)
            weight = int(re.search(r"font-weight:\s*(\d+)", block).group(1))
            url = re.search(r"url\((https://[^)]+)\)", block).group(1)
            faces.setdefault((style, get(url)), []).append(weight)
        slug = family.lower().replace(" ", "-")
        for (style, data), weights in faces.items():
            lo, hi = min(weights), max(weights)
            name = f"{slug}-{lo}{'-' + str(hi) if hi != lo else ''}{'i' if style == 'italic' else ''}.woff2"
            (OUT / name).write_bytes(data)
            wdesc = f"{lo} {hi}" if hi != lo else str(lo)
            css_out.append(
                "@font-face { font-family: '%s'; font-style: %s; font-weight: %s; font-display: block; src: url('%s') format('woff2'); }"
                % (family, style, wdesc, name)
            )
            print(f"{name:40s} {len(data) // 1024:5d} KB")
    (OUT / "fonts.css").write_text("\n".join(css_out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
