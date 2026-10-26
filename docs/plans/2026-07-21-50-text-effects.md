# 50 Text Effects Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 50 visually distinct, selectable, verifiable animated text effects to the GIF generator.

**Architecture:** Keep all effects inside the existing PIL-based generation pipeline in `gif_generator.py`. Each effect must be registered in the effect sets, parsed from the `color` query parameter, rendered through the static-layout frame loop, exposed in `static/index.html`, and documented in `README.md`.

**Tech Stack:** Python, FastAPI, Pillow/PIL, NumPy, vanilla HTML/JS.

---

## Current State

The app already has many working effects and a stable service on `http://127.0.0.1:8002/`.

Important files:
- `gif_generator.py`: effect registration, parameter parsing, drawing functions, GIF frame loop.
- `main.py`: preview/full caps, pure-text-effect detection, response caching.
- `static/index.html`: effect dropdown.
- `static/script.js`: preview URL generation and cache busting.
- `README.md`: user-facing effect catalog.

There is a partially-started set from the interrupted previous turn:
- `aurora_ribbon`
- `strobe_cut`
- `sandstorm`
- `magnetic_flip`
- `ink_bleed`

These are registered in parts of `gif_generator.py`, but still need drawing functions, loop dispatch, UI options, README entries, and API validation.

## Effect Catalog

### Batch 1: Finish In-Progress Effects

1. `aurora_ribbon` - flowing aurora ribbons clipped to text.
2. `strobe_cut` - fast editorial slices with white flash cuts.
3. `sandstorm` - particles assemble/disperse around letter shapes.
4. `magnetic_flip` - letters bend/flip as if pulled by a magnetic field.
5. `ink_bleed` - ink spreads from glyph edges and blooms inward.

### Batch 2: Light And Energy

6. `solar_flare` - hot lens flare bursts across text.
7. `pulse_ring` - expanding rings radiate from glyph centers.
8. `electric_outline` - animated electric outline around text.
9. `photon_stream` - light streaks flow through letter interiors.
10. `neon_saber` - saber-like bright slash reveals text.

### Batch 3: Glitch And Digital

11. `datamosh_blocks` - chunky block displacement and color breakup.
12. `scanline_moire` - moving moire lines through text.
13. `terminal_boot` - text boots with cursor, noise, and green phosphor glow.
14. `signal_dropout` - intermittent missing horizontal bands.
15. `cyber_shred` - thin vertical strips shred and reassemble.

### Batch 4: Liquid And Material

16. `molten_gold` - gold-like molten fill with bright highlights.
17. `ice_crystal` - icy cracks and frozen blue facets.
18. `lava_lamp` - soft blobs moving inside text.
19. `glass_refraction` - transparent text with moving refractive bands.
20. `oil_slick` - iridescent rainbow sheen.

### Batch 5: Particle And Nature

21. `fireflies` - glowing particles orbit and pass through text.
22. `snow_burst` - text appears from a cold snow burst.
23. `leaf_swirl` - small leaf-like strokes swirl around glyphs.
24. `meteor_rain` - diagonal meteor streaks reveal text.
25. `dust_reveal` - dust particles condense into readable letters.

### Batch 6: Motion Typography

26. `rubber_snap` - elastic squash, stretch, and snap.
27. `accordion_fold` - letters compress and expand like folds.
28. `orbit_letters` - characters orbit into final positions.
29. `flipboard` - split-flap board style flipping.
30. `wave_stack` - layered duplicated text waves.

### Batch 7: 3D Illusion

31. `extrude_spin` - faux-3D extruded text with rotating shadow.
32. `perspective_tunnel` - text copies recede into a tunnel.
33. `tilt_parallax` - RGB shadow gives moving parallax depth.
34. `cube_faces` - glyphs appear on rotating cuboid slices.
35. `depth_echo` - repeated offset layers move in z-depth.

### Batch 8: Cute And Social

36. `bubble_pop` - bubbly text grows and pops with small circles.
37. `candy_stripe` - animated candy-stripe fill.
38. `sparkle_hearts` - hearts and sparkles track around glyphs.
39. `confetti_hit` - confetti burst on text impact.
40. `sticker_peel` - sticker-like text peels from one corner.

### Batch 9: Cinematic

41. `title_slam` - title card slam with shockwave.
42. `noir_shadow` - moving noir shadow bands.
43. `spot_glimmer` - tiny glimmers sweep across strokes.
44. `curtain_reveal` - theatrical curtain wipe reveals text.
45. `camera_shutter` - aperture/shutter blades reveal text.

### Batch 10: Experimental

46. `barcode_scan` - barcode-like bars resolve into letters.
47. `topographic_lines` - contour lines move inside text.
48. `soundwave_fill` - audio-wave bars animate inside glyphs.
49. `kaleido_text` - mirrored colored shards around text.
50. `radar_ping` - circular radar sweep and scan glow.

## Implementation Pattern For Each Effect

Every effect must complete these hooks:

1. Add name to `AUTO_ADAPTIVE_TEXT_EFFECTS`.
2. Add name to `PURE_TEXT_EFFECTS`.
3. Add preview cap to `TEXT_EFFECT_PREVIEW_FRAME_CAPS`.
4. Add full cap to `TEXT_EFFECT_FULL_FRAME_CAPS`.
5. Add canvas padding rule in `calculate_adaptive_font_and_canvas`.
6. Add `elif text_color_param == '<effect>'` in the color parser.
7. Add `def draw_text_<effect>(...)` near the existing effect helpers.
8. Add the effect to `is_static_layout`.
9. Add dispatch branch in the frame loop.
10. Add the effect to `main.py` pure-text/rich-preview sets.
11. Add `<option>` in `static/index.html`.
12. Add README bullet.
13. Verify direct generator frames and HTTP API frames.

## Verification Standard

An effect is accepted only if:
- `python -m py_compile main.py gif_generator.py` passes.
- Direct generation returns at least 8 GIF frames for normal mode unless intentionally capped.
- Adjacent frame diff count is greater than 0 for at least 70% of frame pairs.
- API generation on `http://127.0.0.1:8002/generate?...` returns `200 image/gif`.
- The UI dropdown contains the option.
- README includes a user-readable description.

Use this verification snippet after each batch:

```powershell
& 'C:\ai\GIF202606\.venv\Scripts\python.exe' -m py_compile main.py gif_generator.py
```

Use this frame-diff pattern:

```python
from gif_generator import generate_gif_bytes
from PIL import Image, ImageChops, ImageSequence
from io import BytesIO

effects = ["effect_name"]
for effect in effects:
    data = generate_gif_bytes(
        "炫酷文字",
        frame_count=16,
        delay=55,
        text_color_param=effect,
        theme="dark",
        width_pixels=360,
        use_adaptive_canvas=True,
        fast_preview=False,
    ).getvalue()
    img = Image.open(BytesIO(data))
    frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(img)]
    changing = sum(
        ImageChops.difference(a, b).getbbox() is not None
        for a, b in zip(frames, frames[1:])
    )
    assert len(frames) >= 8
    assert changing >= int((len(frames) - 1) * 0.7)
```

## Task List

### Task 0: Stabilize Current Partial Work

**Files:**
- Modify: `gif_generator.py`
- Modify: `main.py`
- Modify: `static/index.html`
- Modify: `README.md`

**Description:** Finish or remove the five partially-registered effects so the codebase has no dangling effect names.

**Acceptance criteria:**
- [ ] `aurora_ribbon`, `strobe_cut`, `sandstorm`, `magnetic_flip`, and `ink_bleed` all have drawing functions.
- [ ] All five appear in the frame-loop dispatch.
- [ ] All five appear in UI and README.
- [ ] All five pass direct frame-diff verification.

**Verification:**
- [ ] `python -m py_compile main.py gif_generator.py`
- [ ] Direct generator frame-diff script for the five effects.
- [ ] API frame-diff script against `http://127.0.0.1:8002/generate`.

**Dependencies:** None.

**Estimated scope:** Medium.

### Task 1: Create Effect Registry Helpers

**Files:**
- Modify: `gif_generator.py`

**Description:** Reduce repeated hard-coded effect lists by introducing shared constants for text effects, rich preview effects, and padding categories.

**Acceptance criteria:**
- [ ] New effects can be added in one or two local registry blocks, not seven scattered places.
- [ ] Existing effects still resolve exactly as before.
- [ ] No behavior change for current API requests.

**Verification:**
- [ ] Compile check.
- [ ] Smoke-test 5 existing effects and 5 new effects.

**Dependencies:** Task 0.

**Estimated scope:** Medium.

### Task 2: Implement Batch 2 Light And Energy

**Files:**
- Modify: `gif_generator.py`
- Modify: `main.py`
- Modify: `static/index.html`
- Modify: `README.md`

**Description:** Add effects 6-10.

**Acceptance criteria:**
- [ ] `solar_flare`, `pulse_ring`, `electric_outline`, `photon_stream`, `neon_saber` work.
- [ ] Each has visible frame-to-frame motion.
- [ ] UI and README are updated.

**Verification:**
- [ ] Compile check.
- [ ] Frame-diff check for all five.
- [ ] API check for all five on port 8002.

**Dependencies:** Task 1.

**Estimated scope:** Medium.

**Status:** Completed on 2026-07-22.

**Verification result:**
- `solar_flare`: 16 frames, 15 changing frame pairs via `http://127.0.0.1:8002/generate`.
- `pulse_ring`: 16 frames, 15 changing frame pairs via `http://127.0.0.1:8002/generate`.
- `electric_outline`: 16 frames, 15 changing frame pairs via `http://127.0.0.1:8002/generate`.
- `photon_stream`: 16 frames, 15 changing frame pairs via `http://127.0.0.1:8002/generate`.
- `neon_saber`: 16 frames, 15 changing frame pairs via `http://127.0.0.1:8002/generate`.

### Task 3: Implement Batch 3 Glitch And Digital

**Description:** Add effects 11-15.

**Acceptance criteria:**
- [ ] All five digital/glitch effects work.
- [ ] At least two effects use structural distortion, not only color changes.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 4: Implement Batch 4 Liquid And Material

**Description:** Add effects 16-20.

**Acceptance criteria:**
- [ ] All material effects use masked fills or edge highlights.
- [ ] GIF optimization does not collapse any effect to static frames.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 5: Implement Batch 5 Particle And Nature

**Description:** Add effects 21-25.

**Acceptance criteria:**
- [ ] Particle counts are bounded for preview mode.
- [ ] Effects remain readable for Chinese text.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 6: Implement Batch 6 Motion Typography

**Description:** Add effects 26-30.

**Acceptance criteria:**
- [ ] Effects use whole-text or per-character motion.
- [ ] Layout remains stable in adaptive canvas mode.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 7: Implement Batch 7 3D Illusion

**Description:** Add effects 31-35.

**Acceptance criteria:**
- [ ] Effects create depth using duplicated layers, perspective, or shadows.
- [ ] No effect requires external 3D dependencies.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 8: Implement Batch 8 Cute And Social

**Description:** Add effects 36-40.

**Acceptance criteria:**
- [ ] Effects are bright, legible, and social-sticker friendly.
- [ ] Preview mode stays responsive.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 9: Implement Batch 9 Cinematic

**Description:** Add effects 41-45.

**Acceptance criteria:**
- [ ] Effects read like title-card motion graphics.
- [ ] At least three effects combine reveal plus glow/shadow.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 10: Implement Batch 10 Experimental

**Description:** Add effects 46-50.

**Acceptance criteria:**
- [ ] Effects are visually distinct from previous batches.
- [ ] All five pass frame-diff and API verification.

**Verification:** Same batch verification standard.

**Dependencies:** Task 1.

**Files likely touched:** `gif_generator.py`, `main.py`, `static/index.html`, `README.md`.

**Estimated scope:** Medium.

### Task 11: Add Automated Effect Smoke Test

**Files:**
- Create: `tests/test_text_effects.py` or `test_text_effects_smoke.py`

**Description:** Add a smoke test that imports `generate_gif_bytes`, renders a representative set of effects, and asserts multi-frame output where expected.

**Acceptance criteria:**
- [ ] Test includes all 50 newly planned effects.
- [ ] Test checks GIF frame count and frame differences.
- [ ] Slow effects use preview mode or lower width to keep runtime acceptable.

**Verification:**
- [ ] Run the smoke test directly with the project Python.

**Dependencies:** Tasks 0-10.

**Estimated scope:** Small.

### Task 12: Final UI And Documentation Audit

**Files:**
- Modify: `static/index.html`
- Modify: `README.md`

**Description:** Ensure the dropdown is organized into readable groups and README documents all effects by category.

**Acceptance criteria:**
- [ ] All 50 effects appear exactly once in the UI.
- [ ] All 50 effects appear exactly once in README.
- [ ] Labels are short and recognizable.

**Verification:**
- [ ] Use `rg` to compare effect IDs across code, UI, and README.
- [ ] Manual browser check on `http://127.0.0.1:8002/`.

**Dependencies:** Tasks 0-11.

**Estimated scope:** Small.

## Checkpoints

### Checkpoint A: After Task 0
- [ ] No dangling partially-registered effects.
- [ ] Existing app still loads on port 8002.

### Checkpoint B: After Tasks 1-3
- [ ] 15 total planned effects are complete.
- [ ] Registry helper does not break old effects.

### Checkpoint C: After Tasks 4-6
- [ ] 30 total planned effects are complete.
- [ ] Preview mode remains responsive.

### Checkpoint D: After Tasks 7-10
- [ ] All 50 planned effects are complete.
- [ ] No effect returns a static one-frame GIF unless intentionally documented.

### Checkpoint E: After Tasks 11-12
- [ ] Automated smoke test covers all 50.
- [ ] UI and README are consistent.

## Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| `gif_generator.py` becomes too large | High | Add registry/helper functions in Task 1 before adding most effects. |
| Some effects look visually similar | Medium | Keep category-level acceptance criteria and require structural differences. |
| Preview generation becomes slow | High | Cap frame counts, particle counts, and canvas sizes in preview mode. |
| GIF optimizer collapses subtle effects to static frames | Medium | Use frame-diff verification and add clear positional/shape changes. |
| 8000 port serves stale code | Medium | Use verified active dev server on `http://127.0.0.1:8002/`. |

## Execution Strategy

Work in batches of five effects. After each batch:

1. Compile.
2. Run direct frame-diff verification.
3. Run HTTP API verification on port 8002.
4. Update UI and README.
5. Only then move to the next batch.

This should avoid a huge unstable final merge and keep every batch demonstrably usable.
