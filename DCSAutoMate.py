##! /usr/bin/python -i
import sys
import socket
import time
import csv
import json
import glob
import os
import math
import importlib
import argparse # Command line parameters.
import ast # Used to parse files to find function names in modules.
import win32com.client # Used for text-to-speech.

from pywinauto.application import Application

# Returns a module.
def getModule(moduleName):
	# This little mess is needed in order to call a variable function in a variable module.
	try:
		module = [importlib.import_module('DCSAutoMateScripts.' + moduleName)] # Modules must be put into a List.
		# Immediately after importing it, reload the module.  This is needed in order to catch any changes.that may have been made while the program was running.  WARNING This is hacky and should not be used as a standard practice, but works in this case.
		importlib.reload(module[0])
		return module[0]
	except:
		print(f'Error: Script file ".\\DCSAutoMateScripts\\{moduleName}.py" not found, or could not parse file.')
		# Keep the window open after program ends.			
		input('Press enter to exit')
		quit()

# Returns a function from the given module.  e.g.: func = getFunction('myFuncName'); funcOutput = func(params);
def getFunction(module, functionName, ignoreError = False):
	try:
		func = getattr(module, functionName) # Then you can access the List index that the module is in without knowing the name of the module, and get the function using a variable name.
		return func
	except:
		if ignoreError:
			return False
		else:
			print(f'Error: Function "{functionName}" not found in ".\\DCSAutoMateScripts\\{moduleName}.py"')
			# Keep the window open after program ends.			
			input('Press enter to exit')
			quit()

def getSecToMin(numSeconds):
	mins = int(math.floor(numSeconds / 60))
	secs = int(numSeconds - (mins * 60))
	return f'{mins}m{secs:02}s'

# speakerId: 0 = MS David, 1 = MS Hazel, 2 = MS Zira
# This code adapted from: https://stackoverflow.com/questions/31167967/python-3-4-text-to-speech-with-sapi
# For more docs, see: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723609(v=vs.85)
def getTtsSpeaker(speakerId = 1):
	speaker = win32com.client.Dispatch("SAPI.SpVoice")
	voices = speaker.GetVoices()
	#for voice in voices:
		#print(voice.GetAttribute("Name"))
	#print(voices.Item(speakerId).GetAttribute("Name")) # speaker name
	speaker.Voice
	speaker.SetVoice(voices.Item(speakerId)) # set voice (see Windows Text-to-Speech settings)
	speaker.Rate
	speaker.SetRate(3) # -10 is slowest, 10 is fastest, 0 is default.
	speaker.Volume
	speaker.SetVolume(75) # 0-100, 0 is quietest, 100 is default.
	return speaker

# If asyncFlag is false, program execution will stop while speaking.
def speak(speaker, string, asyncFlag = True):
	if not config['nospeech']:
		SVSFlag = 1 if asyncFlag is True else 0 # Makes the speaking asyncronous so it doesn't hold up the script.  See https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms720892(v=vs.85)
		speaker.speak(string, SVSFlag)

######
# Seq must be a List of Dictionaries.  Each Dictionary must have {time, cmd, arg, msg}.
######
def executeSeq(seq):
	totalTime = seq[len(seq) - 1]['time'] # Total time for sequence is the time of the last command.
	print('Total script time:', totalTime, 'seconds', getSecToMin(totalTime))
	
	speaker = getTtsSpeaker()
	
	# Look through the script to find how many keyboard commands will be executed.
	numScriptKeyboardCommands = sum(1 for row in seq if row['cmd'] == 'scriptKeyboard') # https://stackoverflow.com/a/16455812
	if numScriptKeyboardCommands:
		print(f'Found {numScriptKeyboardCommands} keyboard commands in script.  Stay in cockpit until last keyboard command is executed.')
		speak(speaker, 'Stay in cockpit until last keyboard command is executed.', asyncFlag=False) # We want to make sure this message is read before any other speech in the script gets played.
	
	remainingTimeInterval = 10 # Display the remaining time every N seconds.  Must be > 1 for the code to work.
	displayedRemainingTime = False # Flag to track whether we've displayed the time for this interval yet.
	
	rowNum = 0
	executedScriptKeyboardCommands = 0
	startTime = time.time() # Start the timer immediately before starting the execution loop.
	while True:
		# When our counter gets past the last row, break out of the loop.
		if rowNum >= len(seq):
			break
			
		currentTime = time.time()
		elapsedTime = currentTime - startTime
		remainingTime = totalTime - elapsedTime
		
		#print('Elapsed time:', elapsedTime) # Prints every time around the loop, watch out.
		
		# When the remainingTime modulo interval is 0, that means we need to display the time.  After doing so, set a flag to true.  That prevents the time from being displayed repeatedly as it loops during this second.  When the modulo is not 0, it means we're on the next interval segment of countdown time, so set the flag back to false.
		if not displayedRemainingTime and int(math.ceil(remainingTime)) % remainingTimeInterval == 0 and int(math.ceil(remainingTime)) != 0:
			print('Remaining time:', getSecToMin(int(math.ceil(remainingTime))))
			displayedRemainingTime = True
			if int(math.ceil(remainingTime)) % 60 == 0:
				mins = int(math.floor(math.ceil(remainingTime) / 60))
				plural = 's' if mins > 1 else ''
				speak(speaker, f'{mins} minute{plural} remaining')
		elif int(math.ceil(remainingTime)) % remainingTimeInterval != 0:
			displayedRemainingTime = False
		
		# Get the current command.
		command = seq[rowNum]
		# If the time since we started is greater than the command we're executing, run that command and go on to the next one.
		if elapsedTime > command['time']:
			cmd = command['cmd']
			arg = command['arg']
			msg = command['msg']
			
			print('Time:', str(round(elapsedTime, 1)) + '\t', end='')
			
			if cmd == 'scriptKeyboard':
				print('Pressing key\t\t', arg, end='')
				# FIXME This steals focus onto the window we're sending the command to.  Not sure if there's a way to prevent that...?
				# FIXME I cannot get it to press RAlt or RCtrl.  LAlt, LCtrl, LShift, LWin, RWin, and RShift work fine, but not RMENU, VK_RMENU, or VK_RCONTROL, and I don't know why.  Therefore any keyboard key we need to press that relies on RAlt or RCtrl will need to be remapped in the game.
				if not config['debug']:
					app.window().type_keys(arg)
				executedScriptKeyboardCommands += 1
				if executedScriptKeyboardCommands == numScriptKeyboardCommands:
					print(' - Last keyboard command executed, you may safely leave the cockpit.')
					speak(speaker, 'Last keyboard command executed, you may safely leave the cockpit.')
			elif cmd == 'scriptSpeech':
				print(f'Speaking:\t\t "{arg}"', end='')
				speak(speaker, arg)
			elif cmd != '':
				print('DCS-BIOS command:\t', cmd, arg, end='')
				if not config['debug']:
					sock.sendto(bytes(str(cmd) + ' ' + str(arg) + '\n', "utf-8"), ('127.0.0.1', 7778))
			
			if msg != '':
				if cmd:
					print(' -', msg, end='')
				else:
					print('Msg:\t\t\t', msg, end='')
			
			print(flush=True)
			
			# Go on to the next command.
			rowNum += 1
		time.sleep(0.01) # Sleep for a short time to save CPU cycles, there's no need to run this loop continuously as fast as possible.
	
	print('Script complete')
	speak(speaker, 'Script complete', asyncFlag=False)

def getModuleNames():
	modules = [] # List type
	for filepath in glob.iglob('./DCSAutoMateScripts/*.py'):
		basename = os.path.basename(filepath)
		filenameNoExt = os.path.splitext(basename)[0]
		
		modules.append(filenameNoExt)
	return modules

# Returns List of function names in the passed moduleName (no extension).
# Code adapted from https://stackoverflow.com/a/46105518 .
def getFunctionNamesOLD(moduleName):
	source = open(f'./DCSAutoMateScripts/{moduleName}.py').read()
	functions = [f.name for f in ast.parse(source).body if isinstance(f, ast.FunctionDef)]
	#print(functions)
	return functions

# Returns Dictionary of function names that are runnable scripts (as opposed to utility functions in the module).
def getFunctionNames(moduleName):
	module = getModule(moduleName)
	functionNames = getFunction(module, 'getScriptFunctions')()
	return functionNames

def showModuleMenu():
	moduleNames = getModuleNames()
	print('0: Quit')
	for i, moduleName in enumerate(moduleNames):
		print(f'{i + 1}: {moduleName}')
	moduleNum = int(input('Select a script file (number): '))
	if moduleNum == 0:
		moduleName = False
	else:
		moduleName = moduleNames[moduleNum - 1]
	return moduleName

def showFunctionMenu(moduleName):
	functionNames = getFunctionNames(moduleName)
	print('0: Back')
	for i, (title, functionName) in enumerate(functionNames.items()):
		print(f'{i + 1}: {title}')
	functionNum = int(input('Select a script function to run (number): '))
	if functionNum == 0:
		functionName = False
	else:
		# In order to access a Dictionary item by numerical index, you need to make a List of the .values().
		functionName = list(functionNames.values())[functionNum - 1]
	return functionName

def makeDefaultConfigFile():
	jsonConfig = """{
	"debug": false,
	"nospeech": false,
	"dvorak": false,
	"dcspath": []
}"""
	with open('DCSAutoMateConfig.json', 'w') as configFileHandle:
		configFileHandle.write(jsonConfig)

def getConfigFromFile():
	import json
	configFile = './DCSAutoMateConfig.json'
	if not os.path.isfile(configFile):
		print('Creating default config file.')
		makeDefaultConfigFile()
	with open(configFile) as configFileHandle:
		try:
			config = json.load(configFileHandle)
		except:
			print("Couldn't parse DCSAutoMateConfig.json, please check syntax.")
			quit()
	if type(config['dcspath']) is not list:
		config['dcspath'] = [
			config['dcspath']
		]
	return config
	


###############################################################################
###############################################################################
###############################################################################



# When running this program as an exe, we need to have its own path appended to the sys.path in order for it to find script files in the DCSAutoMateScripts subfolder.
applicationPath = os.path.dirname(sys.executable)
sys.path.append(applicationPath)

# First, get the config from the .json file.  If the file doesn't exist, this will create it with the defaults.  Anything set up here may be overridden later by command-line parameters.
config = getConfigFromFile()

# Initialize parser for command line arguments.
parser = argparse.ArgumentParser(
	prog = 'DCS AutoMate',
	description = 'Sends scripted commands to DCS, allowing complete cockpit scripting and automation.',
	#epilog = 'my epilog'
)
parser.add_argument(
	'--file',
	action = 'store',
	help = "Script filename, without extension.  Must be a .py file in the ./DCSAutoMateScripts subfolder."
)
parser.add_argument(
	'--function',
	action = 'store',
	help = "Function name in script.  Function must return a list of dictionaries, one dictionary per command to be run."
)
parser.add_argument(
	'--debug',
	action = 'store_true', # Stores True if passed, otherwise False.
	help = "If passed, script will be run normally, but without actually sending any commands to DCS."
)
parser.add_argument(
	'--nospeech',
	action = 'store_true', # Stores True if passed, otherwise False.
	help = "If passed, text-to-speech commands in the script will not be executed."
)
parser.add_argument(
	'--dvorak',
	action = 'store_true', # Stores True if passed, otherwise False.
	help = "If passed, sets a flag for the scripts to detect whether keyboard is using Dvorak layout."
)
parser.add_argument(
	'--dcspath',
	action = 'store',
	help = "If passed, specifies the full path to the DCS.exe file so we can find the DCS window to send commands to."
)

args = parser.parse_args()
#print(args.debug)
moduleName = args.file
functionName = args.function
if args.debug:
	config['debug'] = args.debug
if args.nospeech:
	config['nospeech'] = args.nospeech
if args.dvorak:
	config['dvorak'] = args.dvorak
if args.dcspath:
	config['dcspath'] = [
		args.dcspath
	]

isCommandLine = False
if args.file and args.function:
	isCommandLine = True
	moduleName = args.file
	functionName = args.function

# Pass in script file name (file name only, no path, no extension) and function in script file to call.
# Script file function must return a Python list where each element is a dictionary:
# {"time": <time after start that the command will execute>, "cmd": <command to be executed>, "arg": <argument or parameter for command>, "msg": <optional message to display when executed>}
# Any of the dictionary fields except time may be left blank (empty string).

while True:
	if not isCommandLine:
		moduleName = showModuleMenu()
		if moduleName == False:
			quit()
		functionName = showFunctionMenu(moduleName)
		if functionName == False:
			continue

	module = getModule(moduleName)
	func = getFunction(module, functionName)

	#debug = True
	if config['debug']:
		print('RUNNING IN DEBUG MODE, nothing will be sent to the game')

	seq = func(config) # Then you can execute the function to build the command sequence.
	#print(seq)

	getInfoFunc = getFunction(module, 'getInfo', ignoreError = True)
	if getInfoFunc:
		print(getInfoFunc())

	# Create UDP socket to send DCS BIOS commands.
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	# Find the open DCS window to send keyboard commands.
	if not config['debug']:
		appFound = False
		if config.get('dcspath') and config.get('dcspath') != []: # Use config.get('dcspath') instead of config['dcspath'] to avoid key not exists error.
			for dcsPath in config['dcspath']:
				try:
					print(f"Trying to connect to DCS window by path: {dcsPath}")
					app = Application().connect(path=dcsPath)
					appFound = True;
					break
				except:
					continue
			# Fallthrough
			if not appFound:
				print("Couldn't find any active DCS window by path.  Trying by title...")
		
		if not appFound:
			try:
				print('Trying to connect to DCS window by title: "DCS.openbeta"...')
				app = Application().connect(title="DCS.openbeta")
			except:
				try:
					print('Trying to connect to DCS window by title: "DCS"')
					app = Application().connect(title="DCS")
				except:
					print("Couldn't find any active DCS window.  Please make sure DCS is running before running script, or use debug flag.")
					quit('')

	try:
		executeSeq(seq)
	except:
		print("Error executing script:")
		# Keep the window open after program ends.			
		input('Press enter to exit')
		quit()

	if isCommandLine:
		quit()


# Keep the window open after program ends.			
#input('Press enter to exit')
