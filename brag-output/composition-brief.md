# Hyperframes Composition Brief: The Affine Observatory

## Objective
Create a short launch-style brag video for The Affine Observatory ("Is your phone linear?"), a student lab that calibrates one phone's accelerometer from six resting poses and finds where the model fails.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape, 1920x1080, 30 fps
- Duration: 21.06 seconds

## Source Material
- Project root: the repository root (`Linear Accelometer Project`)
- Primary files read: `web/index.html`, `web/styles.css`, `web/presentation.css`, `README.md`, `report/report.md`, `results/analysis-2026-10-23/static-test.csv`, `results/evidence-2026-10-23/`, `data/processed/angles-2026-10-22/limit.csv` (shaking). Not read: `.private/`, `.tools/`, any `.env` or credential file.
- Product name: The Affine Observatory
- Tagline / strongest claim: "Not quite. It's affine." and "OBSERVE. QUESTION. CALIBRATE."
- Key UI or visual moment to recreate: the viewer's graph card (parchment card, mono eyebrow, serif title) showing uncalibrated (grey) vs calibrated (teal) error for the six test poses; the brand gear mark
- Copy that must appear verbatim:
  - Is your phone linear?
  - Not quite. It's affine.
  - m = S a + b
  - A little curiosity. A more precise world.
  - Music: Sascha Ende, ende.app (CC BY 4.0)

## Creative Direction
- Tone preset: polished
- Creative direction: a quiet lab-notebook film with one dry joke
- Interpretation: slow, confident reveals on a ground that never cuts; understatement is the humour; no hype language
- Angle: asked "Is your phone linear?", the honest answer is "Not quite. It's affine." The film walks the evidence: the equation, six poses, error roughly halved, and the honest limit (shaking).
- Hook: "Is your phone linear?" lands one word at a time over a flat phone with a 9.81 m/s² gravity arrow
- Outro / punchline: "Shake it. The model fails." then the gear mark, The Affine Observatory, and the project's footer line
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Any claim not in the project (see grounding in `brag-plan.md`)
  - Authors' names on screen

## Visual Identity
- Background: `#f3f1e9` (paper), cards `#faf9f3`
- Text: `#263e39` (ink); small text muted `#55625b` (darkened from the app's `#6e7971` for video contrast)
- Accent: teal `#357a71` (calibrated), coral `#b96145` (raw, shaking, the offset b), brass `#9a783a` (rules and eyebrows)
- Display font: Playfair Display (bundled; the app uses Georgia, which is not bundled)
- Body font: Inter. Mono: IBM Plex Mono (the app uses Cascadia Code, not bundled)
- Visual references from the project: parchment ground, brass hairlines, mono eyebrows, graph-card layout, the six-pose phone diagram, the gear mark

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. The question: 0.00-4.23s: title, gravity arrow, "A phone at rest feels only gravity."
2. Not quite: 4.23-10.54s: "Not quite. It's affine.", equation lands on the 6.34s cue, six phones arrive on beats 7.40-10.01 with the label "Six resting poses fit S and b."
3. The proof: 10.54-15.28s: graph card with six bar pairs on beats 11.06-13.70; counter 0.22 → 0.11 m/s²
4. Where it breaks, then the mark: 15.28-21.06s: shaking envelope vs 9.81 line, "Shake it. The model fails.", then gear mark, name, tagline, credit

## Audio
- Audio role: warm professional bed with sparse motion-matched accents
- Audio arc: bed alone under the hook; soft taps with the poses and bars; one gentle bell on the mark; fade out under the end card
- Music: `assets/music/happy-beats-business-moves-vol-9-by-ende-dot-app.mp3` (114.84 BPM)
- Music treatment: starts at 0, fade-in 0.5s, steady, fade-out over the last 1.6s; final mix normalized to -16 LUFS (true peak <= -1.5 dB) in the delivery encode
- Music cue guidance: bundled preset `cues/happy-beats-business-moves-vol-9-by-ende-dot-app.music-cues.md`. Strong cues 4.23, 6.34, 10.54. Beat grid 1.07 + k x 0.5275s.
- Audio-reactive treatment: subtle; RMS drives the paper-ground glow warmth; bass drives the card edge light. Data from `assets/data.js` (extracted with the Hyperframes media-use `extract-audio-data.py`). No waveform visuals.
- Audio-coupled moments:
  - Seams at 4.23 / 10.54 / 15.28: soft impact
  - Six poses on beats 7.40-10.01: soft tap each (every beat, quiet)
  - Six bar pairs on beats 11.06-13.70: soft taps on alternate beats
  - Gear mark at 18.44s: one bell
- SFX selection guidance: `impactSoft_medium_001/004` (seams), `click_003` (taps), `bong_001` (the 0.11 payoff), `impactBell_heavy_000` (mark); all low or medium high-frequency risk
- SFX analysis guidance: `.claude/skills/brag/assets/sfx/sfx-analysis.md`
- Exact SFX choice: final timestamps set after the animation exists
- Audio files: copied into `brag-output/composition/assets/`

## Hyperframes Instructions
Follow the Hyperframes `hyperframes`, `hyperframes-registry`, `media-use` and `hyperframes-cli` guidance as in the skill, skipping storyline, SPEC.md, usage, history, feedback and REVIEW.md steps. `check` is the single gate.

Requirements:
- Show real project data and UI language (the six-pose test errors, the real shaking envelope, the graph-card style, the gear mark).
- Keep all text readable; hold floors per `brag-plan.md`.
- Keep the video within 15-25 seconds.
- Include the planned music/SFX layer.
- Cue locks at 4.23 / 6.34 / 10.54 (marked `// beat-locked`); sequential items on the beat grid (marked `// beat-grid`).
- Local assets only (GSAP vendored in `assets/vendor/`); no network fetches at render time.
- Run `hyperframes check` before render.
- Keep creation and rendering local; no publishing, no telemetry.
