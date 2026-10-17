import os
import sys
import importlib
import traceback

class ScriptManager:
	SCRIPT_PATH = './DCSAutoMateScripts'

	def __init__(self):
		pass

	def getModules(self):
		"""Returns a list of available script modules (filenames without extension)."""
		if not os.path.exists(self.SCRIPT_PATH):
			return []
		modules = [f[:-3] for f in os.listdir(self.SCRIPT_PATH) if f.endswith('.py') and f != '__init__.py']
		return modules

	def getScriptData(self, moduleName):
		"""Loads the script metadata from the specified module."""
		try:
			# Ensure the script path is in sys.path
			if self.SCRIPT_PATH not in sys.path:
				sys.path.append(self.SCRIPT_PATH)

			# Import the module
			module = importlib.import_module(f'DCSAutoMateScripts.{moduleName}')
			importlib.reload(module)

			if hasattr(module, 'getScriptData'):
				return module.getScriptData()
			else:
				return {'scripts': []}
		except Exception as e:
			# We might want to log this or re-raise depending on how we want to handle it in the UI
			print(f"Error loading module {moduleName}: {e}")
			return {'scripts': []}

	def getModule(self, moduleName):
		"""Imports (reloading, so edits are picked up) and returns the script module."""
		module = importlib.import_module(f'DCSAutoMateScripts.{moduleName}')
		importlib.reload(module)
		return module

	def getScriptVars(self, scriptData, scriptName):
		"""Returns the variables dictionary for a specific script."""
		for script in scriptData.get('scripts', []):
			if script['name'] == scriptName:
				return script.get('vars', {})
		return {}

	def loadScriptFunction(self, moduleName, scriptName):
		"""Loads the function object for the specified script."""
		try:
			module = importlib.import_module(f'DCSAutoMateScripts.{moduleName}')
			importlib.reload(module)
			scriptData = module.getScriptData()

			# Find the selected script and its corresponding function
			selectedScript = next((script for script in scriptData['scripts'] if script['name'] == scriptName), None)

			if selectedScript:
				functionName = selectedScript['function']
				scriptFunction = getattr(module, functionName)
				return scriptFunction, module
			else:
				return None, None
		except Exception as e:
			raise Exception(f"Error loading script function: {e}")

	def getScriptInfo(self, module):
		"""Returns the script info string if available."""
		try:
			if hasattr(module, 'getInfo'):
				return module.getInfo()
		except:
			pass
		return None
