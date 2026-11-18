# Story Video Pipeline（image-story-video-wizard 分支）

DeepSeek Harness（DSH）与 OpenCode 桌面版上的图片叙事视频流水线，当前在 DSH 实测跑通主流程，OpenCode 走 Review 面板交付预览。输入一个选题，或者「选题 + 时长」，它查资料、出剧本，再做到配音、分镜、出图、装配、预览、成片。WorkBuddy 一类只带前段能力的宿主也能接，见「宿主」。

用户只提供当前这一步必需的材料或决定。阶段判断、默认值、自检和返工由 Skill 负责，不把整套流程甩给用户。

本 Skill 是 [image-story-video-wizard](https://github.com/aaronyi97/image-story-video-wizard) 的本地分支，库内路径 `.claude/skills/story-video-pipeline`，按 David 的制作习惯改造，与上游不保证同步。

## 适合什么

- AI 讲书、历史故事、人物故事、有声故事。
- 播客音频加配图的图片联播视频。
- 需要人物一致性、固定画风、字幕与文字卡的静态图叙事视频。

只要一篇文案、一张图或普通剪辑，不用调这个 Skill。

## 开工先问服务与模式

新项目第一条回复一次问三件事：生图通道（地址 + key）、音频通道（地址 + key）、运行模式（`全自动` 推荐 / `我来选`）。用宿主可点选提问（DSH 用 `ask_user_question`），每项 2–5 个选项，默认项放第一并标「（推荐）」，附一句代价。不用文字表单，不让用户回 `1A 2B` 这类编号。

- **全自动**：开场只收两条通道的地址与 key 和运行模式，其余默认值由技能定——史实尺度、画幅、语速、视觉风格、配乐、字幕、节奏，逐项记 `source: "skill"`；音色例外：探活通过后出 5–10 个 15 秒试听让操作者点选。START 直接跑到 FINAL_RENDER，停靠为开场、音色试听、pilot 与人物锚点候选三处；只在探活失败、事实无法核验、发布授权时打断，停靠之间连续推进不原地等提示。各道硬门改为自检，依据写进 `review/` 与 `stage_history`。
- **我来选**：开工前三轮点击问完，之后才生产。S 轮就是首条回复：生图地址 + key、音频地址 + key、运行模式。A 轮：史实尺度（正史向 / 平衡 / 戏说）、画幅（`9:16` 默认 / `16:9`）、视觉风格（电影写实 / 国画工笔 / 连环画 / 给参考图）、图片节奏（10–12 秒 / 6–8 秒）。B 轮：音色（5–10 个 15 秒试听）、语速（舒缓 / 标准 / 明快）、配乐（无 / 轻铺底）。

可推断的项（平台、字幕、±10% 时长）不问；续跑沿用状态文件里已记录的模式与配置，不重问。

## 模型服务与 key

开工第一条回复用一条提问收两条通道：每通道一问，**问题不带选项**，答案输入框就是入口，用户直接填 `地址 | key`（例：`https://relay.example.com/v1 | sk-…`）。预设只作说明写进问题正文；不让用户点选代替输入，也不让用户去改任何文件。

- **生图（默认）**：`阿里云 MaaS · qwen-image-2.1-turbo`（推荐，内置地址 `https://maas.qianwenaiapi.com/compatible-mode/v1`）；其余 `OpenAI 兼容`（gpt-image / DALL·E）、`ComfyUI`（自建）、`自定义 / 中转地址`。
- **音频（默认）**：`小米 MiMo TTS · mimo-v2.5-tts`（推荐，内置地址 `https://api.xiaomimimo.com/v1`；token-plan key 用 `https://token-plan-cn.xiaomimimo.com/v1`）；其余 `edge-tts`（免地址、免 key）、`Azure Speech`、`ElevenLabs`、`OpenAI TTS`、`MiniMax / 火山`、`自定义 / 中转地址`。

提问控件是问答的主要入口：支持文本输入就在控件里填 `地址 | key`；控件只有选项时，同一问改在对话里问，用户直接回一句。两种方式都由技能取出密钥后自己写入项目外密钥文件——不要让用户自己去编辑 `~/.story-video/secrets.env`、`PROJECT_STATE.json` 或任何 `.env`。

地址不再静默取默认：选项里写明内置 URL，答案可换成自建或中转地址。key 在同一个答案里给；环境或密钥库已有就把它作为第一项（`env:IMAGE_API_KEY`），不再索要。点了预设但没给地址或 key，用同样的填空形式只补问缺的那一项。key 只写进项目外的 `~/.story-video/secrets.env`，`PROJECT_STATE.json` 只记 `key_ref`；不回显，不进提示词、日志、截图或仓库。探活失败时按供应商报错改地址、key 或服务商。

私网与自建地址一等支持：`http://`、局域网 IP、内网 DNS、带端口或路径前缀的反代、自签 TLS 都能直接填，不强制 HTTPS，不把地址改写成公网。自建服务可以没有 key，答案选「无 key（私网自建）」。探活从实际调用生成服务的那台主机发起：`localhost` 指那台主机，内网地址要同网段或已连 VPN；私网探活失败先查网络与证书，不改地址。

## 快速路径：主题 + 时长 → 剧本

开场只有「主题 + 时长」时（例如「九子夺嫡，10 分钟」），不问简报，只问开场问答（两条通道地址 + key、运行模式）：

- **全自动**：开场已收两条通道的地址与 key；推断受众、平台、语言、`9:16` 等可逆默认值，自选至少两个对标并记理由，自定史实尺度、语速、风格，逐项记 `source: "skill"`；音色在探活通过后出试听点选，然后直接进入检索与写作。
- **我来选**：开场问答先定服务地址、key 与运行模式，再生成 15 秒音色试听，走 A/B 两轮点击；答案落盘后才开始生产。默认值被否就退回 BRIEF/BENCHMARKS。
- **第一条生产消息**：检索（库内素材有则用 + 有限公开只读搜索），事实清单与来源索引写进 `writing-pack/03-MATERIALS.md`，人物表写进 `writing-pack/04-CAST.md`，交一份完整初稿，并且**只合成 45–60 秒样音**（三到五段 = 开头 + 中段专名最密段落拼接，不许只取开头——样音只取开头，中段读音就没人听过；TTS 输入按 `audio/PRONUNCIATION.md` 替换）。查不到的显式标缺口，不编事实、人名、年代、出处。
- **样音通过后**：合成剩余旁白，进入批次 2–4。全自动自检样音时长、发音、响度；我来选等用户点击「通过/要改」。快速路径不豁免发布授权。

## 停靠点

16 个阶段收敛为：全自动 3 个（0 配置、0.5 音色试听、2 画面基准）；我来选 5 个（0 配置、1 文稿+样音、2 画面基准、3 预览、4 成片）。FEEDBACK 要等真实平台数据，交付后异步跑。停靠之间连跑，不逐阶段问「可以继续吗」。开场问答同时探明 TTS 与出图通道，探活失败才补问。

| 停靠 | 覆盖阶段 | 这次锁定什么 |
|---|---|---|
| 0 配置（两种模式都停） | START → BRIEF → BENCHMARKS | 生图地址+key、音频地址+key、运行模式（全自动到此为止）；我来选再加史实尺度、画幅、视觉风格、图片节奏、音色、语速、配乐（三轮点击，开工前问完） |
| 0.5 音色试听（全自动也停） | VOICE 预选 | 5–10 个 15 秒试听经预览通道交付，点选一个音色；我来选已在 0 轮 B 问过，不停 |
| 1 文稿 + 样音 | WRITING_PACK → SCRIPT → VOICE | 终稿与 45–60 秒样音验收；只授权合成剩余旁白 |
| 2 画面基准（全自动也停） | STORYBOARD → VISUAL_STYLE → CHARACTER_ANCHORS | 看 3–5 张 pilot 与每个人物的 2–3 个锚点候选，选 A/B/C 再点 通过/要改；通过后才写完整提示词清单 |
| 3 预览 | IMAGE_PROMPTS → IMAGE_GENERATION → ASSET_QC → MUSIC → PREVIEW | 出图、QC、配乐全自动；只看装配好的预览 |
| 4 成片 | FINAL_RENDER | 成片验收；发布另要一次单独授权 |

规则：每个停靠的提问合并成一次，最多三个问题，全部可点选并附默认项；硬门在批内即时生效，触碰即停；一次回复批量落该停靠内已答阶段的 `已确认`。pilot 与人物锚点是唯一一次图片确认，锚点由用户选 A/B/C；通过后单张图与 QC 不再进停靠。

## 预览通道

能看见才算交付。START 选一条操作者真能看到的通道，记进 `decisions.preview_channel`：

- **OpenCode 桌面版**（`review_pane`，首选）：`browser.preview({ path: "<绝对路径>" })` 把图片、HTML、音频、视频开在 Review 面板。接触表用 `scripts/contact_sheet.py` 生成一个自包含 HTML 最稳：候选、字母、尺寸、备注都在这一个文件里。
- **DeepSeek Harness 网页**（`inline_images`）：`python3 -m http.server <port> --bind 127.0.0.1 --directory <项目>` 起服务，确认一个 URL 返回 200，再用无工具调用的回复内联 `![](http://127.0.0.1:<port>/...)`。同一回复里带工具调用时，图和文字可能一起丢（2026-11-12 实测）。
- **其他宿主**：`attachment` 把文件附进消息，或 `local_browser` 用系统默认浏览器打开 HTML。

裸路径、文件卡片、「已存到 review/…」都不算预览；模型自己 `read` 得到图，只证明模型看得见，不证明操作者看得见。操作者说没看到，就换下一条通道重新展示，不能对着没显示出来的图重复提问。

## 硬门

- 方向没确认，不做写作包；全自动记下默认值即视为确认。
- 终稿没确认，不合成整段旁白；45–60 秒样音没通过，不合成剩余段落（我来选等点击，全自动自检时长、发音、响度并留证）。
- 图片节奏与画风没确认，不写完整提示词清单。
- 3–5 张 pilot 与每个人物的 2–3 个锚点候选没经预览通道展示、没让用户选 A/B/C 并点 `通过`，不批量出图；通过后**不再让用户看单张图、选图或批 QC**。
- 预览没验收，不渲染最终成片；预览验收的是装配好的视频，不是单张图。
- 没有单独的发布授权，不上传、不发帖、不动线上账号。

门没过就标 `需要返工`，只回到最早受影响的阶段；下游产物标不可信，不删。

## 小步执行与中断恢复

一次模型步骤只产出一个小产物，写盘后进下一步，状态文件更新单独一小步：连续流几分钟的步骤被内容过滤或超时打断时，没落盘的推理整段丢失。断流恢复两步走：先把该步拆小重试一次；同样内容再触发，就交给换了 provider/model 的子代理直接写文件、只报路径与一行校验——同模型子代理绕不过过滤器，换模型才是关键，隔离只防失败拖垮主对话。已落盘的不重跑。节奏同理：问运行模式的回复到选项为止，交样音的回复到样音为止，每条回复只跑下一步，不预支后面的阶段。拆步只改执行节奏，停靠、批次与硬门照旧。

## 生产不变式

### 文案

- 学对标的选题逻辑、结构、节奏、钩子和转场，不抄原句、图片、音频、成片。
- 初稿必须完整闭合：起因到结局、开场问题有答案、埋的线有回收。缺结局或主线中断算材料缺口，不算「略短」。
- 开场直接进故事，前几句就带钩子和开场问题。不写「哪里是戏说、哪里是史实」的口径宣言段，考据立场留在 BRIEF / MATERIALS，旁白里最多一句自然带过。
- 历史或真实人物题材必须附人物表（姓名、身份、称谓或排行、年代或年号），正文里的专名逐字核对。错名字、错排行、错年号是事实错误，不是文风问题。
- 原对话给一份定点修改单（落点 + 问题 + 动作 + 范围），写手只改列出的内容和必要例外；回来后核对实际改动，不做第二轮润色，不靠加长凑篇幅。

### 配音

- TTS 服务与 key 在开场问答定好；这里只验证可用性，不再索要密钥。key 只留在项目外的本地密钥文件，状态文件只记 `key_ref`。
- 同一段约 15 秒文本试 5–10 个音色，先定音色再调语速；试听集在配置轮交付。15 秒只用来选音色，不是样音。
- 配置确认后，第一步合成约 45–60 秒样音（三到五段 = 开头 + 中段专名最密段落拼接；只取开头等于中段读音无人验），用户验收音色、节奏、发音后才合成剩余段落；我来选等点击，全自动自检并留证。
- 合成前建发音表：**全量扫描终稿**里 `[胤允]` + 生僻字/多音字的名字 token（含 允禩 这类改名写法），逐个入表或进白名单、key 与脚本 codepoint 精确一致，替换词按字典读音核验（胤禔 = zhī 不是 tí；胤祄 = jiè），未覆盖清单落盘当证据。表落在 `audio/PRONUNCIATION.md`，模板是 `assets/pronunciation-map.md`；替换词只用于 TTS 输入，剧本、字幕、文字卡保留原字。试听没暴露的名字继续当可疑项。读错算映射缺陷，改表重合成受影响段落，不改音色。

### 分镜与画面

- 按实际旁白时长算图数：6–8 秒一张，10 分钟约 75–100 张；10–12 秒一张，约 50–60 张。首个音频优先项目默认 10–12 秒。
- 批量前先跑 `python3 scripts/era_lint.py images/prompts --era qing`，非 0 不出图：只写「清代官员」的提示词会被模型画成明制乌纱帽。
- 3–5 张 pilot 先由技能按 `ERA_SPEC.md` 自检，再用 `scripts/contact_sheet.py` 把 pilot 与锚点候选拼成带 shot ID 和候选字母的接触表，经预览通道交付，让用户选 A/B/C 并点一次 `通过` / `要改`；通过后才写完整提示词清单。
- 识别反复出现的人物；需要身份连贯时，每个严格人物出 2–3 个锚点候选（面部 + 全身同一人），全部展示，用户选一个；不替用户挑「更好的那个」。
- 用户点 `通过` 后，单张图、QC 替换、批量出图都不再交给用户验收；技能自检后自动重出，结论写 `review/IMAGE-QC.md`。`要改` 只重出被拒的行，只展示替换组。
- 提示词按 `assets/prompt-recipes.md` 的顺序写：镜头事实与人数、景别、前景/中景/背景三层、有方向与色温的具体光源、气氛、材质、摄影参数、时代锚点、无字约束。只写「主体 + 风格」会出平图。
- 空镜写「画面中没有人」，单人写「只有一个人」，抱一个孩子写「只抱一个孩子」；CFG 1 下负面词不起作用，人数与动作必须写在正向句子里。
- 历史题材先出 `ERA_SPEC.md`，随风格一起冻结：每条提示词内嵌 2–4 个时代锚点词，负面清单整行照搬；ASSET_QC 逐张对照，中西混搭算替换级缺陷，不商量。
- 清宫剧识别点要写死：前额剃光 + 辫子、顶戴（暖帽/凉帽 + 顶珠 + 花翎）、朝珠、马蹄袖、补子、旗头/两把头；皇帝日常常服不是全套明黄朝服。只写「清朝皇帝」会出成通用古装。
- 真人感单列一道检查：毛孔、细纹、正确五指、自然发际线、织物褶皱与磨损、实用光源、胶片颗粒。塑料脸、磨皮、六指/融指、头套发际线、全新戏服都算替换级缺陷，不算「风格问题」。
- 画质有底线：9:16 至少 1280×2276，优先 1440×2560；每个 pilot 镜头出两张候选，按脸、手、动作留一张；每个锚点出 2–3 个候选，全部给用户选；眼睛、手、发际线按 100% 放大检查。服务商达不到分辨率或没有参考图/图生图能力，批量前先说清能力缺口，不拿成片赌。

### 装配与验收

- 优先 HyperFrames 组装；宿主带 HyperFrames skills 时先加载 `hyperframes` 入口再动工程。
- 图像、字幕、文字卡、可选配乐对齐旁白时间轴。
- 先出可审预览：我来选由用户完整看一遍，全自动抽帧检查并把未覆盖项写进 `review/preview.md`。
- 用户验收前状态是 `已做待验`，验收后才 `已验收`。

## 项目产物与续跑

项目目录固定文件名，换宿主也能接着做：

| 产物 | 内容 |
|---|---|
| `PROJECT_STATE.json` | 阶段、状态、已确认决定、产物路径、当前唯一待办 |
| `BRIEF.md` | 选题、受众、平台、画幅、时长、语言、旁白人数、本期成功标准 |
| `BENCHMARKS.md` | 对标来源、角色、证据、学什么 / 避开什么、权利边界 |
| `writing-pack/` | 通用写作要求 + 频道与语言范例 + 本期材料，自包含 |
| `SCRIPT.md` | 终稿正文 |
| `audio/` | 试听、旁白、时间戳 |
| `audio/PRONUNCIATION.md` | TTS 发音替换表，模板见 `assets/pronunciation-map.md` |
| `STORYBOARD.csv` | 分镜表，一个 shot 一行 |
| `VISUAL_STYLE.md` | 冻结的画风与文字处理 |
| `ERA_SPEC.md` | 历史题材的时代规格与负面清单 |
| `characters/` | 选定锚点（`{name}-face.png` / `{name}-body.png`）、`candidates/` 下的候选、角色卡 |
| `IMAGE_PROMPTS.md` | 与分镜一一对应的提示词 |
| `images/` | 生成图，按 shot ID 编号 |
| `review/` | 审稿记录、`PILOT-SHEET.html` 接触表、`PILOT-REVIEW.md` 选定字母、QC 记录、预览反馈 |
| `renders/` | 成片与检查报告 |
| `HANDOFF.md` | 需要换宿主续做时生成 |

状态文件用 `scripts/project_state.py` 管理：

```bash
python3 <skill-dir>/scripts/project_state.py init D:/projects/jiuzi --title 九子夺嫡 --host dsh
python3 <skill-dir>/scripts/project_state.py validate D:/projects/jiuzi/PROJECT_STATE.json
python3 <skill-dir>/scripts/project_state.py summary D:/projects/jiuzi/PROJECT_STATE.json
python3 <skill-dir>/scripts/project_state.py repair D:/projects/jiuzi/PROJECT_STATE.json
```

`init` 会建好 `writing-pack/`、`audio/`、`characters/`、`images/references/`、`images/generated/`、`review/`、`renders/`；已有状态文件时拒绝覆盖（退出码 2）。状态值是这六个：`未开始`、`进行中`、`待确认`、`已确认`、`需要返工`、`已跳过`。`已做待验` 与 `已验收` 是交付口径，记在 `decisions.delivery_status`，不塞进 `stage_status`。项目目录放在库外，整个目录搬走后跑一次 `repair` 重指路径。

## 宿主

主打 DeepSeek Harness 与 OpenCode 桌面版。Skill 靠会话里的真实能力路由，不按产品名猜。START 时确认：能否读写项目目录、打包附件、接到指定写作模型、在授权范围内用已登录浏览器、调用已配置的 TTS、生图或看图、跑 HyperFrames、渲染本地视频，以及用哪条预览通道把文件真正送到操作者眼前。

- **DeepSeek Harness**：连续宿主。本地文件、Shell、渲染都在时，从 START 一路管到 FINAL_RENDER：管状态文件、出产物、协调写作模型交接、装配和渲染。实测跑通的是这条。网页端用 `inline_images`，图片必须放在无工具调用的回复里。
- **OpenCode 桌面版**：连续宿主。Review 面板用 `browser.preview` 直接显示图片、HTML、音频与视频，`preview_channel` 记 `review_pane`；`[browser.disconnected]` 表示桌面 App 没接上，让用户先在 App 里打开会话，不要反复重试同一个调用。
- **WorkBuddy**：只有前段能力时（分析对标、组写作包、接 Kimi K3）做到 SCRIPT 为止，出 `HANDOFF.md` 和全部产物，写清剩下什么没确认。Kimi K3 的选法：开 Max，思考强度取当前可见的最高档（如 `超高`），上下文 1M。

外部模型或服务不可用时不静默替换，给有限度的用户操作或交接包。

## 一句话安装

DSH 读两种 Skill 目录：工作目录里的 `.claude/skills/`，和全局的 `~/.claude/skills/`。把整个目录复制到任意一处：

```bash
cp -r .claude/skills/story-video-pipeline ~/.claude/skills/story-video-pipeline
```

项目级就复制到工作目录的 `.claude/skills/` 下，只对那个项目生效。Windows 上用 `xcopy /E /I` 或直接复制文件夹。WorkBuddy 若也从本地 Skill 目录加载，装同一份，或链接到这一份。

## 开始使用

标准路径：

> 用 story-video-pipeline 技能做一期「九子夺嫡」的图片联播视频，主动推进，每次只让我提供当前必需的材料或做当前确认。

快速路径：

> 用 story-video-pipeline 技能做一期「九子夺嫡」的 10 分钟视频，查资料直接出剧本。

## 默认制作路线

- 写稿：DeepSeek Harness 里做完对标学习和写作包；需要外部写作模型时把写作包交出去出稿，回来只给定点修改单。
- 配音：默认小米 MiMo TTS（`mimo-v2.5-tts`，预置音色 `mimo_default`、冰糖、茉莉、苏打、白桦、Mia、Chloe、Milo、Dean），地址与 key 在开场问答确认；同段约 15 秒试 5–10 个音色，选完再调语速；也可换 edge-tts（云健等中文音色）或豆包 Seed-TTS 2.0。
  - MiMo 不是 `POST /v1/audio/speech`（那是 404 的错路径），而是 `POST {base}/chat/completions`：目标文本放在 **assistant** 消息的 `content`，请求体带 `audio: {format: "mp3", voice: "<音色>"}`，音频在 `choices[0].message.audio.data`（base64）。`/v1/models` 可先验 key；中文标准语速实测约 6 字/秒。
- 生图：默认阿里云 MaaS `qwen-image-2.1-turbo`，地址 `https://maas.qianwenaiapi.com/compatible-mode/v1` 与 key 在开场问答里确认；每个常驻人物出 2–3 个锚点候选，连同 3–5 张 pilot 经预览通道展示，用户选 A/B/C 并点一次 `通过` 后再批量跑。
- 剪辑：素材齐了优先 HyperFrames 组装，先看预览，验收后再渲染成片。

豆包语音入口：

- [豆包语音官方产品页](https://www.volcengine.com/products/Audio-editing-and-sound-processing)
- [豆包语音控制台](https://console.volcengine.com/speech/app)
- [豆包语音官方快速入门](https://www.volcengine.com/docs/6561/163043?lang=zh)

## 文件结构

```
.claude/skills/story-video-pipeline/
  SKILL.md                     入口：引导合同、运行模式、硬门、不变式
  agents/openai.yaml           界面名称与默认提示词
  assets/
    brief-template.md          简报模板
    handoff-template.md        换宿主交接单
    storyboard-template.csv    分镜表表头
    writing-pack-manifest.md   写作包组包模板
    pronunciation-map.md       发音替换表模板
    writer-rules.md            Kimi 通用写作要求
  references/
    workflow.md                16 阶段逐个的 Enter / Acts / Ask / Deliver / Gate
    host-routing.md            宿主能力路由与交接
    state-schema.md            PROJECT_STATE.json 字段与更新规则
    era-spec.md                历史题材时代考据规格与高频翻车点
    writing-and-review.md      写作包组织与定点审稿
  scripts/project_state.py     init / validate / repair / summary
  scripts/contact_sheet.py     生成自包含 HTML 接触表（候选字母 + 尺寸 + 选定记录）
  scripts/era_lint.py          批量前扫提示词：清代人物必须写帽型/发式/袍式，命中乌纱帽、展角、束发、道袍即拒
  docs/ARTICLE_ALIGNMENT.md    教程要求与 Skill 落点对照
  tests/                       结构、引导合同、状态机一致性测试
```

## 验证

```bash
python3 -m unittest discover -s tests -v
```

覆盖公开文件齐备、可点选交互合同（`全自动`/`我来选`、生图与音频通道的地址 + key 在开场问答收齐、15 秒试听、45–60 秒样音、开头 pilot 与锚点候选一次确认）、预览通道与接触表脚本、16 个阶段与运行时状态机一致（15 个制作阶段 + FEEDBACK）、每个阶段五字段齐全、教程关键要求落点、README 安装入口，以及状态文件的初始化、校验、修复、拒绝覆盖与中文输出编码。

装了 skill-creator 时再跑一次结构校验：

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

## 边界

豆包、生图 API、HyperFrames 和渲染都是实时外部能力，进入对应阶段时先探明当前是否可用；不可用就引导申请配置或出交接单，不声称已经参与或完成。换到 WorkBuddy 这类只带前段能力的宿主，同样先探能力再动手，能力不够就停在 SCRIPT 出交接单。

生图和配音的单价会变，实际调用时重新估算，不写成永久规则。「稳定日更」「人工介入低于一小时」这类指标要跑几期真实数据才记录，一期成片不算实现。

## License

[MIT](LICENSE)
