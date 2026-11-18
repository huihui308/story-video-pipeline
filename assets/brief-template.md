# Production brief

## Project

- Title:
- Topic:
- Target audience:
- Language:

## Services

- Image provider: 阿里云 MaaS qwen-image-2.1-turbo (default) / OpenAI-compatible / ComfyUI / custom HTTP
- Image endpoint: https://maas.qianwenaiapi.com/compatible-mode/v1 (default) or any private/self-hosted URL (http, LAN IP:port, internal DNS, path prefix, self-signed TLS), explicit in the opening Q&A
- Image key: key_ref only, never the key
- Audio provider: 小米 MiMo TTS mimo-v2.5-tts (default) / edge-tts / Azure Speech / ElevenLabs / OpenAI TTS / MiniMax / custom HTTP
- Audio endpoint: https://api.xiaomimimo.com/v1 (default; token-plan keys use https://token-plan-cn.xiaomimimo.com/v1) or any private/self-hosted URL, explicit in the opening Q&A
- Audio key: key_ref only, never the key

## Product

- Run mode: 全自动 / 我来选
- Fidelity: 正史向 / 平衡 / 戏说（default: 平衡）
- Image review: none (fixed; single images and pilots are never shown to the user for approval)
- Narration format: audio-first (fixed; this pipeline does not support visual-first)
- Target platform:
- Aspect ratio: 9:16 (default) / 16:9
- Visual style: 电影写实 / 国画工笔 / 连环画 / 参考图
- Voice:
- Speaking rate: 舒缓 / 标准 / 明快
- Music: 无 / 轻铺底
- Target duration:
- Narrator count: 1 (a multi-narrator plan is outside this pipeline and needs its own decision)
- Desired cadence: 10–12 s per image (default) / 6–8 s

## Scope

- Included in this project:
- Explicitly excluded:
- Existing materials:
- Required user approvals:

## Success for this sample

- The sample is accepted when:
- Performance claims not yet verified:
