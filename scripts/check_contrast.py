"""Check WCAG contrast for the light and dark token sets in frontend/src/styles.css.

Composites translucent backgrounds over the surface they sit on, then reports the
contrast ratio of every foreground/background pair the UI actually uses.
"""
from __future__ import annotations

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "styles.css"


def parse_tokens() -> dict[str, dict[str, str]]:
    text = CSS.read_text(encoding="utf-8")
    blocks: dict[str, dict[str, str]] = {}
    for name, pattern in (
        ("light", r":root\s*\{(.*?)\}"),
        ("dark", r'\[data-theme="dark"\]\s*\{(.*?)\}'),
    ):
        m = re.search(pattern, text, re.S)
        if not m:
            raise SystemExit(f"block not found: {name}")
        tokens = {}
        for decl in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", m.group(1)):
            tokens[decl[0]] = decl[1].strip()
        blocks[name] = tokens
    return blocks


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def composite(fg: tuple[int, int, int], bg: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
    return tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg))


def luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for raw in rgb:
        c = raw / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def resolve(tokens: dict[str, str], name: str) -> tuple[int, int, int]:
    value = tokens[name]
    if value.startswith("rgba"):
        nums = [float(x) for x in re.findall(r"[\d.]+", value)]
        return (round(nums[0]), round(nums[1]), round(nums[2])), nums[3]
    return hex_rgb(value)


def main() -> int:
    blocks = parse_tokens()
    failures = []
    for theme, tokens in blocks.items():
        surface = hex_rgb(tokens["surface"])
        print(f"\n=== {theme} ===")
        pairs = [
            ("body text", "text", "bg", 4.5),
            ("muted text on surface", "muted", "surface", 4.5),
            ("muted text on bg", "muted", "bg", 4.5),
            ("accent on surface", "accent", "surface", 4.5),
            ("on-accent on accent", "on-accent", "accent", 4.5),
        ]
        for band in ("low", "medium", "high"):
            pairs.append((f"badge {band}", band, f"{band}-bg", 4.5))
            pairs.append((f"bandbar {band}", band, f"{band}-bg", 4.5))
        for label, fg_name, bg_name, need in pairs:
            fg = resolve(tokens, fg_name)
            if isinstance(fg, tuple) and len(fg) == 2:
                fg = composite(fg[0], surface, fg[1])
            bg = resolve(tokens, bg_name)
            if isinstance(bg, tuple) and len(bg) == 2:
                bg = composite(bg[0], surface, bg[1])
            r = ratio(fg, bg)
            ok = r >= need
            print(f"  {'PASS' if ok else 'FAIL'}  {label:24s} {r:5.2f}:1  (needs {need})")
            if not ok:
                failures.append(f"{theme}: {label} = {r:.2f}:1 (needs {need})")
    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  - " + f)
        return 1
    print("All checked pairs meet WCAG AA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
