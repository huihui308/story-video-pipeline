# Guided workflow contracts

Use only the current stage section in user-facing interaction. The full sequence belongs to the Skill, not to the user.

Each stage has five fields:

- **Enter when:** required prior gate.
- **Skill acts:** work performed without asking the user to manage it.
- **Ask now:** only the minimum current input.
- **Deliver:** artifact that proves the stage work happened.
- **Gate:** what must be locked before the next stage. Real stops are the batch ends and the hard gates below; every other stage's gate rolls into its stop and is answered once.

## 运行模式（Run mode）

读需求后，第一条回复用一条问答收三件：生图通道（地址 + key）、音频通道（地址 + key）、运行模式（`全自动` 推荐 / `我来选`）。两个服务问题**不带选项**，答案输入框就是入口，用户填 `地址 | key`；由技能取出后写入项目外密钥文件——不要让用户改 `secrets.env`、状态文件或任何配置。模式、两条通道与预览通道（`preview_channel`）写入 `decisions`，续跑沿用，不重问。两条路径共用硬门与不变式，模式只改变「谁来定、谁来确认」。

START 先探两条生成通道的状态；问题里点明环境已有的 key，但不给点选项——答案输入框是唯一入口。地址不静默默认，问题正文给内置 URL，用户可改自建或中转；实际地址与 key 由用户填 `地址 | key` 给出。**每条通道都要实测一次，验证不过不开工**：连不上是地址/网络问题，401/403 或「缺少 key」是 key 不对，404 是路径不对；只把出错那一项带着服务端原文再问一次，另一条已验过的值不动。地址与密钥是能力问题，开场问答不算创作轮。

- **`全自动`**：开场问答只收两条通道的地址与 key 和运行模式；史实尺度、语速、画幅、视觉风格、配乐、字幕、节奏由技能定并逐项记 `source: "skill"`；音色例外——开场探活通过后仍生成 5–10 个 15 秒试听、经预览通道交付让操作者点选（不回答则取第一个，记 `source: "skill" (defaulted)`）。START 连到 FINAL_RENDER，只保留三个停靠：开场问答、音色试听、开头 pilot 与人物锚点候选；其余各门自检并把依据写进 `review/` 与 `stage_history`。只在探活失败、事实无法核验、发布授权时打断。停靠之间连续推进，任何阶段落盘后立即开下一步，不发「进度汇报后原地等提示」的回复。
- **`我来选`**：开工前三轮点击问完配置，之后才生产。S 轮就是首条回复：生图地址 + key、音频地址 + key、运行模式。A 轮：史实尺度（正史向/平衡/戏说）、画幅（9:16/16:9）、视觉风格（电影写实/国画工笔/连环画/给参考图）、图片节奏（10–12 秒/6–8 秒）。B 轮：音色（5–10 个 15 秒试听）、语速（舒缓/标准/明快）、配乐（无/轻铺底）。连同 0 配置共五个停靠。

中途硬门在两种模式下都要留证，缺证据等于没过门：

| 硬门 | 证据落在哪 |
|---|---|
| 终稿 | `review/SCRIPT-REVIEW.md` 与差异核对结论 |
| 音色与语速（45–60 秒样音） | `audio/` 试听集、样音、选定记录、发音表；试听集两种模式都点选（0.5 停靠），样音我来选等点击、全自动自检 |
| pilot 与人物锚点 | pilot 图、`VISUAL_STYLE.md`、`characters/candidates/` 的 2–3 个候选、`review/PILOT-SHEET.html`、`review/PILOT-REVIEW.md` 的选定字母与通过记录；两种模式都等用户点击 |
| 预览 | 预览文件、结构检查；我来选看装配好的视频，全自动记抽帧检查结论 |

**图片只在开头验收一次，而且操作者必须真的看得到。** 生成 3–5 张 pilot，以及每个常驻人物的 2–3 个锚点候选（面部 + 全身同一人，A/B/C 标号，通过 `ERA_SPEC.md` 与写实检查的候选全部保留，不替用户挑「更好的那个」）。用 `scripts/contact_sheet.py` 拼成带 shot ID 与候选字母的接触表，存 `review/PILOT-SHEET.html`，然后通过 START 记录的预览通道交付：OpenCode 桌面用 `browser.preview`，DSH 用本地 http 服务 + 内联图，其他宿主用附件或本机浏览器。**路径、文件卡片、「已存到 review/…」都不算预览。** 先问每个严格人物选 A/B/C（最多三问一轮，超过三个角色续一轮），再问一次 pilot 的 `通过` / `要改`；`要改` 或 `都不要` 只重出被拒的行，并只展示替换后的那一组。选定字母写 `decisions.anchor_selection` 与 `review/PILOT-REVIEW.md`，选定面/全身图复制成稳定文件名 `characters/{name}-face.png` / `{name}-body.png`，被拒候选留在 `characters/candidates/`。通过后，单张图、QC 替换、批量出图都不再向用户提问；技能按 `ERA_SPEC.md`、冻结风格与分镜自检，结论写 `review/IMAGE-QC.md`，失败自动重出。只有装配好的预览与最终成片再交给用户。

## 批次确认（Confirmation batches）

16 个阶段收敛为：全自动 3 个（0 配置、0.5 音色试听、2 画面基准）；我来选 5 个（0 配置、1 文稿+样音、2 画面基准、3 预览、4 成片）。FEEDBACK 要等真实平台数据，不在停靠内，交付后异步。停靠之间连续执行，不逐阶段问「可以继续吗」，也不在停靠之外的步骤后停下等提示——阶段落盘即进下一步。开场问答同时探明 TTS 与出图通道，探活失败才补问。

| 停靠 | 覆盖阶段 | 定什么 |
|---|---|---|
| 0 配置（两种模式都停） | START → BRIEF → BENCHMARKS | 生图地址+key、音频地址+key、运行模式（全自动到此为止）；我来选再加史实尺度、画幅、视觉风格、图片节奏、音色、语速、配乐（三轮点击，开工前一次问完） |
| 0.5 音色试听（全自动也停） | VOICE 预选 | 5–10 个 15 秒试听经预览通道交付，点选一个音色；我来选已在 0 轮 B 问过，不停 |
| 1 文稿+样音 | WRITING_PACK → SCRIPT → VOICE | 终稿 + 45–60 秒样音（通过/要改） |
| 2 画面基准（全自动也停） | STORYBOARD → VISUAL_STYLE → CHARACTER_ANCHORS | 看 3–5 张 pilot 与每个人物的 2–3 个锚点候选（选 A/B/C + 通过/要改）；通过后才写完整提示词清单 |
| 3 预览 | IMAGE_PROMPTS → IMAGE_GENERATION → ASSET_QC → MUSIC → PREVIEW | 出图、QC、配乐全自动；只看装配好的预览（通过/要改） |
| 4 成片 | FINAL_RENDER | 成片验收；发布另一次授权 |

各阶段 Gate 说明该阶段锁定什么；只有上表停靠点与硬门真正停下。非停靠阶段的 Gate 归并进所属停靠，一次答完；每停最多三问，全部可点选，默认项放第一；一次点击批量落该停靠内已答阶段的 `已确认`；硬门在批内即时生效，触碰即停。pilot 与锚点占停靠 2；批量后的 QC 不占停靠。

## 快速路径（主题 + 时长 → 剧本）

开场请求只有「主题 + 目标时长」时进入。只问开场问答（两条通道地址 + key、运行模式）；主题与时长本身已确认方向。

- **全自动**：开场已收两条通道的地址与 key；推断受众、平台、语言、`9:16` 等可逆默认值，自选至少两个对标并记理由，自定史实尺度、语速、风格，逐项记 `source: "skill"`；音色在探活通过后出 5–10 个试听点选（见 0.5 停靠），然后直接进入资料与写作。
- **我来选**：开场问答先定服务地址、key 与运行模式，再生成 15 秒试听，问 A/B 两轮；答案落盘后才开始生产。对标或简报默认值被否 → 退回 BRIEF/BENCHMARKS。
- **第一条生产消息**：资料检索（库内有则用 + 有限公开只读搜索）→ 事实清单与来源索引进 `writing-pack/03-MATERIALS.md`、人物表进 `writing-pack/04-CAST.md` → 一份完整初稿 → 45–60 秒样音（开头 + 中段专名最密段落拼接，不只取开头；TTS 按 `audio/PRONUNCIATION.md` 替换）。查不到的显式标缺口，不编事实、人名、年代、出处。
- **样音通过后**（我来选等点击，全自动自检）→ 合成剩余旁白，进入批次 2–4。快速路径不豁免发布授权。

## 执行韧性（小步执行与中断恢复）

拆步只改执行方式与节奏，停靠、批次与硬门照旧：快速路径第一条生产消息交初稿与样音；每条回复只跑下一步，不预支后面的阶段。**拆步不等于拆停：一个阶段落盘后立即开下一步，不允许发一条没有问题、没有硬门的「进度汇报」就原地等提示；只有停靠、硬门、探活失败、事实决策、发布授权可以让回复停在半路。停了就从盘上最后一个产物接着跑，不重跑已落盘的步骤。**

- 一次模型步骤最多产出一个小产物（单个文件或一组紧密文件），立刻落盘再进下一步；`PROJECT_STATE.json` 校验通过后单独一小步更新。连续流几分钟的步骤天然脆弱——内容过滤、超时、中断一来，没落盘的推理整段丢失。快速路径的首条交付由已落盘的文件拼装，不靠一段没写盘的长推理。
- 步骤以供应商拒绝或中途断流收尾时（`finish_reason: content_filter`、`PI_AI_ERROR` 或任何中断流）：先把这一步拆得更小重试一次；同样内容再触发，就把这一步交给换了 provider/model 的子代理，直接写文件、只回报路径和一行校验——同模型的子代理绕不过过滤器，换模型才是关键，隔离只是防止失败拖垮主对话。已落盘的步骤不重跑，从写好的产物继续。

## START

**Enter when:** the Skill is invoked.

**Skill acts:** locate or initialize `PROJECT_STATE.json`; inspect only the supplied project scope; identify host capabilities and existing artifacts — including which preview channel can actually put a generated image in front of the operator (`review_pane` for the OpenCode desktop Review pane via `browser.preview`, `inline_images` for the DSH web client, `attachment` or `local_browser` elsewhere) — and record it as `decisions.preview_channel`; classify new versus resumed work. Probe both channels once so an already-configured address and key can lead the options, then open with one clickable round that collects each channel's address and key (default image: 阿里云 MaaS `qwen-image-2.1-turbo` at `https://maas.qianwenaiapi.com/compatible-mode/v1`; default audio: 小米 MiMo TTS `mimo-v2.5-tts` at `https://api.xiaomimimo.com/v1`, token-plan keys at `https://token-plan-cn.xiaomimimo.com/v1`; alternatives: OpenAI 兼容 / ComfyUI / 自定义 for images, edge-tts / Azure / ElevenLabs / OpenAI / MiniMax / 自定义 for audio) together with the run mode. The address is always confirmed, never silently defaulted: the option carries the built-in URL, and a public, private/self-hosted, or relay URL can be typed in — plain http, LAN IP, internal DNS, port, path prefix, and self-signed TLS are all valid, and a self-hosted service may have no key. Probe from the host that will call the API, not from the user's browser; a failing private probe asks about LAN/VPN reachability instead of changing the address. Write each key to `~/.story-video/secrets.env` outside the project and record only `key_ref`. Record the image service profile with the probe: model, maximum resolution, and whether it accepts a reference image or img2img. Verify with one cheap probe.

**Ask now:** the opening round: 生图地址+key、音频地址+key、运行模式. The two service questions carry no options; the user types `地址 | key` into the answer field, and the Skill writes the secret file from that answer — never ask the user to edit a file. If undiscoverable, also ask for the project folder and whether this is new or continued work. Address, key, and run mode are capability questions, not creative ones.

**Deliver:** current-state summary, confirmed host and services, missing capability list, and first actionable request.

**Gate:** project root, resume point, both service channels (address + key_ref), the run mode, and `decisions.preview_channel` are recorded; a key exists only outside the project.（批次 0 配置 · 停靠）

## BRIEF

**Enter when:** START is confirmed.

**Skill acts:** turn the user's idea into a production brief: topic, audience, platform, target duration, language, release scope, and what success means for this sample. Narration is audio-first by design; the aspect ratio was already fixed at start with the run mode. A multi-narrator plan is outside this pipeline's flow and needs its own explicit decision before BRIEF continues. In quick path, infer every reversible default from the topic and duration and show them with the script stop instead of asking.

**Ask now:** ask at most three questions. Prefer: topic/audience, target platform/format, desired duration. Infer reversible defaults and show them for confirmation.

**Deliver:** `BRIEF.md` using `assets/brief-template.md`.

**Gate:** user confirms the brief. Channel creation, upload, or publishing is not included unless separately authorized.（批次 0 配置 · 并入停靠）

## BENCHMARKS

**Enter when:** BRIEF is confirmed.

**Skill acts:** first explain that benchmark selection will directly shape script quality and downstream presentation. Prioritize user-supplied benchmarks or selection criteria: ask for the accounts or works the user genuinely wants to learn from, or at least the direction and qualities they want screened. Analyze those materials when provided. Only when the user is unwilling or unable to provide either, perform a bounded public read-only search and return at least two benchmark candidates with clear reasons. Quick path (topic + duration only): run that search automatically without asking, and deliver the candidates as defaults at the script stop.

**Ask now:** ask the user for specific learning targets or concrete screening direction. Make clear that this is a high-impact decision, not routine material collection. If the user cannot or does not want to provide them, say that the Skill can search and recommend candidates instead. Do not silently choose a direction and continue. 全自动：自己选至少两个候选，写明理由，随剧本停靠一并交付。

**Deliver:** `BENCHMARKS.md` with source, role, evidence, learn/avoid decisions, recommendation, and rights boundary.

**Gate:** user carefully confirms benchmark roles after seeing the evidence and recommendation. Do not start WRITING_PACK before this decision; quick path exception: candidates are confirmed or rejected together with the script, and rejection returns here.（批次 0 配置 · 停靠点；快速路径并入剧本停靠） Learning never means copying exact wording, images, audio, or finished footage.

## WRITING_PACK

**Enter when:** BENCHMARKS is confirmed.

**Skill acts:** in quick path (and whenever the pack lacks facts), run a bounded research pass first — library scope plus public read-only search — and write the facts list with source index into `writing-pack/03-MATERIALS.md` and the cast table into `writing-pack/04-CAST.md`; mark unverified gaps, never invent material. Then read [writing and review](writing-and-review.md) and use `assets/writing-pack-manifest.md` to build one self-contained package with the reusable writer rules, only the current channel/language profile and selected examples, and the episode task/materials. Read the channel's existing feedback before selecting examples. Preserve source evidence and mark what may enter narration. Supply needed information and causal relationships instead of prewritten editorial metaphors, forced paragraph formulas, or numerical style quotas.

**Ask now:** ask only for source material that cannot be found in scope and one decision about the desired benchmark emphasis. Quick path: ask nothing — research, pack, and draft all ride the script stop.

**Deliver:** the populated writing package and manifest, as a merged file or archive with actual content. Record the package and channel-profile versions. Do not expose secrets or internal paths in public-facing materials.

**Gate:** user confirms the package direction, not every line of source material.（批次 1 · 并入停靠）

## SCRIPT

**Enter when:** WRITING_PACK is confirmed.

**Skill acts:** follow [writing and review](writing-and-review.md). Preserve the user's chosen writing model; when Kimi K3 is specified, use it if available or provide the user a self-contained handoff instead of silently substituting. Preserve one complete first draft. The original guiding conversation identifies concrete issues and protected passages, then provides one copyable, bounded edit list for the writer. When the revision returns, compare actual body changes with that list, check for new errors or damaged transitions, and stop after those issues are resolved; do not begin another general style review.

**Ask now:** use the already stated preferences to review the draft and prepare the edit list without asking the user to find all problems. Give the user the ready-to-forward instruction when the writer is in another conversation. Request a user decision only for a necessary scope change, missing fact, or final acceptance. Do not ask the user to redesign the workflow.

**Deliver:** preserved original body, `review/SCRIPT-REVIEW.md` with issues/actions/protected scope, the writer's complete revised `SCRIPT.md`, and a short result of the change comparison. Use fresh filenames if originals already exist. Keep counting and unresolved facts separate from narration, and record the user's actual feedback in the channel profile or project feedback file.

**Gate:** the user confirms the final script before marking it `已确认`. A complete but slightly short draft may be accepted without padding; a hollow draft or necessary material gap is `需要返工` and returns to WRITING_PACK. Large restructuring needs a specific reason and the user's decision. Do not perform second-round padding.（批次 1 · 停靠点·硬门：终稿与 45–60 秒样音；选声在配置轮，样音随稿交付；我来选等点击通过，全自动自检并记录时长/发音/响度，样音仍等用户确认）

## VOICE

**Enter when:** 终稿已确认；音色与语速已定（我来选在 B 轮点击；全自动在 0.5 停靠点选或默认第一个，选定记录在 `decisions.voice`）。

**Skill acts:** TTS 服务与 key 在开场问答定好；这里只验证可用性，不再索要密钥。用同一段约 15 秒文本生成 5–10 个音色试听，供配置轮点选；这 15 秒只用来选音色，不是样音。按 `assets/pronunciation-map.md` 建 `audio/PRONUNCIATION.md`：先全量扫描终稿里 `[胤允]`+生僻字的名字 token（含 允禩 这类改名写法），逐个入表或进白名单、key 与脚本 codepoint 一致，替换词按字典读音核验（胤禔 = zhī 不是 tí；胤祄 = jiè），未覆盖清单落盘当证据；易误读的专名给口语替换，只用于 TTS 输入，剧本/字幕/文字卡保留原字。音色定后用语速试听（30–60 秒）确认舒缓/标准/明快。然后合成约 45–60 秒样音（三到五段 = 开头 + 中段专名最密段落拼接，不只取开头），不合成整段。样音确认后合成剩余旁白，回读实测时长，与写作包估算差超过 ±10% 要报告。

**Ask now:** 我来选：音色与语速在配置轮点击，样音在文稿停靠点「通过/要改」；全自动：音色仍要点选——5–10 个 15 秒试听落盘后经预览通道交付，一次点击选一个（不回答则默认第一个并记 `source: "skill" (defaulted)`），语速按默认。

**Deliver:** 经预览通道交付的 15 秒试听集、45–60 秒样音、音色/语速记录、`audio/PRONUNCIATION.md`、整段旁白、实测时长对照、可用时的时间戳。

**Gate:** 样音通过后才合成整段（我来选等点击；全自动自检时长、发音、响度并留证）。模型或参数建议不算验收。

## STORYBOARD

**Enter when:** VOICE is confirmed.

**Skill acts:** use actual narration duration and timestamps to calculate image cadence and create `STORYBOARD.csv`. Each row includes shot ID, audio start/end, narration excerpt, visual intent, characters, text-card need, and status.

**Ask now:** present two concrete cadence options with real counts. Recommended default for a first audio-first project is 10–12 seconds per image; offer 6–8 seconds when the user wants faster visual motion and accepts more images. 全自动：取 10–12 秒默认值，记录张数，写进进度消息。

**Deliver:** complete storyboard and count summary.

**Gate:** cadence and count are fixed from the config round and recorded; no storyboard or image approval is requested. Any later cadence change returns here and is recorded as a revision.（批次 0 配置定节奏；批次 2 自动执行）

## VISUAL_STYLE

**Enter when:** STORYBOARD is confirmed.

**Skill acts:** request one to three reference images or propose two to three directions derived from the brief and benchmarks. Extract stable style variables: medium, palette, line/texture, lighting, composition, aspect ratio, negative constraints, subtitle style, and text-card style. For historical subjects, produce `ERA_SPEC.md` per [era accuracy](era-spec.md) before writing pilot prompts, and freeze it together with the style. Produce three to five pilot prompts or images. Generate two candidates per pilot shot at the delivery floor (9:16 at least 1280×2276, prefer 1440×2560), then keep the better one by face, hands, and action; the loser is recorded, not delivered. If the service cannot reach the floor or takes no reference image, record the gap in `review/IMAGE-QC.md` before the pilot contact sheet.

**Ask now:** nothing. The style is already chosen in Round A; pilot images are shown later, together with the anchors.

**Deliver:** `VISUAL_STYLE.md`, pilot images, and an automated pilot verdict recorded in `review/IMAGE-QC.md`.

**Gate:** the pilot passes the automated check against `ERA_SPEC.md`, the frozen style, and its negative list; a failed row is revised and re-run internally. Freeze `ERA_SPEC.md` with the style before widening.（批次 2 · 先内部自检）

## CHARACTER_ANCHORS

**Enter when:** VISUAL_STYLE is confirmed.

**Skill acts:** detect recurring characters and decide whether strict identity continuity is needed. For each strict character, generate 2–3 anchor candidates; each candidate is a face plate plus a full-body plate of the same person (age, body, clothing, footwear, era details in both). When `ERA_SPEC.md` exists, the candidate's clothing, hairstyle, and footwear must come from its section-2 identity table — the anchor is where a wrong costume would propagate into every later image, so check every candidate against the table and drop the ones that fail before showing anything. Label the survivors A/B/C in a stable order. Never pre-select one and show only that: the choice belongs to the operator. If there are no recurring characters, this stage only prepares the pilot contact sheet.

**Ask now:** build one sheet with `scripts/contact_sheet.py` (`review/pilot-sheet.json` → `review/PILOT-SHEET.html`, record to `review/PILOT-REVIEW.md`) containing the three-to-five pilot shots with shot IDs and every anchor candidate with its letter. Deliver it through the preview channel recorded at START — `browser.preview` for the OpenCode Review pane, inline images in DSH, attachment or local browser elsewhere; a path, a file card, or "sheet saved at…" is not a preview, and the gate is not answered until the operator confirms seeing it. Then ask in rounds of at most three questions: one per strict character with `A` / `B` / `C` (default `A`), continuing in another round if more than three characters need a choice; then one `通过` / `要改` for the pilot. On `要改` or `都不要`, regenerate only the rejected rows and show the replacement set once; accepted rows are not reopened.

**Deliver:** `characters/` with 2–3 candidates per character under `characters/candidates/`, the chosen pair copied to `characters/{name}-face.png` / `{name}-body.png`, character cards, `review/PILOT-SHEET.html`, and the selection record in `review/PILOT-REVIEW.md` plus `decisions.anchor_selection`.

**Gate:** the operator has picked a letter for every strict character and clicked `通过` on the pilot; required anchors exist under their stable names, or the anchor part is explicitly `已跳过`. A `要改` loops only the rejected rows. This is the only image gate in the project.（批次 2 · 等用户点击；全自动也停）

## IMAGE_PROMPTS

**Enter when:** VISUAL_STYLE, the pilot set, and any required CHARACTER_ANCHORS are confirmed.

**Skill acts:** create `IMAGE_PROMPTS.md` mapped one-to-one to storyboard IDs. Each prompt carries reference rules, identity constraints, frozen style, specific scene, composition, output format, and negative constraints. Apply [prompt recipes](../assets/prompt-recipes.md): shot fact and count first, then framing, three planes (foreground / midground / background), a named light source with direction and color temperature, atmosphere, materials, capture, era anchors, and the no-text clause. State `no people in frame`, `one person only`, or `exactly one child` in the positive sentence; do not depend on the negative list to remove a person at CFG 1. Add the period-screen realism block (natural skin, pores, fine lines, correct hands, real hairline, worn fabric, practical light, film grain) and the anti-plastic negative list. For Qing, add the screen baseline from `ERA_SPEC.md` §7: shaved forehead and queue, court hat, horse-hoof cuffs, court beads, rank badge, flag-head hair for women. When `ERA_SPEC.md` exists, every prompt embeds its era anchors (2–4 concrete words) and appends its frozen negative list verbatim.

**Ask now:** nothing. The pilot and anchors were already confirmed; do not show prompts or individual images for another approval.

**Deliver:** the complete prompt manifest.

**Gate:** the manifest is written only after the pilot, anchor, and user confirmation pass. No further image approval.（批次 3 · 自动）

## IMAGE_GENERATION

**Enter when:** the user-confirmed pilot, any required character anchors, the prompt manifest, and the image service are all ready.

**Skill acts:** call the chosen image API in batches at the delivery floor (9:16 at least 1280×2276, prefer 1440×2560), map each result to its shot ID, retry failures, and write a generation ledger. Use the reference-image or img2img path when the service supports it and characters recur. Estimate count and cost before the first paid batch; if the service is unreachable, report the provider error and ask for a corrected key or endpoint — do not switch to manual one-image-at-a-time work, because that would put image review back on the user. Do not invoke video-generation models for this slideshow assembly stage.

**Ask now:** nothing unless the API rejects the key or endpoint; then ask only for the corrected credential.

**Deliver:** numbered generated images and generation ledger with failures or retries.

**Gate:** all required images exist, or missing shots are logged as capability failures; QC replacement runs automatically.（批次 3 · 自动）

## ASSET_QC

**Enter when:** the image batch is complete enough to inspect.

**Skill acts:** check counts, IDs, dimensions, corrupt files, style drift, repeated composition, identity drift, era violations, embedded borders, and text baked into images. Check every image against the delivery floor; a 1024-wide image is a capability failure, not a pass. Inspect eyes, hands, and hairline at 100% on the pilot and on any shot with a visible face; a thumbnail that looks fine but breaks at 100% is a replacement. Check realism separately: skin texture, hands, hairline, fabric wear, and whether a face reads as a photograph of a person rather than a render. For historical subjects judge era violations against `ERA_SPEC.md` sections 2–4 item by item; any East–West mixed element (Western clothing, furniture, or building parts on a Chinese-historic scene) goes straight to the replacement list — “style is close” is not a pass. For Qing, apply section 7's screen baseline and realism check; a plastic face, malformed hand, helmet hairline, or brand-new costume is a replacement, not a grade. Generate a replacement list rather than silently accepting weak assets.

**Ask now:** nothing. Never show replacement candidates for user approval.

**Deliver:** frozen image manifest, `review/IMAGE-QC.md`, and a replacement log.

**Gate:** every shot passes or has been re-generated and re-checked; unresolved capability failures are recorded, not handed to the user as image choices.（批次 3 · 自动）

## MUSIC

**Enter when:** ASSET_QC is confirmed.

**Skill acts:** ask whether music is needed. If no, mark `已跳过`. If yes, generate or source two to three short audition candidates within the authorized tool path, then plan a low-presence bed or a few emotion components. Narration remains dominant.

**Ask now:** nothing. The music choice was settled in the config round; in `全自动` default to no music unless the brief asks for it.

**Deliver:** music choice and mix plan.

**Gate:** music is mixed or explicitly skipped.（批次 3 · 自动）

## PREVIEW

**Enter when:** image QC and music are complete.

**Skill acts:** assemble the project, preferably with HyperFrames when available. In a host with the bundled HyperFrames skills, load the `hyperframes` mandatory entry point before touching the composition and follow its routing instructions. Align images, subtitles, text cards, and music to narration timestamps. Run structural checks and create a reviewable preview. Deliver it through `decisions.preview_channel` — `browser.preview` in the OpenCode Review pane, a local http server in DSH, attachment or local browser elsewhere; a path alone is not a preview. Do not final-render yet.

**Ask now:** in `我来选`, present the assembled preview through that channel and ask for approval — pacing, subtitles, story, ending — not individual images. In `全自动`, do not ask.

**Deliver:** preview delivered through the recorded channel, review board or representative frames, and issue list.

**Gate:** user approves the assembled preview in `我来选`; in `全自动` the frame check is recorded and the run continues. A general earlier “go ahead” is not sufficient.（批次 3 · 停靠点·硬门：只验收装配好的视频，不验收单张图）

## FINAL_RENDER

**Enter when:** PREVIEW is confirmed.

**Skill acts:** render the master, validate container/audio/video properties, extract representative frames from the final file, and watch or request a full human watch. Preserve the editable project.

**Ask now:** ask for acceptance after presenting the actual master and checks. Do not publish automatically.

**Deliver:** master video, project files, check report, and delivery note.

**Gate:** delivery stays `已做待验` until the user accepts the master, then `已验收`; both values live in `decisions.delivery_status`, because `stage_status` only accepts its own six values and a delivery state written there fails validation.（批次 4 · 验收回执）

## FEEDBACK

**Enter when:** the user later provides real platform results.

**Skill acts:** record actual production time, manual intervention, playback/retention/feedback data, and identify the smallest workflow change for the next episode. Follow [writing and review](writing-and-review.md) to retain actual wording corrections and user judgments in the channel profile; select only relevant, current lessons for later packs. For a new account with 7–15 days of weak results, review topic choice and script first, then present an evidence-based choice between changing the niche and repairing those inputs. After three to five stable, accepted scripts exist, offer to extract the channel's own writing template or Skill. Do not infer performance from render success, treat merely used scripts as gold samples, or freeze a channel template from one sample.

**Ask now:** request only the available real results and the user's qualitative judgment.

**Deliver:** next-episode change list and project-level defaults worth freezing after several episodes.

**Gate:** no final gate;（不在停靠内，交付后异步：等真实平台数据到手再进）the next project starts from confirmed defaults rather than copying unverified assumptions.
