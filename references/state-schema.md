# Project state contract

`PROJECT_STATE.json` is the single source for workflow position. It is not a log of secrets or a substitute for the actual artifacts.

## Required top-level fields

```json
{
  "schema_version": 1,
  "project_id": "slug-or-uuid",
  "title": "Human-readable title",
  "project_root": "/absolute/project/path",
  "host": {
    "name": "dsh|codex|workbuddy|other",
    "capabilities": {
      "local_files": true,
      "attachments": true,
      "shell": true,
      "model_routing": false,
      "logged_in_browser": false,
      "tts": false,
      "image_generation": false,
      "hyperframes": false,
      "render": false
    }
  },
  "current_stage": "START",
  "stage_status": "进行中",
  "pending_request": "Choose 全自动 or 我来选 for this project.",
  "next_stage": "BRIEF",
  "decisions": {},
  "artifacts": {},
  "stage_history": [],
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

All nine capability keys are required and must be booleans. `attachments` covers packaging and opening files with the user; `shell` covers running local scripts such as the state CLI, HyperFrames and the render step.

## Allowed stages

`START`, `BRIEF`, `BENCHMARKS`, `WRITING_PACK`, `SCRIPT`, `VOICE`, `STORYBOARD`, `VISUAL_STYLE`, `CHARACTER_ANCHORS`, `IMAGE_PROMPTS`, `IMAGE_GENERATION`, `ASSET_QC`, `MUSIC`, `PREVIEW`, `FINAL_RENDER`, `FEEDBACK`.

## Allowed statuses

`未开始`, `进行中`, `待确认`, `已确认`, `需要返工`, `已跳过`.

Delivery acceptance is a separate axis and never goes into `stage_status`: `未做`, `已做待验`, `已验收` live in `decisions.delivery_status`.

## Update rules

1. Update state after creating a material artifact, reaching a gate, receiving a gate decision, or changing hosts.
2. Before entering a stage, append the prior stage result to `stage_history` with timestamp and artifact paths.
3. `pending_request` must name the one current user action. It must not contain the full future checklist.
4. Store decisions as facts with source and status, for example:

```json
"decisions": {
  "run_mode": { "value": "全自动", "source": "user", "status": "已确认" },
  "services": {
    "image": { "provider": "qwen-image", "endpoint": "http://host:30021", "key_ref": "env:IMAGE_API_KEY", "model": "qwen-image-2.1", "max_resolution": "1088x1920", "reference_input": false, "status": "已确认" },
    "audio": { "provider": "edge-tts", "endpoint": "builtin", "key_ref": null, "status": "已确认" }
  },
  "fidelity": { "value": "平衡", "source": "skill", "status": "已确认" },
  "aspect_ratio": { "value": "9:16", "source": "user", "status": "已确认" },
  "delivery_status": { "value": "已做待验", "source": "self", "status": "进行中" }
}
```

`key_ref` is a pointer to the local secret store, never the secret. Valid forms: `env:NAME`, `file:~/.story-video/secrets.env#NAME`, or `host:<credential-id>`. A null `key_ref` means the provider needs no key (edge-tts).

5. Artifact paths must be absolute inside `PROJECT_STATE.json`. Public deliverables must not expose private paths.
6. Never store plaintext API keys, cookies, login URLs, redemption codes, or tokens. Store services as `{provider, endpoint, key_ref, status}`; the key itself lives only in the local secret store.
7. When returning to an earlier stage, do not delete downstream artifacts. Mark them in `artifacts` as `stale: true` until regenerated or re-confirmed.
8. `全自动` mode still records the evidence for each self-checked gate in `stage_history` or the stage artifact; a gate passed without a record is not passed.
9. Moving the project folder invalidates the absolute `project_root`. Fix it with `repair <state-file>`; do not hand-edit the path and leave other absolute artifact paths stale.

## Resume behavior

On resume:

1. Validate the state file with `scripts/project_state.py validate`.
2. If it reports a `project_root` mismatch, run `scripts/project_state.py repair <state-file>` instead of giving up on the project.
3. Confirm that the latest required artifact still exists.
4. Tell the user the latest confirmed gate and the single pending request.
5. Continue from `current_stage`; do not repeat already confirmed questions.

## Validation rules

`validate` fails on:

- a missing or unknown top-level key;
- `schema_version` that is not the integer `1` (booleans are rejected);
- a stage or status outside the allowed lists;
- a non-absolute `project_root`, or one that does not match the state file's folder (use `repair`);
- a capability map missing a key, carrying an unknown key, or holding a non-boolean value;
- `created_at` / `updated_at` that is not a parseable ISO-8601 timestamp;
- `decisions` / `artifacts` that are not objects, or a `stage_history` entry that is not an object.

## Delivery status mapping

- No material artifact: `未做`.
- Artifact exists but the user has not accepted the relevant gate: `已做待验`.
- User accepted the final master: `已验收`.
