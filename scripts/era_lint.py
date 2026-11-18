#!/usr/bin/env python3
"""Lint image prompts for dynasty slips before an image batch is spent.

Two checks run here: the costume triad for Qing (hat shape, hair, robe) and a
density warning for frames that would collapse into a single object on a black
field. Both catch prompts that are wrong before any image is paid for.

Image models default to Ming/Song when a prompt only says "清代" or "古装":
the hat comes back as a black gauze cap, the hair as a topknot, the robe as a
cross-collar daopao. That failure is invisible at thumbnail size and only shows
up after the batch is paid for, so the costume has to be checked in the prompt,
not in the picture.

Usage:
    python3 scripts/era_lint.py images/prompts --era qing
    python3 scripts/era_lint.py --prompts-dir images/prompts -e qing --strict
    python3 scripts/era_lint.py IMAGE_PROMPTS.md --era qing

Exit code 0 = clean, 1 = fatal findings, 2 = usage/IO error.
"""
import argparse
import re
import sys
from pathlib import Path

# A prompt that contains one of these either shows a person or a worn garment.
PERSON = re.compile(
    r"人|官|臣|帝|皇|妃|嫔|太监|侍卫|差役|兵|卒|仆|婢|书生|士人|商|百姓|"
    r"女子|妇人|夫人|姑娘|老妇|孩童|幼儿|僧|道|背影|身影|人影|剪影|侧影"
)

# Hat / head-wear evidence that the costume is Qing. Shape words beat rank words:
# "顶戴花翎" alone is often rendered as a Ming cap, a cone plus a red tassel is not.
HAT = re.compile(
    r"暖帽|凉帽|顶戴|花翎|顶珠|红缨|官帽|瓜皮帽|旗头|大拉翅|两把头|"
    r"圆锥形帽|锥形帽|帽檐上翻|覆钵形帽|毡帽|风帽|斗笠"
)
HAIR = re.compile(r"剃发|剃光|辫子|发辫|长辫|辫梢|无发髻|额前无发|阴阳头")
# Mandarin robe markers. A person in official dress needs at least one.
ROBE = re.compile(
    r"补服|补褂|补子|马蹄袖|朝珠|披领|箭袖|常服袍|朝服|蟒袍|龙袍|"
    r"圆领对襟|马褂|长衫|氅衣|衬衣"
)

FATAL = [
    ("乌纱", "明代乌纱帽"),
    ("展角", "明代展角幞头"),
    ("幞头", "唐宋幞头"),
    ("梁冠", "明代梁冠"),
    ("束发", "明代束发"),
    ("发髻", "发髻（清代男子前额剃光）"),
    ("道袍", "明代道袍"),
    ("直身", "明代直身"),
    ("深衣", "汉制深衣"),
    ("交领右衽", "汉制交领"),
]
WARN = [
    ("古装", "空锚点，模型会回落到明代/宋代"),
    ("古代服饰", "空锚点"),
    ("顶戴花翎", "只有等级词、没有帽型，模型常画成乌纱帽"),
]

# Shots with no person in frame are exempt from the costume check.
NO_PERSON = re.compile(r"无人物|画面无人|空镜|no people in frame")

# Depth evidence: a frame with one subject on a black field reads as a flat card.
SPACE = re.compile(
    r"前景|中景|背景|近处|远处|身后|两旁人|两旁|两侧|角落|地面|墙上|窗外|"
    r"廊下|案边|画面上缘|下缘|床帐|帷帐|屏风|门框|窗棂|书架|宫灯|栏杆"
)


# Object+剪影 compounds are not a person; strip them before the person test.
NORMALISE = [("书架剪影", "书架"), ("树影", "树"), ("灯影", "灯"), ("窗影", "窗")]


def lint(text: str, era: str, density: bool = True):
    fatal, warn = [], []
    for a, b in NORMALISE:
        text = text.replace(a, b)
    has_person = bool(PERSON.search(text)) and not NO_PERSON.search(text)

    for word, why in FATAL:
        if word in text:
            fatal.append(f"禁用词「{word}」：{why}")
    for word, why in WARN:
        if word in text:
            warn.append(f"可疑词「{word}」：{why}")

    if density and not SPACE.search(text):
        warn.append("没写空间层次（前景/中景/背景、窗外、廊下、屏风…），容易压成单层静物")
    if density and len(text) < 60:
        warn.append("提示词过短，陈设与空气感不够，画面容易单薄")

    if era == "qing" and has_person:
        if not HAT.search(text):
            fatal.append("有人物但没写帽型（暖帽/凉帽/顶珠/红缨/瓜皮帽/旗头）")
        if not HAIR.search(text):
            fatal.append("有人物但没写发式（剃发留辫/前额剃光/无发髻）")
        if not ROBE.search(text):
            fatal.append("有人物但没写袍式（补服/马蹄袖/朝珠/长衫/氅衣）")
    return fatal, warn, has_person


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="prompt files or a directory of them")
    ap.add_argument("--prompts-dir", default=None)
    ap.add_argument("--era", "-e", default="qing", choices=["qing", "other", "none"])
    ap.add_argument("--strict", action="store_true", help="treat warnings as fatal")
    ap.add_argument("--no-density", action="store_true", help="skip the picture-density warnings")
    a = ap.parse_args()

    targets = []
    for p in a.paths:
        q = Path(p)
        if q.is_dir():
            targets += sorted(q.glob("*.txt"))
        elif q.exists():
            targets.append(q)
    if a.prompts_dir:
        targets += sorted(Path(a.prompts_dir).glob("*.txt"))
    if not targets:
        print("no prompt files found", file=sys.stderr)
        return 2

    bad = 0
    for f in targets:
        text = f.read_text(encoding="utf-8")
        fatal, warn, has_person = lint(text, a.era, density=not a.no_density)
        if a.strict:
            fatal, warn = fatal + warn, []
        if fatal:
            bad += 1
            print(f"[FAIL] {f.name}")
            for m in fatal:
                print(f"       - {m}")
        elif warn:
            print(f"[warn] {f.name}")
            for m in warn:
                print(f"       - {m}")
    print(f"\n{len(targets)} prompts, {bad} failing, era={a.era}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
