# Prompt recipes — richer frames without losing the shot

A prompt that only names the subject and a style produces a flat portrait. Build each image prompt in a fixed order, and make the shot's facts survive the style.

## Order

1. **Shot fact.** Who, how many, doing what, where. Empty frame: start with `no people in frame` (or the project's language equivalent). One person: `one person only`. One child: `exactly one child`.
2. **Framing.** Shot size, angle, lens intent. Use natural language: `wide shot from the tent opening`, `medium shot, waist up`, `low angle`.
3. **Three planes.** Foreground object or texture; midground subject; background architecture or landscape. Name each plane explicitly, or the model collapses them into one flat plane.
4. **Light.** Source, direction, hardness, color temperature, practicals. Not `cinematic lighting` alone. Example: `cold window light from camera left, warm candle practicals below, hard rim on the shoulder`.
5. **Atmosphere.** Haze, dust, steam, smoke, falling snow, rain. One or two, not all.
6. **Material.** Fabric weave and wear, wood patina and cracks, brass oxidation, paper fiber, stone pores. Two or three per prompt.
7. **Capture.** Camera, lens, depth of field, film stock or sensor look. Keep it after the content.
8. **Era and continuity.** `ERA_SPEC.md` anchors, costume and hair constraints, character anchor references.
9. **No-text clause.** Paper, edicts, plaques, and folds are blank or have illegible strokes.

## Scene light table

| Scene class | Key light | Fill / practicals | Atmosphere |
|---|---|---|---|
| `object` | single hard side light, raking | none or a thin bounce | dust motes in the beam |
| `tent` | cold light through the tent seam | low candle or brazier | smoke, breath vapor |
| `study` | cold window lattice light | candle on the desk | dust in the light shaft |
| `corridor` | daylight from the far end | lantern pools between columns | haze, floor reflection |
| `hall` | high window shaft and candle collision | rows of candles, dark eaves | incense smoke |
| `outdoor` | low side-back light | sky fill | grass, snow, or dust in the wind |

## Count and action lock

State the count and the action in the positive sentence, then repeat the count in a short clause: `one person only`, `exactly one child in his arms`, `the frame is empty`. A negative list is not enough: many samplers run at CFG 1, where negatives are ignored. When the service exposes CFG, raise it only for a failed shot; do not change the batch default.

## Exposure guard

Rich low-key prompts drift dark. Keep no more than two of `low-key`, `dark`, `deep shadow`, `underexposed` in one prompt. Always add a named key light plus `shadow detail, midtone separation`. Check the histogram during QC; if the median sits below the lower third, lift the render or rebalance the prompt rather than stacking more atmosphere.

## Skeleton

```
[count/action fact]. [place].
[framing].
Foreground: [object/texture]. Midground: [subject + action]. Background: [architecture/landscape].
Light: [source, direction, hardness, color temperature, practicals].
Atmosphere: [one or two].
Materials: [two or three].
[era anchors + costume/hair constraints].
[camera, lens, depth of field, film stock].
No readable text; paper and plaques are blank or illegible.
```

## Period screen realism

Two different failures look alike: a costume that is historically plausible but reads as "generic ancient China", and a face that reads as a rendered doll. Fix both in the positive prompt, then reinforce with the negative list.

**Positive realism block** (append after the character and costume sentence):

```
photorealistic film still from a historical drama, real actor, natural skin texture with visible pores, fine lines and subtle imperfections, anatomically correct hands with five fingers, period-correct hairline, practical light, 35mm film grain, restrained color grade
```

**Qing screen baseline** (when the subject is Qing): shaved forehead with a queue, court hat with a finial, horse-hoof cuffs, court beads, rank badge on the surcoat, cloth that wrinkles and shows wear. State the rank and the occasion; a Qing emperor in daily dress is not in full ceremonial yellow.

**Negative list** (add to the project's era negatives, not instead of them):

```
plastic skin, airbrushed face, beauty filter, doll face, wax figure, CGI, 3D render, anime, cosplay, extra fingers, fused fingers, deformed hands, modern makeup, contact lenses, veneers, bodybuilder physique, brand-new costume, costume-shop sheen, Ming dynasty clothing, Japanese clothing, Western clothing
```

A group shot needs `distinct faces, real casting, no repeated face`. A hands-visible shot needs `hands relaxed and anatomically correct`; hands are the cheapest realism check and the first thing a viewer notices.

**Prestige period-drama look.** When the brief asks for a TV-drama still, name the production level rather than the genre: `prestige historical drama, on-set production still, elaborate set dressing, practical candlelight, restrained grade, 35mm`. Add `not a short-form drama, not a studio portrait, not costume rental` to the negative list. "古装/清朝/电影感" alone collapses to a generic costume portrait; the production-level words are what separate a drama still from a photo studio.

## Delivery quality floor

- Resolution: for 9:16 request at least `1280×2276`, prefer `1440×2560`; for 16:9 at least `2276×1280`. Upscaling does not add detail, so a service that only returns 1024-wide images is a capability gap, not a style choice.
- Reference capability: prefer a service that accepts a reference image or img2img. Text-only generation cannot hold a face across shots; if the service has no reference input, record that limit before batch and do not promise character consistency.
- Candidates: generate two candidates for each pilot shot and keep the better one by face, hands, and action. For batch shots, one candidate is enough after the pilot locks the look; regenerate only QC failures.
- Realism crops: inspect eyes, hands, and hairline at 100% on the pilot contact sheet. A face that survives a thumbnail but breaks at 100% is a replacement.
- If the chosen service cannot meet the floor, say so before spending on a batch: name the missing capability and offer a stronger provider, instead of producing a full set that will be rejected.

## QC before batch

For each pilot image check: count, action, era, character identity, text, exposure, and whether the three planes are actually visible. For realism, check skin texture, hands, hairline, fabric wear, and whether the face looks like a photograph of a person rather than a render. For Qing, check the screen baseline: shaved forehead, queue, hat, cuffs, beads, rank badge. A missing action, wrong count, wrong dynasty, plastic face, or malformed hand is a replacement-level defect; a slightly dark frame is a grade adjustment.
