---
name: story-video-pipeline
description: 'Use when a user wants step-by-step help making an audio-first image-story, AI narration, slideshow, illustrated story, AI 讲书, 图片联播, 有声故事, or 静态图叙事视频 with DeepSeek Harness or OpenCode (WorkBuddy for front-end stages) — including the quick path where they give only a topic and a target duration: first asks 全自动 or 我来选 with clickable options (never typed codes), asks once for the image-generation and voice-generation addresses and keys in the opening Q&A, then delivers researched materials and a complete script plus a 45–60 s narration sample (选题→文案→配音→分镜→出图→装配→成片, stage-gated); not for a standalone script, single image, or ordinary video editing.'
---

# Story Video Pipeline（image-story-video-wizard 分支）

Own the process. The user supplies the current decision or material; the Skill decides what must happen next, performs everything it can, and asks only where the chosen run mode requires an answer.

## Interaction: clickable choices, not typed codes

When a decision is needed, use the host's interactive question tool — in DeepSeek Harness that is `ask_user_question` — with 2–5 concrete options. Put the default first and mark it `（推荐）`; add one line on the tradeoff. The user clicks or types a short answer; never ask them to reply in the chat with `1A 2B` codes, and never present a plain-text form as the only way to choose.

- Keep the status line to one sentence: `第 3 步 · 文稿与样音`, then the action or the question. Do not recite a five-part status script every turn.
- One round holds at most three questions. Group related decisions; three rounds at the start is the ceiling (services, creative, voice).
- Infer everything reversible — platform, subtitles on, duration inside ±10% — instead of asking.
- Never ask “接下来想做什么”, and never make the user pick a workflow stage.
- A question that does not block the current step waits.

Use these stage statuses exactly: `未开始`, `进行中`, `待确认`, `已确认`, `需要返工`, `已跳过`. Confirm in batches (see Confirmation batches), not stage by stage.

## Preview: a channel the operator can actually see

A preview is a capability, not a formatting choice. Before the first gate, pick and verify the channel that actually puts the file in front of the operator, and record it as `decisions.preview_channel`:

| Host | Channel value | How |
|---|---|---|
| OpenCode desktop | `review_pane` | `browser.preview({ path: "<absolute path>" })` opens images, HTML, audio, and video in the Review pane. Preferred: no local server and no markdown-image support needed. |
| DeepSeek Harness web | `inline_images` | Serve the project with `python3 -m http.server <port> --bind 127.0.0.1 --directory <project>`, check one URL returns `200`, then embed `![](http://127.0.0.1:<port>/...)` in a tool-free reply. |
| Other hosts | `attachment` / `local_browser` | Attach the file to the message, or open the HTML with the OS default browser (`xdg-open`). |

- A bare local path is not a preview. The model's own `read` of an image proves the model can see it, not the operator.
- On DSH, a reply that also carries a tool call can lose its text and images — measured 2026-11-12: markdown images plus `ask_user_question` in one message rendered nothing, while the same images in a tool-free reply were visible. Post the images in a tool-free reply, end the turn, and ask on the next turn.
- If the operator reports seeing nothing, the gate has not happened. Switch to the next channel and show the artifact again; never repeat the same question over an unseen sheet.
- The same channel carries the voice auditions and the assembled preview.

## Start or resume

On first use, detect whether this is a new project or a resumed one. Look for `PROJECT_STATE.json` in the supplied project folder. If none exists, initialize one with the bundled script, called by its full path from the skill folder, and keep the project folder outside this vault so generated media never enters the knowledge base:

```
python3 <skill-dir>/scripts/project_state.py init <project-folder> --title "<title>" --host dsh
```

If a state file exists, validate it, summarize the latest confirmed artifact, and resume at `pending_request`; do not restart from the beginning. If the project folder was moved, `repair <state-file>` rewrites `project_root` to the current location instead of leaving the file permanently invalid.

At stage 0, identify the actual host and capabilities. Read [references/host-routing.md](references/host-routing.md) when choosing between DeepSeek Harness, OpenCode, WorkBuddy, or a handoff. Never claim a host can access local files, call a model, use a logged-in browser, synthesize audio, or render unless that capability is available now. Identify which preview channel can actually show a generated file to the operator (`review_pane`, `inline_images`, `attachment`, `local_browser`) and record it as `decisions.preview_channel`; the image gate is unanswerable on a channel the operator cannot see. Probe both generation channels once to see what is already configured, then open with the service Q&A below — in both run modes the address and key are asked in the first exchange.

Read [references/workflow.md](references/workflow.md) before starting a project and whenever entering a new stage. Read [references/state-schema.md](references/state-schema.md) before creating or changing project state.

## Model services: address + key, asked in the first exchange

The first exchange collects both generation channels before any production, in both run modes. Ask one `ask_user_question` call with three questions — image channel, audio channel, run mode. For the two service questions **pass no options**: with an empty option list the answer field is the interface, and the user types the address and key there as `地址 | key` (e.g. `https://relay.example.com/v1 | sk-…`). The question body names the built-in URL and shows that template:

- **生图（默认）**：`阿里云 MaaS · qwen-image-2.1-turbo（推荐，内置地址 https://maas.qianwenaiapi.com/compatible-mode/v1）`；其余选项 `OpenAI 兼容（gpt-image / DALL·E）`、`ComfyUI（自建）`、`自定义 / 中转地址`。
- **音频（默认）**：`小米 MiMo TTS · mimo-v2.5-tts（推荐，内置地址 https://api.xiaomimimo.com/v1；token-plan key 用 https://token-plan-cn.xiaomimimo.com/v1）`；其余选项 `edge-tts（免地址、免 key）`、`Azure Speech`、`ElevenLabs`、`OpenAI TTS`、`MiniMax / 火山`、`自定义 / 中转地址`。

**The answer field is the only input path.** The address and the key are typed into the question — no clickable preset can stand in for them. Never ask the user to edit `~/.story-video/secrets.env`, `PROJECT_STATE.json`, a `.env` file, or any other file by hand, and never end the exchange by telling them to send the values some other way. The Skill writes the secret store itself; the user's only action is typing into the question. If the answer comes back empty or without an address or key, re-ask the same text-only question once, shorter, for the missing field.

The address is always asked, never silently defaulted: every option carries its built-in URL, and the answer may replace it with a public endpoint, a private/self-hosted one (`http://192.168.x.x:port/v1`, internal DNS, reverse-proxy path), or a relay. Private addresses are first-class: accept plain `http`, IP literals, ports, path prefixes, and self-signed TLS; never rewrite the URL to a public one and never require HTTPS. A self-hosted service may legitimately have no key — offer `无 key（私网自建）` and do not invent one.

The key is asked in the same answer; when the environment or the host's secret store already holds one, name it in the question (`env:IMAGE_API_KEY 已检测到，回这个变量名即可`) and accept that name as the answer. Ask for the auth scheme only when the service is not OpenAI-compatible (Bearer vs `api-key` vs query token); the secret itself is taken once. If the provider needs a region, account id, or model name, ask for it in the same round. When an answer arrives without the address or key, re-ask the same text-only question once for the missing field.

Probe from the host that will actually call the API, not from the user's browser: `localhost` / `127.0.0.1` means that generation host, and a LAN address must be reachable from it (same network or VPN). Verification is mandatory and blocking: no production step starts on an unverified channel. Classify the failure before re-asking — transport error or timeout means the address or the network is wrong; `401` / `403` or a missing-key message means the key is wrong even though the host answered; `404` means the path or base URL is wrong. Re-ask only the failing field, quoting the provider's own error text, and leave the other channel's confirmed values alone. If a private probe fails, report the transport error, ask whether the host is on the right network or VPN, and keep the address unchanged — never substitute a public endpoint. For self-signed TLS, retry with certificate verification disabled and treat a TLS-only failure as reachability confirmed.

Collect the key once through the question's answer field. The Skill then writes it to a local secret file outside the project (`~/.story-video/secrets.env`, owner-only permissions) — that write is the Skill's own step, never something the user does. Keep only a `key_ref` in `PROJECT_STATE.json`; never echo the key back, and never write it to prompts, project artifacts, logs, screenshots, or Git. Verify each channel with one cheap probe; if the probe fails, report the provider's own error and ask for a corrected address, key, or provider.

Record `decisions.services.image` and `decisions.services.audio` as `{provider, endpoint, key_ref, status}` with `source: "user"` for address and key — never the key itself. A resumed project uses the recorded services and does not re-ask unless the user asks to change one.

## Run mode: ask once, then obey it

Read the request first. If it already carries a topic, a duration, and a format, the brief is settled; the opening round settles only the services and who decides.

Ask this as the third question of the opening round: `全自动`（推荐，除两条通道的地址与 key 外我替你定全部）or `我来选`（开始前把要定的都摆出来）. It rides with the service questions, never with production work.

- `全自动`: after the opening round settles the two channel addresses and keys, the Skill makes every remaining choice — fidelity, voice rate, aspect, visual style, music, subtitles, cadence — records each with `source: "skill"`, then runs START → FINAL_RENDER. It stops at most three times: the opening round, the voice-audition pick, and the pilot image set. It interrupts only for a failing channel probe, a fact that changes the output and cannot be verified, or publish authorization. Every gate becomes a recorded self-check in `review/` and `stage_history`. Between those stops the run never idles: each finished step starts the next one in the same reply, and a reply that reports progress without a question or a gate is a stalled run, not a checkpoint — keep going until a stop is actually reached.
- `我来选`: before any production, ask the choices in three clickable rounds. Round S is the opening exchange: 生图地址 + key、音频地址 + key、运行模式. Round A: 史实尺度（正史向 / 平衡 / 戏说）, 画幅（9:16 / 16:9）, 视觉风格（电影写实 / 国画工笔 / 连环画 / 给参考图）, 图片节奏（10–12 秒 / 6–8 秒）. Round B: 音色（5–10 个 15 秒试听）, 语速（舒缓 / 标准 / 明快）, 配乐（无 / 轻铺底）. Then run; the only later stops are 文稿+样音, 画面基准, 预览, 成片, each asking only that stop's verdict — 画面基准 also collects one candidate letter per recurring character.

Record `decisions.run_mode` as `全自动` or `我来选`, and record each channel's address and key_ref plus fidelity, voice, rate, aspect, style, cadence, music, subtitles, and `preview_channel` with source and status. A resumed project keeps the recorded mode and answers; never re-ask them.

**Output aspect ratio** is part of the config, default `9:16` (1080×1920 vertical — phone-first feeds like Douyin), with `16:9` (1920×1080 horizontal) as the alternative. Record it as `decisions.aspect_ratio` and set the canvas and image aspect from it before IMAGE_GENERATION; never switch aspect mid-project — changing it later reworks every generated image and the whole layout.

## Start: two channels and the run mode in the first exchange

Do not consume the whole pipeline in one turn.

1. **First exchange — catch both channels and the mode.** Open one `ask_user_question` call with three questions: 生图通道（地址 + key）、音频通道（地址 + key）、运行模式（`全自动` / `我来选`）. The two service questions carry no options, so the user types `地址 | key` into the answer field. No research, no writing pack, no draft, no synthesis, and no instruction for the user to edit files.
2. **Record what came back.** Write each key to `~/.story-video/secrets.env`, record `{provider, endpoint, key_ref, status}` in `decisions.services`, and probe both channels once from the host that will call them (private address: check LAN/VPN reachability; self-signed TLS allowed). A failed probe asks only for the corrected address, key, or provider.
3. **If `全自动`** — record every remaining default with `source: "skill"` and run the next step. No creative questions — except the voice: generate the 15-second auditions for 5–10 voices as soon as the TTS probe passes, serve the clips, and ask one click question to pick a voice (default first). The Skill never picks a voice on the operator's behalf, in any mode.
4. **If `我来选`** — generate the 15-second voice auditions, then ask Round A and Round B as clickable questions. Do not start production until both rounds are answered.
5. **Then the first production step** — research + writing pack + one complete first draft + the narration sample (45–60 seconds, TTS input run through `audio/PRONUNCIATION.md`). In `我来选` this waits for a 通过/要改 question; in `全自动` it is self-checked and recorded, then the run continues.

The narration sample is 45–60 seconds, not the 15-second audition. The 15-second clip exists only to choose a voice.

## Quick path: topic + duration → script

When the opening request is only a topic and a target duration (for example "九子夺嫡, 10 minutes"), do not interview for the brief. Ask only the opening service-and-mode round — the topic plus duration already confirms direction.

- **`全自动`**: the opening round already settled both channel addresses and keys; infer every reversible default (audience, platform, language, 9:16), pick at least two benchmark candidates with reasons, choose fidelity, voice, rate, and style, record each with `source: "skill"`, then run research → writing pack → script → sample without further questions.
- **`我来选`**: the opening round settles both channel addresses, keys, and the mode; generate the 15-second auditions, then ask Round A/B before production. Rejecting a benchmark or brief default sends the direction back to BENCHMARKS/BRIEF.
- **First production step**: research the available scope (library files when present, plus bounded public read-only search), write the facts list and source index into `writing-pack/03-MATERIALS.md`, build the cast table into `writing-pack/04-CAST.md`, deliver one complete first draft, and synthesize the 45–60 s narration sample (TTS input per `audio/PRONUNCIATION.md`). Mark what could not be verified as a gap; never invent facts, names, dates, or citations.
- **After the sample passes** (clicked in `我来选`, self-checked and recorded in `全自动`): synthesize the remaining narration, then run the stages in the selected mode. Quick path never waives separate publish authorization.

## Stage order and hard gates

Follow this state machine:

`START → BRIEF → BENCHMARKS → WRITING_PACK → SCRIPT → VOICE → STORYBOARD → VISUAL_STYLE → CHARACTER_ANCHORS → IMAGE_PROMPTS → IMAGE_GENERATION → ASSET_QC → MUSIC → PREVIEW → FINAL_RENDER → FEEDBACK`

Hard gates:

- Do not generate a writing pack before product direction is confirmed. In quick path the topic plus duration confirms direction; a rejected benchmark or brief default returns the pack to BENCHMARKS.
- Do not synthesize full narration before the final script is confirmed. The 45–60 s sample is the pacing and pronunciation gate: in `我来选` it waits for a click; in `全自动` it is checked against duration, pronunciation map, and loudness, and the evidence is recorded before continuing.
- Do not write the complete image-prompt manifest before image cadence and visual style are confirmed.
- Do not batch-generate images before the user confirms the three-to-five-image pilot and any required character anchors. This is the one image gate; it applies in both run modes. After it passes, individual images never go back to the user.
- Do not render a final video before the preview passes: the assembled preview is clicked through in `我来选`, frame-checked and recorded in `全自动`.
- Do not publish, upload, post, or change a live channel unless the user separately authorizes that action.

**One image gate, at the start.** The operator must see it. Generate the three-to-five pilot images and, for every recurring character, 2–3 anchor candidates. The anchor is the operator's decision: keep every candidate that passes the era and realism check, label them A/B/C, and let the operator pick one — never generate two, keep the "better" one, and show only that. An anchor candidate is a face plate plus a full-body plate generated as one coherent person, so the pick is not a face from one plate and a body from another.

Lay the pilot shots and anchor candidates out as one contact sheet with shot IDs and candidate letters. In a host with a Review pane, build a self-contained sheet and show it:

```
python3 <skill-dir>/scripts/contact_sheet.py build review/pilot-sheet.json review/PILOT-SHEET.html --record review/PILOT-REVIEW.md
browser.preview({ path: "<project>/review/PILOT-SHEET.html" })
```

On DSH or another host, deliver the same sheet through the channel recorded at START (see Preview). Do not call the gate answered until the operator confirms they saw the sheet or answers from it.

Then ask in rounds of at most three questions:

1. For each strict character, one clickable question with the candidate letters (`A` / `B` / `C`, default `A`). If more than three characters need a choice, continue in another round — never default an anchor the operator has not seen.
2. One `通过` / `要改` question for the pilot shots.

On `要改` or `都不要`, regenerate only the rejected rows and show the replacement set once; never reopen accepted rows. Record the chosen letters in `decisions.anchor_selection` and fill the selection lines in `review/PILOT-REVIEW.md`; copy the chosen pair to the stable `characters/{name}-face.png` / `characters/{name}-body.png` names later prompts use, keeping the rejected candidates under `characters/candidates/`.

After the set passes, the rest of the batch is autonomous: QC against `ERA_SPEC.md`, the frozen style, and the shot list, record the verdict in `review/IMAGE-QC.md`, replace failures without asking, and surface an image only when it cannot be fixed without a new capability or a fact decision.

Run mode effect: in `全自动` the opening service-and-mode round, the voice-audition pick, and the pilot/anchor set are the only three stops. The anchor choice is part of that stop in both modes — `全自动` never auto-picks an anchor. Every other mid-run gate is satisfied by recorded self-check evidence. In `我来选` every stop is one clickable 通过/要改 question; the voice rides in config Round B and the pilot gate is stop 2.

If a gate fails, mark `需要返工`, return only to the earliest affected stage, and preserve later artifacts as untrusted rather than deleting them.

## Confirmation batches

In `全自动` the stops are the opening service-and-mode round, the voice-audition pick, and the image pilot; the same coverage elsewhere is recorded as self-check evidence in `review/`. In `我来选` the stages collapse into five clickable stops — FEEDBACK sits outside them, running once real platform data exists. Between stops the Skill runs covered stages back-to-back and never asks “可以继续吗”. A reply that ends on a non-stop step with no question and no gate has stalled the run — resume the next step immediately instead of waiting to be prompted. The opening round both asks for and probes TTS and image generation; only a failed probe adds a question.

| 停靠 | 覆盖阶段 | 这一次定什么 |
|---|---|---|
| 0 配置（两种模式都停） | START → BRIEF → BENCHMARKS | 生图地址+key、音频地址+key、运行模式（全自动到此为止）；我来选再加史实尺度、画幅、视觉风格、图片节奏、音色、语速、配乐（三轮点击，开工前一次问完） |
| 0.5 音色试听（全自动也停） | START 后的 VOICE 预选 | 5–10 个 15 秒试听落盘、经预览通道交付，点选一个音色；我来选已在 0 轮 B 问过，不停 |
| 1 文稿+样音 | WRITING_PACK → SCRIPT → VOICE | 终稿 + 45–60 s 样音（通过/要改） |
| 2 画面基准（全自动也停） | STORYBOARD → VISUAL_STYLE → CHARACTER_ANCHORS | 看 3–5 张 pilot 与每个常驻人物的 2–3 个锚点候选，选 A/B/C 再点 通过/要改；通过后才写完整提示词清单、批量出图 |
| 3 预览 | IMAGE_PROMPTS → IMAGE_GENERATION → ASSET_QC → MUSIC → PREVIEW | 出图、QC、配乐全自动；只看装配好的预览（通过/要改） |
| 4 成片 | FINAL_RENDER | 成片验收；发布另一次授权 |

Rules:

- 每个停靠的提问合并成一次，最多三问，全部用可点选控件，默认项放第一。
- 硬门在批内即时生效，触碰即停，停靠点后半段不提前执行。
- 批次内已确认的阶段标 `已确认`，一次点击批量落状态；缺输入的阶段不标。
- pilot 与人物锚点是唯一一次图片确认；通过后单张图、QC 替换不再进停靠，也不再问用户。

## Execution: small steps and refusal recovery

Never let one long generation carry several artifacts. Each model step produces at most one artifact (or one small group), writes it to disk immediately, then moves on; `PROJECT_STATE.json` changes get their own final small step after `validate` passes. The same discipline applies to whole replies: the exchange that asks for the services and run mode ends at that question, and the step that delivers the sample ends at the sample — each reply runs only the next step and never pre-spends later stages. **Small steps never mean pausing between them: after a step lands on disk, the very next action is starting the following step, in the same reply if capacity remains or by continuing the run — never a bare “progress report” reply that ends with nothing pending and waits to be prompted. A reply may end without a question only at a declared stop, a hard gate, a failed probe, or a fact decision. Stopping anywhere else is a stalled run; when the run resumes, pick up from the last artifact on disk, not from scratch.** A step that streams for minutes is fragile: a provider interruption — content filter, timeout, abort — discards the whole step, because uncommitted reasoning never reaches disk. The quick path's first exchange is assembled from files already on disk, not from one unwritten stream. This changes how work runs, never what is delivered: stops, batches, hard gates, and the delivery shapes above stay exactly as specified.

When a step ends in a provider refusal or mid-stream abort (`finish_reason: content_filter`, `PI_AI_ERROR`, or any interrupted stream):

1. Split that step smaller and retry once — the same content in shorter pieces usually passes.
2. If the refusal repeats on the same content, delegate only that step to a sub-agent routed to a different provider/model; instruct it to write the artifact file directly and report just the path plus a one-line verification. A sub-agent on the same model does not bypass the filter — switching models is the point; the isolation only keeps a failed step from taking the main conversation down.
3. Continue from the written artifact; never re-run steps that already landed on disk.

## Production invariants

### Script

- Learn a benchmark's topic logic, structure, pace, hooks, transitions, and audience need; never copy its original wording or finished assets.
- At WRITING_PACK and SCRIPT, read [writing and review](references/writing-and-review.md). Keep reusable writer rules, the current channel/language with selected examples, and episode materials separate inside one self-contained package.
- Require one complete first draft; do not pad for length. A complete but slightly short draft can be reviewed as-is. A hollow draft or missing necessary material calls for repairing the package, not decorative expansion.
- Complete means the story closes: cause to outcome, the opening question answered, every planted payoff collected by the ending. A missing ending or dangling main thread is a material gap (`需要返工` to WRITING_PACK), not a “slightly short” draft.
- Open straight into the story: the first lines carry the hook and the opening question. Do not open with a disclaimer section declaring which parts are 戏说 and which are 史实, and do not front-load any accuracy manifesto — the accuracy stance lives in BRIEF/MATERIALS and enters the narration at most as one light sentence woven into the telling, never as a standing block that delays the first scene.
- For historical or real-person subjects the pack carries a cast table (name, identity, 称谓 or 排行, rank or relationship, reign title when the subject has one, years). Verify every proper noun in the body against it before acceptance; wrong names, ranks, or reign titles are factual errors, not style preferences.
- The original guiding conversation gives a focused edit list; the chosen writer performs local repairs. Compare the returned text against the list, then stop for user acceptance. Large rewrites require a clear reason and user confirmation.

### Voice

- TTS credentials are settled in the opening service round. Prefer a key already in the environment or the host's secret store; if the chosen provider needs one and none is configured, take it once there and store it outside the project. Never repeat it in later messages.
- Compare five to ten voices with the same **15-second** sample. The clip exists only to choose timbre; it is not the pacing check. In `我来选` it rides in the config round. In `全自动` the Skill still synthesizes all 5–10 auditions, puts the clips into the conversation, and stops once for the operator to pick — it never silently chooses a voice; if the operator does not answer within the same session, default to the first voice, record `source: "skill" (defaulted)` and keep running.
- Pick speaking rate after the voice: 舒缓 / 标准 / 明快, mapped to the TTS engine's rate value and checked on a 30–60 s passage. Record the value, not just the label.
- The first TTS production step is a 45–60 s sample stitched from the opening paragraphs PLUS the mid-script paragraphs where the rare names cluster — never only the opening: a sample cut from the first three paragraphs alone leaves every middle-of-script name unheard, which is exactly how mid-video mispronunciations ship. In `我来选` it waits for the 通过/要改 click; in `全自动` it is checked for duration, pronunciation, and loudness, the evidence is written to `review/`, and the run continues. A resumed project with a confirmed script goes straight to this sample.
- Before synthesizing anything, build a pronunciation map for proper nouns the TTS is likely to misread (rare characters, polyphones, historical names such as 胤禛 / 胤礽 / 胤禩 / 胤禵): build it by scanning the **whole final script** for name tokens (`[胤允]` plus rare or polyphone characters, including renamed forms like 允禩) — every scanned token must land in the map or an explicit whitelist, keys must match the script's exact codepoints, and the uncovered-token diff is saved as evidence before full narration; never build the map from memory. Verify each substitute against a dictionary or authoritative source (胤禔 = zhī not tí; 胤祄 = jiè) — a plausible-looking substitute that is wrong is still a defect. Record the spoken substitute, apply it only to the TTS input, and keep the original characters in SCRIPT, subtitles, and text cards. Write the map to `audio/PRONUNCIATION.md` from `assets/pronunciation-map.md` so a re-synth or a host handoff keeps the same substitutions. Put every mapped name into the 15-second audition, and make the 45–60 s sample include the mid-script name-dense paragraphs so middle names are heard before full narration. A mispronounced name is a mapping defect, not a voice choice — fix the map, re-synth every affected segment, and re-run the token coverage diff; a name the audition never exposed stays a suspect until heard.
- Prefer narration output with sentence- or word-level timestamps when available.

### Storyboard and images

- Calculate image count from narration duration. A dynamic 6–8 second cadence means about 75–100 images per ten minutes; an economical 10–12 second cadence means about 50–60.
- Lock image style and text treatment with a three-to-five-image pilot and the character anchors before producing the full prompt manifest.
- Detect recurring characters. When identity continuity matters, generate 2–3 face-plus-full-body anchor candidates per strict character, verify each against `ERA_SPEC.md` before showing it, and put every candidate in the same contact sheet as the pilot shots. Show all candidates; the operator picks one per character. Never auto-pick.
- Show the pilot and anchor candidates as one contact sheet with shot IDs and candidate letters through the preview channel recorded at START — `browser.preview` in OpenCode desktop, inline images in DSH, attachment or local browser elsewhere. A bare path, a "sheet saved at…" line, or a file card alone is not a preview. Then ask the candidate letters and one `通过` / `要改` for the pilot. On `要改`, regenerate only the rejected rows and show the replacement set once; after the choices, never ask about individual images again. Self-check the batch against `ERA_SPEC.md` and the frozen style, record the result in `review/IMAGE-QC.md`, and replace failures automatically.
- Build every prompt with the [prompt recipes](assets/prompt-recipes.md) order: shot fact and count, framing, three planes (foreground / midground / background), a named light source with direction and color temperature, one or two atmosphere cues, two or three materials, capture, era anchors, no-text clause. A prompt that only names subject and style is incomplete.
- Realism is part of the style gate, not a post-process. Use the period-screen realism block in [prompt recipes](assets/prompt-recipes.md) and, for Qing, section 7 of [era accuracy](references/era-spec.md): natural skin with pores and fine lines, anatomically correct hands, a real hairline and weighted queue, fabric that wrinkles and shows wear, practical light, film grain. A plastic or CGI face, malformed hands, helmet-like hairline, or brand-new costume is a replacement-level defect; "historical enough" is not a pass when the person looks rendered.
- For Qing subjects, hold the screen baseline that a viewer recognises instantly: shaved forehead with a queue, court hat with finial, horse-hoof cuffs, court beads, rank badge, flag-head or two-hand-tied hair for women; daily dress is not full ceremonial yellow. State rank and occasion so the costume is not a generic "ancient Chinese" bundle.
- **Qing costume is written by shape, never by dynasty name.** `清代官员`, `顶戴花翎`, `古装` are weak anchors: image models default to Ming and return a black gauze cap with wing flaps, a topknot, and a cross-collar daopao. Every prompt that contains a person must name three shapes — hat (conical warm or rain hat, upturned brim, red tassel, finial), hair (shaved forehead, queue, no topknot), robe (round-collar front-opening surcoat, square rank badge, horse-hoof cuffs, court beads). Run `python3 scripts/era_lint.py <prompts-dir> --era qing` before the batch and do not spend on a failing set. A Ming hat is a replacement-level defect even on a background silhouette; "close enough for a transition shot" is how a whole act ends up in the wrong dynasty.
- **Screen identity beats costume purism.** The lead the audience must recognise — an emperor, a general, a pope — carries one instantly readable marker even in a quiet domestic scene (Qing emperor: imperial-yellow `常服` robe, east-pearl hat finial, yellow belt; a general: armour or a distinctive colour). A technically correct outfit that renders the protagonist in the same colour and silhouette as his ministers is a defect, not a period-accurate choice: colour and silhouette first, rank minutiae second. Check every scene with the lead against one question — "would a viewer who knows nothing pick him out in one second?"
- Respect the delivery quality floor: 9:16 at least 1280×2276, prefer 1440×2560; generate two candidates for each pilot shot and keep the better one by face, hands, and action; generate 2–3 candidates per character anchor and show them all for the operator to pick; inspect eyes, hands, and hairline at 100%. Prefer an image service with reference-image or img2img support for recurring characters. If the chosen service cannot reach the floor, name the missing capability before batch instead of producing a set that must be rejected.
- Lock count and action in the positive sentence (`no people in frame`, `one person only`, `exactly one child`). Negative lists are unreliable at CFG 1; do not rely on them to remove a person or restore an action.
- Keep the exposure guard: no more than two dark/low-key words, always a named key light plus `shadow detail, midtone separation`. Check the histogram at QC; a dark frame is a grade fix, a missing action or wrong count is a prompt fix.
- Keep prompt IDs, storyboard IDs, generated filenames, and narration ranges aligned.
- For historical subjects, produce `ERA_SPEC.md` per [era accuracy](references/era-spec.md) before pilot prompts, freeze it with the style, embed its era anchors and negative list in every prompt, and check every image against it at ASSET_QC. East–West mixed imagery is a replacement-level defect, not taste. Replace failures automatically; surface only unresolved capability or fact problems.

### Assembly and review

- Prefer HyperFrames for programmable assembly when available, but follow the confirmed project format and host capability.
- When actual assembly or rendering begins in an environment that provides the HyperFrames skills, load the `hyperframes` mandatory entry point and follow the routed core, media, animation, audio, and CLI instructions that apply to the confirmed project.
- Align images, subtitles, text cards, and optional music to narration timing.
- Produce a reviewable preview before final render. The user reviews the assembled video — pacing, subtitles, story — not individual images; in `全自动` inspect representative frames and record what was checked and what could not be.
- Keep delivery status `已做待验` until the user accepts the final master.

## Secrets and external actions

A key is accepted once in the opening service round and stored only in a local secret file outside the project. Never write a key, session URL, redemption code, cookie, or token into prompts, `PROJECT_STATE.json`, project artifacts, logs, screenshots, or repositories; record only `key_ref`. Redact it if it appears in command output. Never ask for the same key twice.

Model calls that spend money, browser actions using logged-in sessions, final rendering, uploads, and publishing must stay within the user's current authorization. Explain cost or account impact before the action when material.

## Project artifacts

Use stable filenames so the project can resume across hosts:

- `PROJECT_STATE.json`
- `BRIEF.md`
- `BENCHMARKS.md`
- `writing-pack/`
- `SCRIPT.md`
- `audio/`
- `audio/PRONUNCIATION.md`（发音替换表，按 `assets/pronunciation-map.md` 填）
- `STORYBOARD.csv`
- `VISUAL_STYLE.md`
- `ERA_SPEC.md`（历史题材，见 references/era-spec.md）
- `characters/`（候选在 `candidates/`，选定锚点用 `{name}-face.png` / `{name}-body.png`）
- `IMAGE_PROMPTS.md`
- `images/`
- `review/`（含 `PILOT-SHEET.html`、`PILOT-REVIEW.md`、`IMAGE-QC.md`）
- `renders/`
- `HANDOFF.md` when another host must continue

Use the templates in `assets/` when creating these artifacts. Validate `PROJECT_STATE.json` before claiming a stage is complete: `stage_status` only takes its six-value set, and delivery acceptance is recorded separately in `decisions.delivery_status` (`未做` / `已做待验` / `已验收`). Never put a key in this file; `services.*.key_ref` is a pointer, not a secret.

## Completion

Completion means the confirmed master and its resumable project files exist and pass the proportional checks in the workflow. Report the current state as `未做`, `已做待验`, or `已验收` in `decisions.delivery_status`; do not squeeze those three into `stage_status`. Do not call a workflow “automated” merely because one sample rendered; record manual intervention and real production time after several episodes.
