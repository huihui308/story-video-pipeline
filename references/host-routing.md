# Host routing: DeepSeek Harness, OpenCode, and WorkBuddy

Do not route by product name alone. Route by verified capability in the current session.

## Capability check

At START, determine whether the host can currently:

- read and write the chosen local project folder;
- package and open attachments;
- run local shell commands for the state CLI, HyperFrames, or the renderer;
- route to the requested writing model;
- use a logged-in browser within the authorized boundary;
- call the configured TTS service without exposing secrets;
- generate or inspect images;
- run HyperFrames or another confirmed assembly tool;
- render a local video;
- show a generated file to the operator, and through which channel.

Record the result in the nine capability fields of `PROJECT_STATE.json` (`local_files`, `attachments`, `shell`, `model_routing`, `logged_in_browser`, `tts`, `image_generation`, `hyperframes`, `render`); a missing field fails validation. `Logged in` is not proof of the correct account, and an installed tool is not proof it is authorized for this project.

The preview is a separate delivery choice, recorded as `decisions.preview_channel` with one of `review_pane`, `inline_images`, `attachment`, `local_browser`. It is not a tenth capability boolean, so the nine-field map above stays unchanged. Decide it by what the operator can actually see in this session, not by what the model can read: a model's own `read` of an image proves nothing about the operator's view.

## DeepSeek Harness route

Use DeepSeek Harness as the continuous host when local files, required tools, and render capability are available. It may own the state file, produce project artifacts, coordinate writing-model handoffs, inspect images, build the HyperFrames project, and render after the preview gate.

The DSH web client cannot read a bare local path. Record `inline_images` and serve the project folder with `python3 -m http.server <port> --bind 127.0.0.1 --directory <project>`, check one URL returns `200`, then post `![](http://127.0.0.1:<port>/...)` in a reply with no tool call: a reply that carries both images and a tool call can lose its text and images — measured 2026-11-12.

If a required external model or service is unavailable, do not substitute silently. Create a bounded user action or handoff package.

For writing, keep the original guiding conversation as the reviewer and the user's chosen model as the author. Follow [writing and review](writing-and-review.md): the guiding conversation sends specific local edit instructions, the writer returns the full revision, and the guiding conversation checks the actual changes before user acceptance. A file handoff does not authorize the reviewer to replace the author's voice or expand into a rewrite.

## OpenCode route

Use OpenCode as the continuous host when it has local files, shell, both generation channels, and a working preview surface. Its desktop app renders files in the Review pane: call `browser.preview({ path: "<absolute path>" })` with the contact sheet, a single image, an audio clip, or the assembled preview. The path is server-local (relative to the workspace or absolute), so pass the project file's real path; an HTML contact sheet is the most reliable gate artifact because every candidate and label travels in one file.

If the call reports `[browser.disconnected]`, no desktop app is attached to the session: ask the operator to open the session in the app rather than repeating the call, and use `attachment` or `local_browser` only when those are genuinely available. Do not fall back to pasting a path and calling it a preview.

## WorkBuddy route

WorkBuddy may own early stages when it can analyze benchmarks, build or consume a writing pack, and use Kimi K3. For the tutorial route, select Kimi K3, turn on Max mode, choose the strongest available thinking setting such as `超高`, and use the 1M context window when those controls are actually visible. Confirm the selected model, mode, thinking strength, and context window before claiming Kimi K3 participated; if the product labels or available options have changed, state the nearest verified substitute instead of pretending the original setting is still available.

If WorkBuddy has verified local file and render capabilities, it may continue. Otherwise stop after the last supported stage and create `HANDOFF.md` plus all referenced artifacts for the next host. Tell the user exactly:

- what WorkBuddy completed;
- what remains unconfirmed;
- which folder or archive to give the next host;
- what the next host should do first;
- which gate must be presented to the user next.

## Handoff rules

Use `assets/handoff-template.md`. A handoff is valid only when artifact paths resolve or files are included, current stage/status are explicit, and the pending user request is preserved.

Do not call a handoff complete merely because a summary was written. Validate the state and package contents.
