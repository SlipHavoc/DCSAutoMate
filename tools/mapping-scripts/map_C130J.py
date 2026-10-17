"""Control-mapping generator for the C-130J-30 Super Hercules.

Reads config/nativeExtractions/C-130J-30.json and writes
config/controlMappings/C-130J-30.json using the explicit archetype dispatch.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, buttonOrAxis, incrementalTumb,
)

def customFirePull(elem, indices, ctx):
	controls = buttonOrAxis(elem, indices, ctx)
	if controls:
		for canonical, control in list(controls.items()):
			if canonical.endswith('_pull') or 'pull' in canonical:
				control['type'] = 'discrete'
				control['step'] = 1.0
				control['positions'] = 2
	return controls

def customMultiswitch(elem, indices, ctx):
	controls = simpleDiscrete(elem, indices, ctx)
	if controls:
		for canonical, control in list(controls.items()):
			if control.get('step') == 2.0 and control.get('argLim') == [-1.0, 1.0]:
				control['argLim'] = [-2.0, 2.0]
				control['step'] = 4.0
				control['positions'] = 2
				if 'indicatorArgLim' in control:
					del control['indicatorArgLim']
	return controls

def customVisor(elem, indices, ctx):
	controls = buttonOrAxis(elem, indices, ctx)
	if controls:
		for canonical, control in list(controls.items()):
			if 'shade_show_hide' in canonical:
				control['argLim'] = [-1.0, 1.0]
				control['step'] = 2.0
				control['positions'] = 2
				if 'indicatorArgLim' in control:
					del control['indicatorArgLim']
	return controls

def customHudBtn(elem, indices, ctx):
	controls = simpleDiscrete(elem, indices, ctx)
	if controls:
		for canonical, control in list(controls.items()):
			control['argLim'] = [0.0, 0.25]
			control['step'] = 0.25
			control['positions'] = 2
	return controls

def customRotary(elem, indices, ctx):
	controls = simpleDiscrete(elem, indices, ctx)
	if controls:
		for canonical, control in list(controls.items()):
			if 'ref_select' in canonical:
				control['argLim'] = [-0.8, 0.8]
				control['step'] = 0.4
				control['positions'] = 5
	return controls

HELPER_MAP = {
	# Momentary and simple discrete switches/buttons
	'adi_cage':                                      buttonOrAxis, # BTN+LEV multi-group
	'air_deflector':                                 simpleDiscrete, # TUMB+TUMB discrete
	'amu_key':                                       simpleDiscrete, # BTN momentary
	'at_disconnect':                                 simpleDiscrete, # BTN momentary
	'base_btn':                                      simpleDiscrete, # BTN momentary
	'base_btn_cycle':                                simpleDiscrete, # BTN+BTN cycles
	'base_btn_cycle2':                               simpleDiscrete, # TUMB+TUMB cycles (galley props)
	'base_btn_cycle3':                               simpleDiscrete, # TUMB+TUMB cycles, no arg (light toggles)
	'base_btn_cycle_release':                        simpleDiscrete, # TUMB+TUMB cycles with stop (galley props)
	'boost_guard':                                   simpleDiscrete, # TUMB+TUMB discrete
	'cable_interaction':                             simpleDiscrete, # BTN+BTN momentary
	'cni_brt':                                       simpleDiscrete, # BTN momentary
	'cni_key_no_stop':                               simpleDiscrete, # BTN momentary
	'display_rocker_hdd':                            simpleDiscrete, # BTN momentary
	'emergency_trim':                                simpleDiscrete, # BTN momentary
	'emg_ext_light':                                 simpleDiscrete, # BTN momentary
	'fire_pull':                                     customFirePull, # TUMB+TUMB+LEV multi-group
	'flap_switch':                                   continuousAxis, # LEV axis
	'fuel_transfer':                                 simpleDiscrete, # TUMB+TUMB discrete
	'fuel_xfeed':                                    simpleDiscrete, # TUMB+TUMB discrete
	'gear_handle':                                   simpleDiscrete, # TUMB+TUMB discrete
	'generator_switch':                              simpleDiscrete, # TUMB+TUMB discrete
	'glare_activate':                                customVisor, # LEV+TUMB multi-group
	'guard':                                         simpleDiscrete, # TUMB+TUMB discrete
	'hud_brt_knob':                                  buttonOrAxis, # BTN+BTN+LEV multi-group
	'hud_btn':                                       customHudBtn, # BTN momentary
	'hud_latch':                                     simpleDiscrete, # TUMB+TUMB discrete
	'ics_knob':                                      buttonOrAxis, # TUMB+TUMB+LEV multi-group
	'knob_360':                                      continuousAxis, # LEV relative axis
	'knob_360_0_1':                                  continuousAxis, # LEV relative axis
	'knob_360_press':                                buttonOrAxis, # BTN+LEV multi-group
	'knob_fixed':                                    buttonOrAxis, # LEV+BTN multi-group
	'knob_rot':                                      continuousAxis, # LEV continuous axis
	'knob_rot_rel':                                  continuousAxis, # LEV relative axis
	'landing_lights':                                simpleDiscrete, # TUMB+TUMB discrete
	'landing_lights_motor':                          simpleDiscrete, # TUMB+TUMB discrete
	'lsgi_btn':                                      simpleDiscrete, # BTN momentary
	'master_caution':                                simpleDiscrete, # BTN momentary
	'master_warning':                                simpleDiscrete, # BTN momentary
	'microwave_key':                                 simpleDiscrete, # BTN momentary
	'multiswitch':                                   customMultiswitch, # TUMB+TUMB discrete
	'multiswitch_stop':                              incrementalTumb, # TUMB+TUMB sign-driven incremental (engine start, APU)
	'oil_flap_switch':                               simpleDiscrete, # BTN momentary (oil cooler flap, command-only)
	'oil_flap_switch_open_close':                    simpleDiscrete, # BTN with stop (oil cooler flap open/close)
	'one_way_rocker':                                simpleDiscrete, # BTN momentary
	'oxygen_switch':                                 customMultiswitch, # TUMB+TUMB discrete
	'parking_brake':                                 simpleDiscrete, # TUMB+TUMB discrete
	'push_button':                                   simpleDiscrete, # BTN momentary
	'ref_btn':                                       simpleDiscrete, # BTN momentary
	'rocker_centering':                              simpleDiscrete, # TUMB+TUMB discrete
	'rotary':                                        customRotary, # TUMB+TUMB discrete
	'rudder_trim':                                   simpleDiscrete, # TUMB+TUMB discrete
	'scroll_point_axis':                             continuousAxis, # LEV axis
	'stby_altim':                                    continuousAxis, # LEV relative axis
	'tab':                                           simpleDiscrete, # BTN+BTN momentary
	'three_pos_spring_load_on':                      simpleDiscrete, # TUMB+TUMB discrete
	'three_pos_spring_load_on_inv':                  simpleDiscrete, # TUMB+TUMB discrete
	'three_pos_switch_spring':                       simpleDiscrete, # TUMB+TUMB discrete
	'two_pos_switch':                                simpleDiscrete, # TUMB+TUMB discrete
	'two_pos_switch_ap':                             simpleDiscrete, # TUMB+TUMB discrete
	'two_pos_switch_cargo':                          simpleDiscrete, # TUMB+TUMB discrete
	'two_pos_switch_rev':                            simpleDiscrete, # TUMB+TUMB discrete
	'two_pos_switch_spring':                         simpleDiscrete, # TUMB+TUMB discrete
	'wiper':                                         simpleDiscrete, # TUMB+TUMB discrete
}

if __name__ == '__main__':
	runMapping('C-130J-30', HELPER_MAP)
