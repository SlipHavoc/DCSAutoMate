# Retro: C-130J cold start completion + SAPI TTS tags

**Goal:** Finish the C-130J `ColdStart()` (checklist steps 18–23) in the user's established style, then fix TTS mispronouncing "resume".

## What worked

- Reading switch semantics from the module's `Input/C-130J/keyboard/default.lua` (named bindings like "Nav Lights - Steady" with `value_down`). This gave exact position meanings that clickabledata.lua doesn't. It caught several inverted or unexpected switches: pitot/NESA 0 = ON, `ext_master` 1 = COVERT, strobes -1 = WHITE / 1 = RED, `NAV_RADAR.master_mode` 0.5 = ON / 1.0 = TEST.
- Recognizing that `multiswitch_stop` engine start knobs are the same factory as the user's already-working APU knob, and copying that step pattern (+1, +1, wait, -1). Worked first try in game.
- `scriptPause` for the non-clickable throttle step.
- Rendering SAPI to WAV and comparing file sizes as an automated proxy for "tag parsed vs read aloud".
- Writing a small speaker test script with numbered variants for the user to listen to. That settled the pronunciation question in one round.

## What didn't

- My first WAV check of SAPI XML put the tag at the **start** of the string. It passed, and I wrongly told the user tags work anywhere. Autodetect only fires on a leading `<`. Test the actual shape of the input, not a convenient one.
- Backup ADI: I guessed that uncaging meant press/release on `pitch_bar_cage`. Actually the pull **cages**, and uncaging means turning the knob (`MECH_INTERFACE.pitch_bar`, continuous). The user's working version moves it to 0.25, then 0.51. Exactly 0.50 does not uncage.
- Engine start wait of 40 s was just barely enough; the user set it to 45 s.

## Instruction update candidates

- Add to `dcsautomate.instructions.md`: "For position meanings of multi-position switches, check the module's `Input/<module>/keyboard/default.lua`. Named bindings with `value_down` give the per-position labels that clickabledata.lua lacks."
- Add: "When verifying a behavior with a proxy test, use input shaped like real usage (e.g. a tag mid-string, not at the start)."
