#!/usr/bin/env python3
"""Build a self-contained contact sheet for the story-video image gate.

The sheet embeds every image as a data URI, so it opens from a bare file path
with no local HTTP server, no relative-asset resolution, and no markdown-image
support. OpenCode desktop can show it directly through `browser.preview`.

Usage:
    python3 scripts/contact_sheet.py build review/sheet.json review/PILOT-SHEET.html \
        --record review/PILOT-REVIEW.md

Manifest (relative image paths resolve against the manifest's own folder):
    {
      "title": "画面基准 · 候选对照",
      "subtitle": "人物锚点每个角色选一个候选；pilot 镜头确认通过或要改。",
      "groups": [
        {
          "id": "P01",
          "name": "雨夜宫门",
          "note": "pilot 镜头",
          "candidates": [
            {"id": "", "images": [{"path": "images/p01.png", "label": "P01"}]}
          ]
        },
        {
          "id": "C1",
          "name": "胤礽 · 太子",
          "note": "二十岁，石青常服",
          "candidates": [
            {
              "id": "A",
              "images": [
                {"path": "characters/candidates/yinreng-a-face.png", "label": "脸"},
                {"path": "characters/candidates/yinreng-a-body.png", "label": "全身"}
              ],
              "note": "眼神更稳"
            },
            {"id": "B", "images": ["characters/candidates/yinreng-b-face.png"]}
          ]
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import struct
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".avif": "image/avif",
}

DEFAULT_SUBTITLE = (
    "人物锚点每个角色选一个候选（A/B/C）；pilot 镜头确认「通过」或「要改」。"
)

CSS = """
:root {
  color-scheme: dark;
  --bg: #121212;
  --panel: #1b1b1b;
  --line: #2e2e2e;
  --text: #ececec;
  --muted: #9a9a9a;
  --accent: #e8b45a;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px;
  background: var(--bg);
  color: var(--text);
  font: 15px/1.55 "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
}
header.page { max-width: 1600px; margin: 0 auto 28px; }
h1 { margin: 0 0 8px; font-size: 25px; letter-spacing: .02em; }
.subtitle { margin: 0 0 10px; color: var(--muted); }
.meta { margin: 0; color: var(--muted); font-size: 13px; }
section.group {
  max-width: 1600px;
  margin: 0 auto 30px;
  padding: 18px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
}
.group-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px; margin-bottom: 14px; }
.group-head h2 { margin: 0; font-size: 18px; }
.gid {
  display: inline-block;
  padding: 2px 8px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
}
.group-note { margin: 0; color: var(--muted); font-size: 13px; }
.cands { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
figure.cand {
  margin: 0;
  padding: 12px;
  background: #161616;
  border: 1px solid var(--line);
  border-radius: 10px;
}
figure.cand.chosen { border-color: var(--accent); }
.cand-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; min-height: 28px; }
.badge {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  color: #161616;
  font-weight: 800;
}
.cand-note { color: var(--muted); font-size: 13px; }
.imgs { display: grid; gap: 8px; }
figure.shot { margin: 0; }
figure.shot img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 6px;
  background: #0a0a0a;
}
figure.shot figcaption { margin-top: 4px; color: var(--muted); font-size: 12px; }
figure.shot .dims { color: #6f6f6f; }
footer.page { max-width: 1600px; margin: 8px auto 0; color: #6f6f6f; font-size: 12px; }
"""


def fail(message: str) -> None:
    print(f"contact_sheet: {message}", file=sys.stderr)
    raise SystemExit(2)


def image_size(data: bytes, suffix: str) -> tuple[int, int] | None:
    """Read pixel dimensions from the file header without Pillow."""
    try:
        if suffix == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n":
            width, height = struct.unpack(">II", data[16:24])
            return int(width), int(height)
        if suffix == ".gif" and data[:6] in (b"GIF87a", b"GIF89a"):
            width, height = struct.unpack("<HH", data[6:10])
            return int(width), int(height)
        if suffix in (".jpg", ".jpeg") and data[:2] == b"\xff\xd8":
            index = 2
            while index + 9 < len(data):
                if data[index] != 0xFF:
                    index += 1
                    continue
                marker = data[index + 1]
                if marker in (0xD8, 0xD9):
                    index += 2
                    continue
                segment_length = struct.unpack(">H", data[index + 2:index + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    height, width = struct.unpack(">HH", data[index + 5:index + 9])
                    return int(width), int(height)
                index += 2 + segment_length
        if suffix == ".webp" and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            kind = data[12:16]
            if kind == b"VP8X":
                width = 1 + int.from_bytes(data[24:27], "little")
                height = 1 + int.from_bytes(data[27:30], "little")
                return width, height
            if kind == b"VP8 ":
                width, height = struct.unpack("<HH", data[26:30])
                return int(width) & 0x3FFF, int(height) & 0x3FFF
            if kind == b"VP8L":
                bits = int.from_bytes(data[21:25], "little")
                width = (bits & 0x3FFF) + 1
                height = ((bits >> 14) & 0x3FFF) + 1
                return width, height
    except (IndexError, struct.error):
        return None
    return None


def normalize_image(entry: Any, manifest_dir: Path) -> dict[str, Any]:
    if isinstance(entry, str):
        raw_path, label = entry, ""
    elif isinstance(entry, dict):
        raw_path = entry.get("path")
        label = str(entry.get("label") or "")
    else:
        fail(f"image entry must be a path string or an object, got {type(entry).__name__}")
    if not isinstance(raw_path, str) or not raw_path.strip():
        fail("image entry is missing a path")

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = manifest_dir / path
    path = path.resolve()
    if not path.is_file():
        fail(f"image not found: {path}")

    suffix = path.suffix.lower()
    mime = IMAGE_SUFFIXES.get(suffix)
    if mime is None:
        fail(f"unsupported image type: {path} (allowed: {', '.join(sorted(IMAGE_SUFFIXES))})")

    data = path.read_bytes()
    dimensions = image_size(data, suffix)
    return {
        "path": path,
        "raw": raw_path,
        "label": label,
        "mime": mime,
        "data": data,
        "dimensions": dimensions,
    }


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"manifest not found: {manifest_path}")
    except json.JSONDecodeError as error:
        fail(f"manifest is not valid JSON: {error}")
    if not isinstance(manifest, dict):
        fail("manifest must be a JSON object")

    groups = manifest.get("groups")
    if not isinstance(groups, list) or not groups:
        fail("manifest needs a non-empty 'groups' list")

    normalized_groups = []
    for group_index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            fail(f"group {group_index} must be an object")
        name = str(group.get("name") or "").strip()
        if not name:
            fail(f"group {group_index} is missing a name")
        candidates = group.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            fail(f"group {name!r} needs a non-empty 'candidates' list")

        normalized_candidates = []
        for candidate_index, candidate in enumerate(candidates, start=1):
            if not isinstance(candidate, dict):
                fail(f"group {name!r} candidate {candidate_index} must be an object")
            images = candidate.get("images")
            if not isinstance(images, list) or not images:
                fail(f"group {name!r} candidate {candidate_index} needs images")
            normalized_candidates.append({
                "id": str(candidate.get("id") or "").strip(),
                "note": str(candidate.get("note") or "").strip(),
                "images": [normalize_image(entry, manifest_path.parent) for entry in images],
            })

        normalized_groups.append({
            "id": str(group.get("id") or "").strip(),
            "name": name,
            "note": str(group.get("note") or "").strip(),
            "candidates": normalized_candidates,
        })

    return {
        "title": str(manifest.get("title") or "画面基准 · 候选对照").strip(),
        "subtitle": str(manifest.get("subtitle") or DEFAULT_SUBTITLE).strip(),
        "groups": normalized_groups,
    }


def render_html(sheet: dict[str, Any]) -> str:
    groups = sheet["groups"]
    image_count = sum(len(candidate["images"]) for group in groups for candidate in group["candidates"])
    parts = [
        "<!doctype html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(sheet['title'])}</title>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        '<header class="page">',
        f"<h1>{html.escape(sheet['title'])}</h1>",
        f'<p class="subtitle">{html.escape(sheet["subtitle"])}</p>',
        f'<p class="meta">{len(groups)} 组 · {image_count} 张图 · 图片已内嵌，可离线查看</p>',
        "</header>",
    ]

    for group in groups:
        parts.append('<section class="group">')
        parts.append('<div class="group-head">')
        if group["id"]:
            parts.append(f'<span class="gid">{html.escape(group["id"])}</span>')
        parts.append(f"<h2>{html.escape(group['name'])}</h2>")
        if group["note"]:
            parts.append(f'<p class="group-note">{html.escape(group["note"])}</p>')
        parts.append("</div>")
        parts.append('<div class="cands">')
        for candidate in group["candidates"]:
            parts.append('<figure class="cand">')
            parts.append('<div class="cand-head">')
            if candidate["id"]:
                parts.append(f'<span class="badge">{html.escape(candidate["id"])}</span>')
            if candidate["note"]:
                parts.append(f'<span class="cand-note">{html.escape(candidate["note"])}</span>')
            parts.append("</div>")
            parts.append('<div class="imgs">')
            for image in candidate["images"]:
                encoded = base64.b64encode(image["data"]).decode("ascii")
                alt = image["label"] or Path(image["raw"]).name
                parts.append('<figure class="shot">')
                parts.append(
                    f'<img src="data:{image["mime"]};base64,{encoded}" '
                    f'alt="{html.escape(alt, quote=True)}">'
                )
                caption = html.escape(image["label"] or Path(image["raw"]).name)
                if image["dimensions"]:
                    width, height = image["dimensions"]
                    caption += f' <span class="dims">{width}×{height}</span>'
                parts.append(f"<figcaption>{caption}</figcaption>")
                parts.append("</figure>")
            parts.append("</div>")
            parts.append("</figure>")
        parts.append("</div>")
        parts.append("</section>")

    parts.append('<footer class="page">contact_sheet.py · 每张图与候选字母一一对应，选字母即锁定。</footer>')
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def render_record(sheet: dict[str, Any], sheet_path: Path) -> str:
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        f"# {sheet['title']}",
        "",
        f"- 接触表：`{sheet_path}`",
        f"- 生成时间：{now}",
        "- 选法：每个角色选一个候选字母（A/B/C）；pilot 镜头回「通过」或「要改」。",
        "",
    ]
    for group in sheet["groups"]:
        heading = f"{group['id']} · {group['name']}" if group["id"] else group["name"]
        lines.extend([f"## {heading}", ""])
        if group["note"]:
            lines.extend([group["note"], ""])
        lines.extend(["| 候选 | 图片 | 备注 |", "|---|---|---|"])
        for candidate in group["candidates"]:
            files = "；".join(f"`{image['raw']}`" for image in candidate["images"])
            lines.append(
                f"| {candidate['id'] or '—'} | {files} | {candidate['note'] or ''} |"
            )
        lines.append("")
        if len(group["candidates"]) > 1:
            letters = " / ".join(c["id"] for c in group["candidates"] if c["id"])
            lines.append(f"选定：待选（{letters}）")
        else:
            lines.append("选定：待确认（通过 / 要改）")
        lines.append("")
    return "\n".join(lines)


def build(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    sheet = load_manifest(manifest_path)
    html_text = render_html(sheet)

    out_path = Path(args.out).expanduser()
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"WROTE {out_path.resolve()} ({len(html_text):,} bytes)")

    if args.record:
        record_path = Path(args.record).expanduser()
        if not record_path.is_absolute():
            record_path = Path.cwd() / record_path
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(render_record(sheet, out_path), encoding="utf-8")
        print(f"RECORD {record_path.resolve()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a self-contained contact sheet for the image gate.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="build the HTML sheet")
    build_parser.add_argument("manifest", help="JSON manifest describing groups and candidates")
    build_parser.add_argument("out", help="output HTML path (self-contained)")
    build_parser.add_argument("--record", help="also write a Markdown candidate record")
    build_parser.set_defaults(func=build)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
