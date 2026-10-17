# Canonical-alias-naming follow-ups

## Unify `generate_Mi24P.py` into `generateControlMapping.py` — DONE (2026-04-21)

Completed in commit `61efeb7` ("Deterministic device→table mapping + Mi-24P unification").
The shared generator now handles all four modules; `generate_Mi24P.py`,
`generate_FA18C.py`, `generate_AV8BNA.py`, and `generate_AH64D.py` have all been
deleted.  Live-validated: Mi-24P 1002/30/162 unchanged, FA-18C +2/−2, AV-8B +2/0,
AH-64D +4/−4.  See `.agent/retros/2026-04-21-deterministic-device-table-mapping.md`.

## F-15E mirror controls: fallback names and live check

The nil-hole extraction fix (2026-10-04) added six F-15ESE controls from `Mirror_Adjust_Control` (`PTN_1010`-`PTN_1012`).  Five got fallback names: `CNPYSYST.cmd_3010`/`3011`/`3012` (BTN, mirror rendering toggle, `misc_commands.mirror_center/left/right`) and `CNPYSYST.cmd_3911`/`3912` (LEV, angle adjust, `misc_commands.mirror_left_adjust/right_adjust`).  Only `CNPYSYST.mirror_center_adjust` resolved.  Work out why the helper's `command1_`/`command2_` parameters don't resolve through the command-access log, and live-validate the six controls in an F-15E (not yet done; the session was in a Mi-24P).
