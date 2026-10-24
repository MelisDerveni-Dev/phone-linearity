# Brag Plan: The Affine Observatory ("Is your phone linear?")

## What is this app?
A student lab that calibrates one phone's accelerometer from six resting poses, then shows the raw and corrected readings side by side, and finds the one situation where the model stops working: shaking.

## The angle
The project's own punchline is a one-word correction. Asked "Is your phone linear?", the honest answer is **"Not quite. It's affine."** The video plays that as a quiet lab-notebook film: a question, a dry correction, the one line of maths (`m = S a + b`, with the offset `b` as the culprit), proof that calibration roughly halves the error, and an honest limit. No hype. The restraint is the joke, and the honesty (it breaks when shaken) is the credibility.

## Hook (first 2-3 seconds)
"Is your phone **linear?**" in large Playfair serif on the project's parchment ground, one word at a time, with a small flat phone and a gravity arrow reading 9.81 m/s² beneath it. Eyebrow above in mono: OBSERVE. QUESTION. CALIBRATE. (the app's own tagline).

## Key moments (the middle)
- **The correction.** "Not quite. It's affine." then the equation `m = S a + b` with `b` in coral and the caption "a straight line that misses the origin".
- **Six resting poses.** Six small phones, one per pose, each with its up-arrow (+z, −z, +y, −y, +x, −x), arriving one per beat, labelled "Six resting poses fit S and b."
- **The proof.** A recreated viewer graph card: grey (uncalibrated) and teal (calibrated) error bars for the six test poses, built from the real test results, with the counter 0.22 → 0.11 m/s² ("error, on poses the fit never saw").
- **The break.** The real 30-second shaking recording as a coral envelope against the flat 9.81 line, peaking near 120 m/s².

## Outro / punchline
"Shake it. The model fails." (the honest limit) then the gear mark, **The Affine Observatory**, and its own footer line: *A little curiosity. A more precise world.*

## User flow worth showing
The product's flow is: connect phone, watch raw and corrected traces on the same scale, check against a reference, shake it. The video follows the evidence arc of that flow (pose, calibrate, compare, break) using the viewer's own card style and real results, rather than landing-page sections. The live connection screen is not recreated: there is no real phone data to show without fabricating it.

## Tone
- Preset: `polished`
- Creative direction: a quiet lab-notebook film with one dry joke
- Interpretation: four scenes, long holds, slow soft transitions on a ground that never cuts. Humour comes from understatement ("Not quite."). No exclamation, no stat-card hype.

## Format: landscape — 1920x1080
## Duration: 21.06 seconds (scene seams on the music's strong beats; the end card is extended so the closing lines get their reading hold)

## Visual identity (from the project: `web/styles.css`)
- Background: `#f3f1e9` (paper); panels/cards `#faf9f3`
- Accent: teal `#357a71` (calibrated), coral `#b96145` (raw / shaking / the offset b), brass `#9a783a`
- Text: `#263e39` (ink); muted `#6e7971`
- Display font: Georgia in the app, so **Playfair Display** here (bundled; Georgia is not)
- Body font: Inter. Mono: Cascadia Code in the app, so **IBM Plex Mono** here (bundled)
- Strongest visual element: the viewer's graph cards, the six-pose phone diagram, and the brand gear mark

## Share copy (draft)
Is your phone linear? Not quite, it's affine. Six resting poses roughly halved our accelerometer's error on poses the fit never saw; shake it, and the model fails.

## Audio direction
- Role: warm professional bed with sparse motion-matched accents
- Music: `happy-beats-business-moves-vol-9` (114.8 BPM, beat grid from 1.07 s); credit required (CC BY 4.0)
- Music treatment: enters at 0 under the hook at a low-to-moderate level, fade-in 0.5 s, holds steady, fades out over the last 1.6 s under the end card
- Music cue guidance: bundled preset read. Strong cues used: **4.23 s** (scene 1 to 2), **10.54 s** (scene 2 to 3, the proof card), **6.34 s** (the equation lands). Beat-grid windows for sequential reveals: six poses on 7.40, 7.92, 8.44, 8.96, 9.50, 10.01; six error-bar pairs on 11.06, 11.60, 12.12, 12.65, 13.18, 13.70
- Audio-reactive treatment: subtle; music RMS/bass gently warms the paper-ground glow and the card edge. No waveform or equalizer visuals.
- SFX posture: sparse, motion-matched, low high-frequency risk
- Audio-coupled moments: scene seams (soft impact), the poses arriving (soft taps), the bars landing, the final gear mark (one bell)
- Restraint rule: audio never competes with reading time; no whoosh on every cut

## Storyboard

### Scene 1: The question: 4.23s
Paper ground. Mono eyebrow "OBSERVE. QUESTION. CALIBRATE." fades in at the top. The title "Is your phone **linear?**" lands word by word (blur-in, 0.067 s apart, no travel); "linear?" in teal italic. Beneath, a flat phone on a line with a gravity arrow labelled "9.81 m/s²", and the line "A phone at rest feels only gravity." (reading hold about 2.3 s).
Sequential/interaction: no
Audio intent: calm, curious; bed alone
Audio-coupled idea: none
Music: warm bed, entering
Transition mood: clean blur swap on one stage → Scene 2 (lands on the 4.23 s strong cue)

### Scene 2: Not quite: 6.31s
"Not quite. It's affine." lands top (italic Playfair), holds. On the 6.34 s strong cue the equation **m = S a + b** lands large with `b` in coral and the caption "A straight line that misses the origin." From 7.40 s, six small phones with their up-arrows (+z, −z, +y, −y, +x, −x) arrive one per beat; label "Six resting poses fit S and b."
Sequential/interaction: yes, six phones arrive one by one on beats 7.40 to 10.01; the label holds fully visible for about 2 s afterwards
Audio intent: dry, wry; a soft tap per phone
Audio-coupled idea: six soft taps on the beat grid
Music: bed continues
Transition mood: blur swap → Scene 3 (lands on the 10.54 s strong cue)

### Scene 3: The proof: 4.74s
A recreated viewer graph card ("Calibrated vs uncalibrated · six test poses") with grey and teal bars for ±x, ±y, ±z built from the real test errors, arriving pair by pair on beats 11.06 to 13.70. At left the counter "0.22 → 0.11 m/s²" with the caption "typical error, on poses the fit never saw".
Sequential/interaction: yes, six bar pairs grow one by one on beats; the counter's final value holds about 1.5 s
Audio intent: quiet satisfaction
Audio-coupled idea: soft taps as bars land (every other beat so it never gets busy); one pop on the final 0.11
Music: bed continues
Transition mood: blur swap → Scene 4

### Scene 4: Where it breaks, then the mark: 5.78s (4a: 3.16s, 4b: 2.62s)
The real 30-second shaking envelope (coral) draws against the flat teal 9.81 line, labelled "up to 120 m/s²" and "at rest · 9.81". Line: "Shake it. The model fails." (about 2.2 s hold), then it exits and the gear mark with **The Affine Observatory** and "A little curiosity. A more precise world." lands and holds 2 s. A small credit line: "Music: Sascha Ende, ende.app (CC BY 4.0)".
Sequential/interaction: the trace draws left to right
Audio intent: tension without drama, then release
Audio-coupled idea: one bell on the mark
Music: bed fades out under the end card
Transition mood: blur swap inside the scene; end on a long hold

**Music mood for this video:** warm, light, professional
**Audio summary:** a steady warm bed with a few soft taps under the poses and bars, one gentle bell on the mark, fading out under the end card.

## Grounding of on-screen claims (all from the project)
- "Is your phone linear?", "Not quite", affine, "a straight line that misses the origin": report Section 1
- `m = S a + b`; six resting poses; "A phone at rest feels only gravity": report Sections 1-2
- 0.22 → 0.11 m/s²: report Section 4 (held-out static test poses, 0.216 → 0.111 RMS); per-bar values from `results/analysis-2026-10-23/static-test.csv`
- Shaking up to 120 m/s²; "the model assumes a phone at rest": report Section 4 and `results/evidence-2026-10-23/`; trace from `data/processed/angles-2026-10-22/limit.csv`
- OBSERVE. QUESTION. CALIBRATE. and "A little curiosity. A more precise world.": `web/index.html`
- Authors' names are intentionally **not** on screen; the video credits the project, not individuals.
