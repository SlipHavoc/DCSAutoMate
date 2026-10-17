from engine.simCommands import isCommsMenuCommand, parseSimCommandEntry, resolveSimCommand, rowUsesCommsMenu, simCommandProblem


def test_commsMenuCommandsByNameOrNumber():
	assert isCommsMenuCommand('ICommandMenuItem8') is True
	assert isCommsMenuCommand(978) is True # ICommandMenuExit
	assert isCommsMenuCommand('iCommandToggleCommandMenu') is True
	assert isCommsMenuCommand('iCommandLeftEngineStart') is False
	assert isCommsMenuCommand(311) is False
	assert isCommsMenuCommand('home') is False

def test_onlySimCommandRowsUseTheCommsMenu():
	assert rowUsesCommsMenu({'cmd': 'scriptSimCommand', 'arg': 'ICommandMenuItem12'}) is True
	assert rowUsesCommsMenu({'cmd': 'scriptSimCommand', 'arg': 'iCommandRightEngineStart'}) is False
	assert rowUsesCommsMenu({'cmd': 'scriptText', 'arg': 'ICommandMenuItem12'}) is False


def test_wrongCaseNameIsRejectedWithTheRightSpelling():
	assert resolveSimCommand('iCommandMenuItem8') is None
	assert "did you mean 'ICommandMenuItem8'" in simCommandProblem({'arg': 'iCommandMenuItem8'})
	assert "did you mean 'iCommandPlaneCollectiveStop'" in simCommandProblem({'arg': 632, 'hold': 1, 'stop': 'ICommandPlaneCollectiveStop'})


def test_numberPassesThrough():
	assert resolveSimCommand(1234) == 1234

def test_nameResolvesFromDcsTable():
	assert resolveSimCommand('iCommandLeftEngineStop') == 313
	assert resolveSimCommand('iCommandThrottleStop') == 1034

def test_unknownNameIsNone():
	assert resolveSimCommand('iCommandNoSuchThing') is None

def test_nonNumericTypesAreNone():
	assert resolveSimCommand(True) is None
	assert resolveSimCommand(3.5) is None
	assert resolveSimCommand(None) is None


# parseSimCommandEntry: what the Control Panel's Send Sim Command row typed, as (commandId, value, error).
def test_typedNameResolvesWithNoValue():
	assert parseSimCommandEntry(' iCommandLeftEngineStop ', '') == (313, None, '')

def test_typedNumberIsUsedAsIs():
	assert parseSimCommandEntry('1034', '') == (1034, None, '')

def test_typedValueIsANumber():
	assert parseSimCommandEntry('iCommandThrottleStop', '-0.5') == (1034, -0.5, '')

def test_badValueIsAnError():
	commandId, value, error = parseSimCommandEntry('iCommandThrottleStop', 'half')
	assert commandId is None and value is None
	assert "'half'" in error

def test_wrongCaseNameGetsSpellingHint():
	commandId, _, error = parseSimCommandEntry('iCommandMenuItem8', '')
	assert commandId is None
	assert "did you mean 'ICommandMenuItem8'" in error

def test_emptyNameIsAnError():
	assert parseSimCommandEntry('  ', '')[2] != ''
