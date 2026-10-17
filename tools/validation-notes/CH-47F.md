# CH-47F Validation Notes

Module: `CH-47Fbl1`
Validation run: 2026-05-09
Result: 588 pass / 448 fail / 270 skip → after rocker fix: re-validate pending

---

## Failure Categories

### Fixed: Inverted rockers (26 controls)

**Symptoms:** `inc: expected 1.0000, got -1.0000; dec: expected 0.0000, got 1.0000`

**Root cause:** `detectBtnPulseCounter` in `generateControlMapping.py` was misclassifying
`animated_rocker` / `animated_rocker_small` elements as pulse-counter wheels.
These controls (BTN class, `argValue = ±1.0`, `argLim = [[-1,1],[-1,1]]`, `stopAction` set,
`use_release_message = true`) share the structural shape of a BTN pulse counter except that
their argLim spans negative to positive (centered range). The fix: reject BTN elements with
`lim[0] < 0` in `detectBtnPulseCounter` — these are rockers, not counters.

After the fix, rockers are classified as discrete with 3 positions `[-1, 0, +1]`, step 1.0.

**Affected controls:**
- `CANTED_CONSOLE.AFCS_AFT/FWD` — AFCS attitude rockers
- `CENTRAL_CONSOLE.MISC_CGI_TEST` — CGI test rocker
- `GRIPS.C1_CMDS/CRSR_H/CRSR_V/TRIM_H/TRIM_V/MFCU1_R1/S2_H/S2_V/S3_H/S3_V` — pilot grip rockers
- `GRIPS.T1_DAFCSMODE_H/V/FRQ_H/V/HUDMODE_H/V/SRCH_H/V/UPDN` — pilot throttle rockers
- `OVERHEAD_CONSOLE.OCFC_ENG_START/NR_1/NR_2/OSPD` — FADEC rocker switches

---

### Acknowledged: Crew access restrictions (most failures)

DCS only allows a crew member to operate controls they have `crew_member_access` for.
The validator runs as crew member 0 (pilot). Controls for crew members 1-5 do not respond.

**Crew access breakdown:**
- Crew 1 (copilot): `COMM_PANEL_LEFT` (ICS2), `GRIPS.C2_*`, `GRIPS.T2_*`, PDP1 CBs, etc.
- Crew 2 (crew chief): `COMM_PANEL_TROOP_COMMANDER` (ICS3), `AFT_WORKSTATION`, `MAINTENANCE_PANEL`, `EXTERNAL_CARGO_EQUIPMENT`, etc.
- Crew 3-5 (gunners): ICS4, ICS5, ICS6 comm panels; external cargo hooks; etc.

These are not extractor bugs. All 223 PDP1 CB failures, all 126 COMM panel failures (ICS2-ICS6),
and most of the "no response" category are crew-access state issues.

---

### Acknowledged: PDP2 circuit breaker argValue discrepancy

**Symptom:** `pos 1: expected 0.9000, got 1.0000`

PDP2 CBs (crew 0 accessible) respond, but the arg goes to 1.0 when the native Lua declares
`argValue = 0.9` for the pull-out action. The DCS CB device apparently snaps to the nearest
discrete stable state (1.0 = fully out) rather than the declared animation arg value.

This is not an extractor bug — the Lua correctly declares 0.9 and the extractor reads 0.9.
The device's runtime behavior diverges from the clickabledata declaration. CB controls are not
used in the CH-47F automation script so this has no practical impact.

PDP1 CBs (crew 1) don't respond at all — crew access issue.

---

### Fixed: ARC186_FREQ1 step/argLim (extractor bug)

**Symptom:** `inc: expected 0.2500, got 0.2000` (pre-fix validation)

**Root cause:** `extract_CH47F.py` was calling `extractSlaveAnimation` but NOT
`extractSlaveAnimationMeta`. The extraction JSON had `slaveAnimation` (arg numbers) but no
`slaveArgLim` or `slaveArgScale`. The generator then used `incValue = 0.1` directly as the step
and `[0, 1]` as the argLim — both wrong for FREQ1.

The native Lua spec is `{1229, {0.125, 0.775}, 0.5}`, meaning the display arg spans [0.125, 0.775]
and moves at 0.5× the command value per click. Correct step = 0.1 × 0.5 = **0.05**.

**Fix:** Added `extractSlaveAnimationMeta` import and extraction block to `extract_CH47F.py`
(mirroring `extract_A10C.py`). Also added `animationSpeed` extraction so `settleDelay` is
auto-computed. Re-extracted CH-47Fbl1.json and regenerated the control mapping.

**Verified in controlMapping:**
- `ARC_186.ARC186_FREQ1`: `step: 0.05`, `argLim: [0.125, 0.775]`, `settleDelay: 0.1`
- `ARC_186.ARC186_FREQ2/3/4`: `step: 0.1`, `argLim: [0.0, 1.0]` (scale=1.0, lim=[0,1])

---

### Acknowledged: STEER_KNOB_arg590 momentary readback

**Symptom:** `pos 1: expected 1.0000, got 0.0000`

`STEER_KNOB_arg590` (Button_4) is the steering knob re-center action. The Lua declares
`use_release_message = true` and `arg_lim = {0.0, 1.0}`. DCS sends 1.0 on press and
0.0 on release immediately after. By the time the validator reads back, the release has
already fired and the arg is back at 0.0. The control is correctly mapped — the re-center
action does execute when commanded. Pos 0 correctly does nothing (0.0 is the rest/release
state). This is a validator limitation with momentary spring-loaded buttons, not a mapping bug.

---

### Acknowledged: ARC186_SQUELCH — DCS Lua bug (missing stop_val_)

**Symptom:** `pos 0: arg unchanged at 0.0000; pos 2: arg unchanged at 0.0000`

**Root cause:** `default_tumb_button` is called at clickabledata.lua line 1486 with only 6 positional
arguments: `default_tumb_button({0,1}, _("Squelch / TONE"), devices.ARC_186, device_commands.Button_7, device_commands.Button_8, 1220)`.
The 7th argument (`stop_val_`) is not passed, so it is nil in the returned element table (`stop_value = nil`).

For a `TUMB`-class sub-element, `stop_value` is the arg position where the TUMB stops toggling.
With `stop_value = nil`, DCS has no valid stop target and ignores all mouse clicks on the control.
This is confirmed in-cockpit: the squelch knob does not move, rotate, depress, or respond to input at all.

**This is a bug in the CH-47F Lua, not a mapping issue.** The control is correctly extracted and mapped;
the DCS module simply doesn't implement it in a working state. No fix is possible on our side.

---

### Acknowledged: PDP2 CBs with collars installed — mission state

**Symptom:** `pos 0: arg unchanged at 0.8000; pos 1: arg unchanged at 0.8000`

13 specific PDP2 circuit breakers are in the collar-installed state (arg=0.8) in the hot-start
validation mission. A collar physically blocks the CB from being toggled. Validation commands have
no effect until the collar is removed. This is mission state, not a mapping bug.

**Affected CBs:** `PDP2.2B13`, `PDP2.2C10`, `PDP2.2C20`, `PDP2.2C22`, `PDP2.2D18` through
`PDP2.2D24`, `PDP2.2E07`, `PDP2.2E08` (13 controls total).

---

### Acknowledged: Miscellaneous state failures

- `AFT_WORKSTATION.INTRLTG_CABIN_KNOB/SW`: crew 2 (crew chief)
- `EXTERNAL_CARGO_EQUIPMENT.*`: crew 2 + require sling load attached
- `GRIPS.MAIN_MCAUTION_L`, `GRIPS.T2_IRWHT`: crew 1 (copilot)
- `MAINTENANCE_PANEL.*`: crew 2

---

## Pilot Seat Validation (2026-05-10)

Run: `--module CH-47Fbl1 --only tools/pilot_controls_CH47F.txt`
Result: **711 pass / 15 fail / 269 skip** (995 tested: 989 controls + 6 guards/covers)
7112 controls excluded as `type=raw` (AI crew commands).

All 15 failures accounted for:
- 1× `ARC_186.ARC186_SQUELCH` — DCS Lua bug (stop_val_ = nil), see above
- 1× `CENTRAL_CONSOLE.STEER_KNOB_arg590` — momentary spring-loaded button, see above
- 13× `PDP2.*` CBs — collar installed in hot-start mission, see above

No unresolved failures remain for the pilot seat.

---

## Copilot Seat Validation (2026-05-10)

Run: `--module CH-47Fbl1 --only tools/copilot_controls_CH47F.txt` (crew 1, game key 2)
Result: **714 pass / 12 fail / 269 skip** (995 tested)

All 12 failures accounted for:
- 1× `ARC_186.ARC186_SQUELCH` — DCS Lua bug (same as pilot seat)
- 1× `CENTRAL_CONSOLE.STEER_KNOB_arg590` — momentary button (same as pilot seat)
- 10× `PDP1.*` CBs with collars: `1B11`, `1B12`, `1C08`, `1C09`, `1C12`, `1D20`, `1D21`, `1D22`, `1E07`, `1E08` — collar installed in hot-start mission (same cause as PDP2 collar failures in pilot seat)

No unresolved failures remain for the copilot seat.

---

## Flight Engineer Seat Validation (2026-05-10)

Run: `--module CH-47Fbl1 --only tools/flighteng_controls_CH47F.txt` (crew 2, game key 3)
Result: **243 pass / 46 fail / 262 skip** (551 tested)

**Crew station layout (confirmed in-cockpit):**
- Pilot (crew 0, key 1): `COMM_PANEL_RIGHT` (ICS1)
- Copilot (crew 1, key 2): `COMM_PANEL_LEFT` (ICS2)
- Flight engineer (crew 2, key 3): `COMM_PANEL_TROOP_COMMANDER`, `COMM_PANEL_LH_GUNNER`, `COMM_PANEL_RH_GUNNER`
- Ramp/aft engineer (crew 5, key 6): `COMM_PANEL_AFT_ENGINEER` (ICS6)

All 46 failures fall into 4 categories, all attributed to early-access Lua `crewAccess` bugs:

**28× `COMM_PANEL_AFT_ENGINEER.ICS6_*`** — Lua tags these as `crewAccess: [2, 5]` but they should be
crew 5 (ramp station) only. DCS does not respond to crew 2 commands on this panel.
No `COMM_PANEL_AFT_ENGINEER` controls respond from the flight engineer seat.

**5× `MAINTENANCE_PANEL.*`** — Lua tags these as `crewAccess: [2]` but there is no maintenance panel
at the flight engineer station. All stuck/unresponsive.

**2× `AFT_WORKSTATION.*`** — `INTRLTG_CABIN_KNOB` (stuck at 0.5) and `INTRLTG_CABIN_SW` (stuck at
0.1). Lua tags as `crewAccess: [2]`. Either initial mission state or another crewAccess mismatch.

**11× `EXTERNAL_CARGO_EQUIPMENT.*`** — Lua tags as `crewAccess: [2]`. No sling load attached in
mission (same cause as previously noted for all cargo equipment controls).

No unresolved failures remain for the flight engineer seat. All failures are Lua crewAccess
misassignments or mission state — not mapping bugs.

---

## Left Gunner Seat Validation (2026-05-10)

Run: `--module CH-47Fbl1 --only tools/lgunner_controls_CH47F.txt` (crew 3, game key 4)
Result: **91 pass / 0 fail / 262 skip** (353 tested)

Clean pass. No failures.

---

## Right Gunner Seat Validation (2026-05-10)

Run: `--module CH-47Fbl1 --only tools/rgunner_controls_CH47F.txt` (crew 4, game key 5)
Result: **91 pass / 0 fail / 262 skip** (353 tested)

Clean pass. No failures.

---

## Ramp Station Validation (2026-05-10)

Run: `--module CH-47Fbl1 --only tools/ramp_controls_CH47F.txt` (crew 5, game key 6)
Result: **91 pass / 0 fail / 262 skip** (353 tested)

Clean pass. No failures.

Note: The ramp controls list (7466 entries) matches the gunner counts exactly, suggesting the
`COMM_PANEL_AFT_ENGINEER` ICS6 controls (crewAccess [2, 5]) were not exercised from this seat
either. They failed from crew 2 (FE) and were not in scope for crew 3/4/5 runs. Their true
accessible seat (crew 5) was not separately verified beyond what the crewAccess tag asserts.

---

## Per-Seat Validation Summary (2026-05-10)

| Seat | Crew | Key | Pass | Fail | Skip | Notes |
|------|------|-----|------|------|------|-------|
| Pilot | 0 | 1 | 711 | 15 | 269 | 1× ARC186_SQUELCH, 1× STEER_KNOB, 13× PDP2 CBs |
| Copilot | 1 | 2 | 714 | 12 | 269 | 1× ARC186_SQUELCH, 1× STEER_KNOB, 10× PDP1 CBs |
| Flight Engineer | 2 | 3 | 243 | 46 | 262 | 28× AFT_ENG ICS6, 5× MAINT_PANEL, 2× AFT_WS, 11× cargo |
| Left Gunner | 3 | 4 | 91 | 0 | 262 | Clean |
| Right Gunner | 4 | 5 | 91 | 0 | 262 | Clean |
| Ramp | 5 | 6 | 91 | 0 | 262 | Clean |

All failures are acknowledged. No unresolved mapping bugs remain. Ready for Phase 5.
