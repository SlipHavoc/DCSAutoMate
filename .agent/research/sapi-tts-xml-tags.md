# SAPI TTS: inline XML tags (pronunciation, part of speech)

**Date:** 2026-09-26

## Problem

`scriptSpeech` strings with a tag partway through (e.g. `'Then click <pron sym="r ih z uw m"/>.'`) had the tag read aloud letter by letter.

## Cause

`SpVoice.Speak(text, flags)` with the default flags (`0` sync / `1` async) only *autodetects* XML when the string **starts** with `<`. A tag later in the string is treated as plain text.

## Fix

`TTSManager.speak()` now adds `SVSFIsXML` (`8`) when the string contains `<`. Strings without `<` go down the unchanged path. Covered by `tests/test_ttsManager.py`, which renders to WAV and compares file sizes. A tag read aloud makes the audio about 2.6× as long.

## Verified by ear (MS Zira, en-US)

| Markup | Result |
|---|---|
| `<pron sym="r ih z uw 1 m"/>` (with or without the `1` stress mark) | Correct "resume" (verb) |
| `<pron sym="r ih z uw 1 m">resume</pron>` | Correct |
| `<partofsp part="verb">resume</partofsp>` | Correct. Easiest fix for heteronyms (resume, lead, read, live) |
| `<sapi>…</sapi>` wrapping the whole string, default flags | Correct (works because the string now starts with `<`) |
| `&` in plain text with flag `8` | Still read as "and"; SAPI's parser is lenient |

Without markup, SAPI read "click Resume" and "to resume" as résumé. Respelling as "re zoom" also works, but it's a hack.

## Gotchas

- `ttsVoiceId` indexes the installed voices, so it's machine-dependent. On the dev machine, `1` is Zira, not Hazel as an old code comment claimed.
- `<pron sym>` uses the SAPI phone set (`aa ae ah ao aw ax ay b ch d dh eh er ey f g h ih iy jh k l m n ng ow oy p r s sh t th uh uw v w y z zh`; stress digits `1`/`2` after the vowel). Only tested with en-US Zira.
- Displayed `scriptText` is separate from `scriptSpeech`, so speech-only markup never shows in the overlay text (it does appear in the "Speaking:" log line).
