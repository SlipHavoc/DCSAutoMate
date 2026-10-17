import json
import os

from utils.appPaths import appBaseDir

COMMS_MENU_TOGGLE = 'iCommandToggleCommandMenu'
simCommands = None
commsMenuIds = None

def loadSimCommands():
	global simCommands
	if simCommands is None:
		with open(os.path.join(appBaseDir(), 'config', 'simCommands.json'), encoding='utf-8') as f:
			simCommands = json.load(f)
	return simCommands

def resolveSimCommand(arg):
	"""Returns the iCommand number for a number or a name from config/simCommands.json, or None."""
	if isinstance(arg, bool):
		return None
	if isinstance(arg, int):
		return arg
	if not isinstance(arg, str):
		return None
	return loadSimCommands().get(arg)

def spellingHint(name):
	"""Returns ' (did you mean ...?)' when name matches a known command except for case, else ''."""
	if not isinstance(name, str):
		return ''
	matches = [known for known in loadSimCommands() if known.lower() == name.lower()]
	return f" (did you mean '{matches[0]}'? Names are case-sensitive)" if matches else ''

def parseSimCommandEntry(nameText, valueText=''):
	"""(commandId, value, error) from a typed iCommand name or number and an optional value; error is '' if it can be sent."""
	name = (nameText or '').strip()
	if not name:
		return None, None, 'Type an iCommand name or number.'
	commandId = int(name) if name.isdigit() else resolveSimCommand(name)
	if commandId is None:
		return None, None, f"'{name}' is not a known iCommand name{spellingHint(name)}."
	valueText = (valueText or '').strip()
	if not valueText:
		return commandId, None, ''
	try:
		return commandId, float(valueText), ''
	except ValueError:
		return None, None, f"The value must be a number, got '{valueText}'."

def isCommsMenuCommand(arg):
	"""True for the comms menu's sim commands, by name or number; the player's own comms menu use would throw them off."""
	global commsMenuIds
	if commsMenuIds is None:
		commsMenuIds = {number for name, number in loadSimCommands().items() if name.startswith('ICommandMenu') or name == COMMS_MENU_TOGGLE}
	return resolveSimCommand(arg) in commsMenuIds

def rowUsesCommsMenu(command):
	return command.get('cmd') == 'scriptSimCommand' and isCommsMenuCommand(command.get('arg'))

def simCommandProblem(command):
	"""Returns why a scriptSimCommand row can't be sent, or None if it can."""
	arg = command.get('arg')
	if resolveSimCommand(arg) is None:
		if isinstance(arg, str):
			return f"scriptSimCommand '{arg}' is not a known iCommand name{spellingHint(arg)} (see config/simCommands.json)."
		return f'scriptSimCommand needs an iCommand number or name, got {arg!r}.'
	hold = command.get('hold')
	stop = command.get('stop')
	release = command.get('release')
	if release is not None:
		if release is not True:
			return f'scriptSimCommand release must be True, got {release!r}.'
		if hold is not None or stop is not None or command.get('value') is not None:
			return "scriptSimCommand release can't be combined with hold, stop or value."
		return None
	if hold is None:
		if stop is not None:
			return 'scriptSimCommand stop needs hold (the seconds to hold the command before sending stop).'
		return None
	if hold is not True and (isinstance(hold, bool) or not isinstance(hold, (int, float)) or hold <= 0):
		return f'scriptSimCommand hold must be a positive number of seconds, got {hold!r}.  Use hold=True to hold until a release step.'
	if stop is not None and resolveSimCommand(stop) is None:
		return f'scriptSimCommand stop {stop!r} is not a known iCommand{spellingHint(stop)}.'
	return None
