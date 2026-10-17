# Mi-8MT multi-position discrete audit

For each control, verify that the integer position index used in `Mi-8MTV2.py`
still selects the intended cockpit position under the canonical positionMap.
BIOS positions are listed in the order DCS BIOS enumerated them; canonical
positionMap (when present) reflects the new mapping order.

## `INV_115V_SWITCH` → `ELEC_INTERFACE.PTR-EEP-TMB-PO`

BIOS positions:
- 0: MANUAL
- 1: OFF
- 2: AUTO

Canonical positions count: 3

## `INV_36V_SWITCH` → `ELEC_INTERFACE.PTR-EEP-TMB-PT`

BIOS positions:
- 0: MANUAL
- 1: OFF
- 2: AUTO

Canonical positions count: 3

## `TRANS_36V_SWITCH` → `ELEC_INTERFACE.PTR-APP-TMB-TRNS`

BIOS positions:
- 0: MAIN
- 1: OFF
- 2: AUXILIARY

Canonical positions count: 3

## `FUEL_REFUEL` → `FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-CONTR`

BIOS positions:
- 0: REFUEL
- 1: OFF
- 2: CHECK

Canonical positions count: 3

## `APU_START_MODE` → `ENGINE_INTERFACE.PTR-CPE-TMB-TURBOSTART-ST`

BIOS positions:
- 0: START
- 1: COLD CRANKING
- 2: FALSE START

Canonical positions count: 3

## `ENG_SEL` → `ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-LFTRGT`

BIOS positions:
- 0: LEFT
- 1: OFF
- 2: RIGHT

Canonical positions count: 3

## `ENG_START_MODE` → `ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-ROLL`

BIOS positions:
- 0: START
- 1: OFF
- 2: COLD CRANKING

Canonical positions count: 3

## `ENG_IGN_CHK` → `ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-TEST`

BIOS positions:
- 0: LEFT
- 1: OFF
- 2: RIGHT

Canonical positions count: 2

## `ENG_LEFT_FREE_TURB_RPM` → `ENGINE_INTERFACE.PTR-STKSGR-TMB-RPM-LEFT`

BIOS positions:
- 0: MORE
- 1: OFF
- 2: LESS

Canonical positions count: 2

## `ENG_RIGHT_FREE_TURB_RPM` → `ENGINE_INTERFACE.PTR-STKSGR-TMB-RPM-RIGHT`

BIOS positions:
- 0: MORE
- 1: OFF
- 2: LESS

Canonical positions count: 2

## `ENG_LEFT_FT_CHECK` → `ENGINE_INTERFACE.PTR-APP-TMB-ST-L`

BIOS positions:
- 0: ST1
- 1: WORK
- 2: ST2

Canonical positions count: 2

## `ENG_RIGHT_FT_CHECK` → `ENGINE_INTERFACE.PTR-APP-TMB-ST-R`

BIOS positions:
- 0: ST1
- 1: WORK
- 2: ST2

Canonical positions count: 2

## `ENG_CT_CHECK` → `ENGINE_INTERFACE.PTR-APP-TMB-TKLR`

BIOS positions:
- 0: RIGHT
- 1: WORK
- 2: LEFT

Canonical positions count: 2

## `SAS_CHK` → `SYS_CONTROLLER.PTR-APP-TMB-TEST`

BIOS positions:
- 0: LAMPS
- 1: OFF
- 2: FLASHER

Canonical positions count: 3

## `LGHT_ANO` → `NAVLIGHT_SYSTEM.PTR-RSPE-TMB-ANO`

BIOS positions:
- 0: BRIGHT
- 1: OFF
- 2: DIM

Canonical positions count: 3

## `LGHT_FRM` → `NAVLIGHT_SYSTEM.PTR-RSPE-TMB-LGTWING`

BIOS positions:
- 0: BRIGHT
- 1: OFF
- 2: DIM

Canonical positions count: 3

## `LGHT_L_LAND` → `NAVLIGHT_SYSTEM.PTR-LEFT-TAXI-L-POS-SW`

BIOS positions:
- 0: LIGHT
- 1: OFF
- 2: RETRACT

Canonical positions count: 3

## `LGHT_R_LAND` → `NAVLIGHT_SYSTEM.PTR-LEFT-TAXI-R-POS-SW`

BIOS positions:
- 0: LIGHT
- 1: OFF
- 2: RETRACT

Canonical positions count: 3

## `LGHT_L_CEIL` → `LIGHT_SYSTEM.PTR-LES-TMB-PLF`

BIOS positions:
- 0: RED
- 1: OFF
- 2: WHITE

Canonical positions count: 3

## `LGHT_R_CEIL` → `LIGHT_SYSTEM.PTR-RES-TMB-PLF`

BIOS positions:
- 0: RED
- 1: OFF
- 2: WHITE

Canonical positions count: 3

## `KO50_MODE` → `HEATER_KO50.PTR-RPE-TMB-KO50MODE`

BIOS positions:
- 0: MANUAL
- 1: OFF
- 2: AUTO

Canonical positions count: 3

## `KO50_REGIME` → `HEATER_KO50.PTR-RPE-TMB-KO50FILL`

BIOS positions:
- 0: FILLING
- 1: FULL
- 2: MEDIUM

Canonical positions count: 3

## `FUEL_METER_SWITCH` → `FUELSYS_INTERFACE.PTR-FUEL-LVR-MODE`

BIOS positions:
- 0: OFF
- 1: SUM
- 2: LEFT
- 3: RIGHT
- 4: FEED
- 5: ADDITIONAL

Canonical positions count: 6

## `PYRO_L` → `WEAPON_SYS.PTR-LPE-TMB-PYRO-L`

BIOS positions:
- 0: OFF
- 1: I
- 2: II
- 3: III

Canonical positions count: 4

## `PYRO_R` → `WEAPON_SYS.PTR-LPE-TMB-PYRO-R`

BIOS positions:
- 0: OFF
- 1: I
- 2: II
- 3: III

Canonical positions count: 4

## `FIRE_CHECK_CIRC` → `FIRE_EXTING_INTERFACE.PTR-CPE-LVR-CONTR-MODE`

BIOS positions:
- 0: OFF
- 1: CONTROL
- 2: 1
- 3: 2
- 4: 3
- 5: 4
- 6: 5
- 7: 6

Canonical positions count: 8

## `RADIO_SEL_L` → `SPU_7.PTR-LAZS-LVR-MODES`

BIOS positions:
- 0: R-863
- 1: JADRO-1A
- 2: R-828
- 3: NF
- 4: ARC-9
- 5: ARC-UD Left

Canonical positions count: 6

## `RADIO_SEL_R` → `SPU_7.PTR-RAZS-LVR-MODES002`

BIOS positions:
- 0: R-863
- 1: JADRO-1A
- 2: R-828
- 3: NF
- 4: ARC-9
- 5: ARC-UD Right

Canonical positions count: 6

## `JADR1A_MODE` → `JADRO_1A.PTR-ADDSECPLT-LVR-ONOFF`

BIOS positions:
- 0: OFF
- 1: OM
- 2: AM

Canonical positions count: 3

## `ARCUD_MODE` → `ARC_UD.PTR-RPE-LVR-ARKMODE1`

BIOS positions:
- 0: OFF
- 1: NARROW
- 2: WIDE
- 3: PULSE
- 4: RC

Canonical positions count: 5

## `ARCUD_CHL` → `ARC_UD.PTR-RPE-LVR-ARKMODE2`

BIOS positions:
- 0: 1
- 1: 2
- 2: 3
- 3: 4
- 4: 5
- 5: 6

Canonical positions count: 6

## `ARC9_MODE` → `ARC_9.PTR-RPE-LVR-FRQMODE`

BIOS positions:
- 0: OFF
- 1: COMP
- 2: ANT
- 3: LOOP

Canonical positions count: 4

## `GMC_CTRL_SWITCH` → `GMK1A.PTR-RPE-LVR-CRDCONTR`

BIOS positions:
- 0: 0
- 1: CONTROL
- 2: 300

Canonical positions count: 2

## `STC_PRS_SYSTEM` → `FM_PROXY.PTR-STAT-PRESS`

BIOS positions:
- 0: LEFT
- 1: COMMON
- 2: RIGHT

Canonical positions count: 3

## `CMD_FLARE_SEL` → `UV_26.PTR-UV26-BOARD`

BIOS positions:
- 0: LEFT
- 1: BOTH
- 2: RIGHT

Canonical positions count: 3

## `ARC_9_LOOP` → `ARC_9.PTR-RPE-TMB-FRQFRAME`

BIOS positions:
- 0: LEFT
- 1: OFF
- 2: RIGHT

Canonical positions count: 2

## `IFF_MODE_SELECTOR` → `IFF.PTR-LSPE-LVR-MODE`

BIOS positions:
- 0: AUTO
- 1: KD
- 2: +-15
- 3: KP

Canonical positions count: 4
