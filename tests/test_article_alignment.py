"""Structural checks that keep the skill aligned with its reference workflow."""

from __future__ import annotations

import base64
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FIVE_FIELDS = ("**Enter when:**", "**Skill acts:**", "**Ask now:**", "**Deliver:**", "**Gate:**")

GUIDED_LABELS = (
    "现在进行到：",
    "我现在会做：",
    "你现在只需要：",
    "完成后我会交付：",
    "确认后下一步：",
)

PUBLIC_FILES = (
    "SKILL.md",
    "README.md",
    "LICENSE",
    "agents/openai.yaml",
    "assets/brief-template.md",
    "assets/handoff-template.md",
    "assets/pronunciation-map.md",
    "assets/prompt-recipes.md",
    "assets/storyboard-template.csv",
    "assets/writing-pack-manifest.md",
    "assets/writer-rules.md",
    "references/workflow.md",
    "references/host-routing.md",
    "references/state-schema.md",
    "references/era-spec.md",
    "references/writing-and-review.md",
    "scripts/project_state.py",
    "scripts/contact_sheet.py",
    "docs/ARTICLE_ALIGNMENT.md",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load_state_module():
    path = ROOT / "scripts" / "project_state.py"
    spec = importlib.util.spec_from_file_location("project_state", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workflow_stages(text: str) -> list[str]:
    return re.findall(r"^## ([A-Z][A-Z_]+)\s*$", text, flags=re.MULTILINE)


def stage_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"^## ([A-Z][A-Z_]+)\s*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end():end]
    return sections


class StructureTests(unittest.TestCase):
    def test_public_files_exist(self):
        for relative in PUBLIC_FILES:
            self.assertTrue((ROOT / relative).is_file(), f"missing {relative}")

    def test_description_contract(self):
        skill = read("SKILL.md")
        description = re.search(r"^description: (.+)$", skill, flags=re.MULTILINE).group(1).strip().strip("'\"")
        self.assertTrue(description.startswith("Use when "), description)
        self.assertIn("DeepSeek Harness", description)
        self.assertIn("WorkBuddy", description)
        self.assertNotIn("modifiable fork", description)

    def test_clickable_interaction_contract(self):
        skill = read("SKILL.md")
        for token in ("ask_user_question", "全自动", "我来选", "15 秒", "45–60 s", "qwen-image", "secrets.env"):
            self.assertIn(token, skill, f"missing interaction token {token}")
        self.assertNotIn("一次性搞定", skill)
        self.assertNotIn("中间校验", skill)

    def test_service_address_and_key_asked_in_opening(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        readme = read("README.md")
        self.assertIn("address + key, asked in the first exchange", skill)
        self.assertIn("地址 + key", readme)
        self.assertIn("地址不静默默认", workflow)
        start = workflow.split("## START", 1)[1].split("## BRIEF", 1)[0]
        self.assertIn("address and key", start)
        self.assertIn("key_ref", start)
        self.assertIn("运行模式", start)

    def test_default_service_endpoints_and_models(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        readme = read("README.md")
        for text in (skill, workflow, readme):
            self.assertIn("qwen-image-2.1-turbo", text)
            self.assertIn("mimo-v2.5-tts", text)
            self.assertIn("https://maas.qianwenaiapi.com/compatible-mode/v1", text)
            self.assertIn("https://token-plan-cn.xiaomimimo.com/v1", text)

    def test_private_network_endpoints_supported(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        readme = read("README.md")
        self.assertIn("private/self-hosted", skill)
        self.assertIn("private/self-hosted", workflow)
        self.assertIn("self-signed", skill + workflow)
        self.assertIn("私网", readme)
        self.assertIn("无 key", readme)

    def test_one_image_gate_at_start(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        readme = read("README.md")
        self.assertIn("One image gate, at the start.", skill)
        self.assertIn("the user confirms the three-to-five-image pilot", skill)
        self.assertIn("pilot 与人物锚点是唯一一次图片确认", skill)
        self.assertIn("PILOT-REVIEW", workflow)
        self.assertIn("pilot 与人物锚点是唯一一次图片确认", readme)
        self.assertNotIn("No user image review", skill)
        self.assertNotIn("never asked to approve images", skill)

    def test_prompt_recipes_require_layers_and_counts(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        recipes = read("assets/prompt-recipes.md")
        self.assertIn("assets/prompt-recipes.md", skill)
        self.assertIn("prompt-recipes.md", workflow)
        self.assertIn("Foreground", recipes)
        self.assertIn("one person only", recipes)
        self.assertIn("no people in frame", recipes)
        self.assertIn("CFG 1", recipes)
        self.assertIn("Period screen realism", recipes)
        self.assertIn("plastic skin", recipes)
        self.assertIn("Realism is part of the style gate", skill)
        self.assertIn("1280×2276", skill)
        self.assertIn("delivery quality floor", skill.lower())
        self.assertIn("Prestige period-drama look", recipes)
        self.assertIn("1280×2276", recipes)
        self.assertIn("two candidates", recipes)
        self.assertIn("屏幕写实与真人感", read("references/era-spec.md"))
        self.assertIn("六指", read("references/era-spec.md"))

    def test_stage_sequence_matches_workflow(self):
        module = load_state_module()
        stages = workflow_stages(read("references/workflow.md"))
        self.assertEqual(len(stages), 16, stages)
        self.assertEqual(stages, list(module.STAGES))
        self.assertEqual(stages[-1], "FEEDBACK")
        self.assertIn("FINAL_RENDER", stages)

    def test_every_stage_has_five_fields(self):
        sections = stage_sections(read("references/workflow.md"))
        self.assertEqual(len(sections), 16)
        for stage, body in sections.items():
            for field in FIVE_FIELDS:
                self.assertIn(field, body, f"{stage} missing {field}")

    def test_run_mode_section_covers_both_modes(self):
        workflow = read("references/workflow.md")
        self.assertIn("## 运行模式", workflow)
        self.assertIn("全自动", workflow)
        self.assertIn("我来选", workflow)
        self.assertNotIn("一次性搞定", workflow)
        section = workflow.split("## 运行模式", 1)[1].split("## 批次确认", 1)[0]
        self.assertIn("FINAL_RENDER", section)
        self.assertIn("SCRIPT-REVIEW", section)
        self.assertIn("delivery_status", workflow)
        self.assertIn("aspect_ratio", read("SKILL.md"))

    def test_quick_path_states_stop_count(self):
        workflow = read("references/workflow.md")
        readme = read("README.md")
        self.assertIn("0 配置", workflow)
        self.assertIn("0 配置", readme)
        self.assertIn("2 画面基准", workflow)
        self.assertIn("2 画面基准", readme)
        self.assertIn("4 成片", workflow)
        self.assertIn("4 成片", readme)
        self.assertNotIn("7 次回复", workflow)

    def test_execution_resilience_contract(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        readme = read("README.md")
        self.assertIn("content_filter", skill)
        self.assertIn("sub-agent", skill)
        self.assertIn("执行韧性", workflow)
        self.assertIn("小步执行与中断恢复", readme)

    def test_readme_install_route(self):
        readme = read("README.md")
        for required in (
            "一句话安装",
            "story-video-pipeline",
            "image-story-video-wizard",
            ".claude/skills/story-video-pipeline",
        ):
            self.assertIn(required, readme)

    def test_host_routing_contract(self):
        routing = read("references/host-routing.md")
        for token in ("DeepSeek Harness", "WorkBuddy", "Kimi K3", "1M", "attachments", "shell"):
            self.assertIn(token, routing, token)
        self.assertIn("HANDOFF.md", routing)

    def test_preview_channel_contract(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        routing = read("references/host-routing.md")
        readme = read("README.md")
        for text in (skill, workflow):
            self.assertIn("preview_channel", text)
            self.assertIn("browser.preview", text)
        self.assertIn("review_pane", skill)
        self.assertIn("OpenCode", routing)
        self.assertIn("browser.preview", routing)
        self.assertIn("[browser.disconnected]", routing)
        self.assertIn("预览通道", readme)
        self.assertIn("inline_images", routing)

    def test_character_anchor_candidates_selected_by_user(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        readme = read("README.md")
        routing = read("references/host-routing.md")
        self.assertIn("2–3 anchor candidates", skill)
        self.assertIn("preview_channel", routing)
        self.assertIn("decisions.anchor_selection", skill)
        self.assertIn("anchor_selection", workflow)
        self.assertIn("characters/candidates/", skill)
        self.assertIn("PILOT-SHEET.html", skill)
        self.assertIn("PILOT-SHEET.html", workflow)
        for text in (skill, workflow, readme):
            self.assertIn("contact_sheet.py", text)
        self.assertIn("A/B/C", readme)
        self.assertIn("2–3", workflow)

    def test_contact_sheet_builds_self_contained_sheet(self):
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "images").mkdir()
            (project / "characters" / "candidates").mkdir(parents=True)
            (project / "images" / "p01.png").write_bytes(png)
            (project / "characters" / "candidates" / "a-face.png").write_bytes(png)
            (project / "characters" / "candidates" / "b-face.png").write_bytes(png)
            manifest = {
                "title": "画面基准",
                "groups": [
                    {
                        "id": "P01",
                        "name": "雨夜宫门",
                        "candidates": [
                            {"id": "", "images": [{"path": "images/p01.png", "label": "P01"}]}
                        ],
                    },
                    {
                        "id": "C1",
                        "name": "胤礽",
                        "candidates": [
                            {"id": "A", "images": ["characters/candidates/a-face.png"]},
                            {"id": "B", "images": ["characters/candidates/b-face.png"]},
                        ],
                    },
                ],
            }
            (project / "sheet.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "contact_sheet.py"),
                    "build",
                    str(project / "sheet.json"),
                    str(project / "review" / "PILOT-SHEET.html"),
                    "--record",
                    str(project / "review" / "PILOT-REVIEW.md"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WROTE", result.stdout)
            sheet = (project / "review" / "PILOT-SHEET.html").read_text(encoding="utf-8")
            self.assertIn("data:image/png;base64", sheet)
            self.assertIn("1×1", sheet)
            self.assertIn("P01", sheet)
            self.assertIn('class="badge">A<', sheet)
            self.assertIn('class="badge">B<', sheet)
            record = (project / "review" / "PILOT-REVIEW.md").read_text(encoding="utf-8")
            self.assertIn("选定：待选（A / B）", record)
            self.assertIn("选定：待确认（通过 / 要改）", record)

    def test_craft_rules_are_actionable(self):
        skill = read("SKILL.md")
        workflow = read("references/workflow.md")
        self.assertIn("mapping defect", skill)
        self.assertIn("5–10", workflow)
        self.assertIn("three-to-five", workflow)
        self.assertIn("±10%", read("assets/writing-pack-manifest.md"))
        self.assertIn("ERA_SPEC", read("references/era-spec.md"))

    def test_state_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            script = ROOT / "scripts" / "project_state.py"
            init = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "init",
                    str(project),
                    "--title",
                    "九子夺嫡",
                    "--host",
                    "dsh",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            state = project / "PROJECT_STATE.json"
            self.assertTrue(state.is_file())

            validate = subprocess.run(
                [sys.executable, str(script), "validate", str(state)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("VALID", validate.stdout)

            again = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "init",
                    str(project),
                    "--title",
                    "九子夺嫡",
                    "--host",
                    "dsh",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(again.returncode, 2)


if __name__ == "__main__":
    unittest.main()
