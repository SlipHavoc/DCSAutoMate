import os
import shutil
from PySide6 import QtWidgets

from utils.appPaths import appBaseDir


class DcsScriptsInstaller:
	@staticmethod
	def getAppBaseDir():
		return appBaseDir()

	@staticmethod
	def getSourcePaths(appBaseDir):
		return {
			'export': os.path.join(appBaseDir, 'Scripts', 'DCSAutoMate', 'DCSAutoMateExport.lua'),
			'hook': os.path.join(appBaseDir, 'Scripts', 'Hooks', 'DCSAutoMateHook.lua'),
			'dlg': os.path.join(appBaseDir, 'Scripts', 'DCSAutoMate', 'DCSAutoMateMonitorWindow.dlg'),
			'hookSettings': os.path.join(appBaseDir, 'Scripts', 'DCSAutoMate', 'DCSAutoMateHookSettings.lua'),
			'exportSettings': os.path.join(appBaseDir, 'Scripts', 'DCSAutoMate', 'DCSAutoMateExportSettings.lua'),
		}

	@staticmethod
	def getExistingDcsSavedGamesFolders(config):
		overridePath = str((config or {}).get('dcsSavedGamesOverride', '') or '').strip()
		if overridePath != '':
			path = os.path.expandvars(overridePath)
			if os.path.exists(path):
				return [('Override', path)]

		userProfile = os.environ.get('USERPROFILE', '')
		savedGamesRoot = os.path.join(userProfile, 'Saved Games')
		candidates = [
			('DCS', os.path.join(savedGamesRoot, 'DCS')),
			('DCS.openbeta', os.path.join(savedGamesRoot, 'DCS.openbeta')),
		]

		found = []
		for name, path in candidates:
			if os.path.exists(path):
				found.append((name, path))
		return found

	@staticmethod
	def promptForInstallTargets(parentWindow, folders):
		if len(folders) == 0:
			QtWidgets.QMessageBox.critical(parentWindow, 'Error', "Could not find 'DCS' or 'DCS.openbeta' under Saved Games.")
			return []

		if len(folders) == 1:
			return [folders[0][1]]

		nameToPath = {name: path for name, path in folders}

		box = QtWidgets.QMessageBox(parentWindow)
		box.setIcon(QtWidgets.QMessageBox.Icon.Question)
		box.setWindowTitle('Install DCS Scripts')
		box.setText('Multiple DCS Saved Games folders were found. Where do you want to install the DCSAutoMate scripts?')

		dcsButton = box.addButton('DCS', QtWidgets.QMessageBox.ButtonRole.AcceptRole)
		openbetaButton = box.addButton('DCS.openbeta', QtWidgets.QMessageBox.ButtonRole.AcceptRole)
		bothButton = box.addButton('Both', QtWidgets.QMessageBox.ButtonRole.AcceptRole)
		cancelButton = box.addButton('Cancel', QtWidgets.QMessageBox.ButtonRole.RejectRole)
		box.setDefaultButton(cancelButton)

		box.exec()
		clicked = box.clickedButton()

		if clicked == cancelButton:
			return []
		if clicked == bothButton:
			return list(nameToPath.values())
		if clicked == openbetaButton:
			return [nameToPath.get('DCS.openbeta')]
		return [nameToPath.get('DCS')]

	@staticmethod
	def confirmOverwrite(parentWindow, targetPaths):
		dofileLine = r'dofile(lfs.writedir()..[[Scripts\DCSAutoMate\DCSAutoMateExport.lua]])'
		newFileLines = []
		overwriteLines = []
		exportLuaUpdates = []

		for targetPath in targetPaths:
			scriptsDir = os.path.join(targetPath, 'Scripts')
			hooksDir = os.path.join(scriptsDir, 'Hooks')
			dcsAutoMateDir = os.path.join(scriptsDir, 'DCSAutoMate')
			folderName = os.path.basename(targetPath)

			# Files that are always copied (overwritten if they exist, newly installed if not).
			alwaysCopied = [
				(os.path.join(hooksDir, 'DCSAutoMateHook.lua'), r'Scripts\Hooks\DCSAutoMateHook.lua'),
				(os.path.join(dcsAutoMateDir, 'DCSAutoMateExport.lua'), r'Scripts\DCSAutoMate\DCSAutoMateExport.lua'),
				(os.path.join(dcsAutoMateDir, 'DCSAutoMateMonitorWindow.dlg'), r'Scripts\DCSAutoMate\DCSAutoMateMonitorWindow.dlg'),
			]
			# Settings files are only copied when missing.
			onlyIfMissing = [
				(os.path.join(dcsAutoMateDir, 'DCSAutoMateHookSettings.lua'), r'Scripts\DCSAutoMate\DCSAutoMateHookSettings.lua'),
				(os.path.join(dcsAutoMateDir, 'DCSAutoMateExportSettings.lua'), r'Scripts\DCSAutoMate\DCSAutoMateExportSettings.lua'),
			]
			prefix = f'[{folderName}] ' if len(targetPaths) > 1 else ''
			for fullPath, displayName in alwaysCopied:
				if os.path.exists(fullPath):
					overwriteLines.append(f'  - {prefix}{displayName}')
				else:
					newFileLines.append(f'  - {prefix}{displayName}')
			for fullPath, displayName in onlyIfMissing:
				if not os.path.exists(fullPath):
					newFileLines.append(f'  - {prefix}{displayName}')

			exportLuaPath = os.path.join(scriptsDir, 'Export.lua')
			needsUpdate = True
			if os.path.exists(exportLuaPath):
				with open(exportLuaPath, 'r', encoding='utf-8', errors='replace') as f:
					content = f.read()
				if dofileLine in content:
					needsUpdate = False
			if needsUpdate:
				exportLuaUpdates.append(folderName)

		messageParts = []
		if newFileLines:
			messageParts.append('The following files will be installed:\n\n' + '\n'.join(newFileLines))
		if overwriteLines:
			messageParts.append('The following existing files will be overwritten:\n\n' + '\n'.join(overwriteLines))
		if exportLuaUpdates:
			folders = ', '.join(exportLuaUpdates)
			messageParts.append(f'Scripts\\Export.lua will be created or updated ({folders}).')
		if not messageParts:
			messageParts.append('All files are already up to date.')

		message = '\n\n'.join(messageParts) + '\n\nProceed?'

		box = QtWidgets.QMessageBox(parentWindow)
		box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
		box.setWindowTitle('Confirm Install')
		box.setText(message)
		okButton = box.addButton('Install', QtWidgets.QMessageBox.ButtonRole.AcceptRole)
		cancelButton = box.addButton('Cancel', QtWidgets.QMessageBox.ButtonRole.RejectRole)
		box.setDefaultButton(cancelButton)
		box.exec()
		return box.clickedButton() == okButton

	@staticmethod
	def ensureExportLuaInclude(scriptsDir):
		exportLuaPath = os.path.join(scriptsDir, 'Export.lua')
		dofileLine = r'dofile(lfs.writedir()..[[Scripts\DCSAutoMate\DCSAutoMateExport.lua]])'
		legacyLines = [
			r'dofile(lfs.writedir()..[[Scripts\DCSAutoMateExport.lua]])',
			r'dofile(lfs.writedir()..[[Scripts/DCSAutoMateExport.lua]])',
		]

		if not os.path.exists(exportLuaPath):
			with open(exportLuaPath, 'w', encoding='utf-8') as f:
				f.write(dofileLine + '\n')
			return 'created'

		with open(exportLuaPath, 'r', encoding='utf-8', errors='replace') as f:
			content = f.read()

		if dofileLine in content:
			return 'alreadyOk'

		for legacyLine in legacyLines:
			if legacyLine in content:
				with open(exportLuaPath, 'w', encoding='utf-8') as f:
					f.write(content.replace(legacyLine, dofileLine))
				return 'updatedLegacy'

		if 'DCSAutoMateExport.lua' not in content:
			with open(exportLuaPath, 'a', encoding='utf-8') as f:
				f.write('\n' + dofileLine + '\n')
			return 'appended'

		return 'presentButUnknown'

	@staticmethod
	def installToTarget(dcsSavedGamesPath, sourcePaths, hotkey):
		scriptsDir = os.path.join(dcsSavedGamesPath, 'Scripts')
		hooksDir = os.path.join(scriptsDir, 'Hooks')
		dcsAutoMateScriptsDir = os.path.join(scriptsDir, 'DCSAutoMate')

		os.makedirs(hooksDir, exist_ok=True)
		os.makedirs(dcsAutoMateScriptsDir, exist_ok=True)

		shutil.copy2(sourcePaths['export'], os.path.join(dcsAutoMateScriptsDir, 'DCSAutoMateExport.lua'))
		shutil.copy2(sourcePaths['hook'], os.path.join(hooksDir, 'DCSAutoMateHook.lua'))
		shutil.copy2(sourcePaths['dlg'], os.path.join(dcsAutoMateScriptsDir, 'DCSAutoMateMonitorWindow.dlg'))
		# Don't overwrite settings files if they already exist.
		hookSettingsDest = os.path.join(dcsAutoMateScriptsDir, 'DCSAutoMateHookSettings.lua')
		if not os.path.exists(hookSettingsDest):
			shutil.copy2(sourcePaths['hookSettings'], hookSettingsDest)
		exportSettingsDest = os.path.join(dcsAutoMateScriptsDir, 'DCSAutoMateExportSettings.lua')
		if not os.path.exists(exportSettingsDest):
			shutil.copy2(sourcePaths['exportSettings'], exportSettingsDest)
		exportStatus = DcsScriptsInstaller.ensureExportLuaInclude(scriptsDir)
		return exportStatus

	@staticmethod
	def installFromUi(parentWindow, config, hotkey):
		appBaseDir = DcsScriptsInstaller.getAppBaseDir()
		sourcePaths = DcsScriptsInstaller.getSourcePaths(appBaseDir)

		missing = [k for k, p in sourcePaths.items() if not os.path.exists(p)]
		if missing:
			QtWidgets.QMessageBox.critical(parentWindow, 'Error', f"Missing required script files next to the program: {', '.join(missing)}")
			return False

		folders = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		targetPaths = DcsScriptsInstaller.promptForInstallTargets(parentWindow, folders)
		if not targetPaths:
			return False

		if not DcsScriptsInstaller.confirmOverwrite(parentWindow, targetPaths):
			return False

		results = []
		for targetPath in targetPaths:
			if not targetPath:
				continue
			try:
				exportStatus = DcsScriptsInstaller.installToTarget(targetPath, sourcePaths, hotkey)
				results.append(f"Installed to: {targetPath} (Export.lua: {exportStatus})")
			except Exception as e:
				QtWidgets.QMessageBox.critical(parentWindow, 'Error', f'Failed installing to {targetPath}: {e}')
				return False

		QtWidgets.QMessageBox.information(parentWindow, 'Install Complete', '\n'.join(results))
		return True

	@staticmethod
	def check_installed(config):
		found_folders = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		if not found_folders:
			return False

		for name, path in found_folders:
			dcs_automate_export = os.path.join(path, 'Scripts', 'DCSAutoMate', 'DCSAutoMateExport.lua')
			dcs_automate_hook = os.path.join(path, 'Scripts', 'Hooks', 'DCSAutoMateHook.lua')
			export_lua = os.path.join(path, 'Scripts', 'Export.lua')

			if not os.path.exists(dcs_automate_export):
				return False
			if not os.path.exists(dcs_automate_hook):
				return False
			if not os.path.exists(export_lua):
				return False

			try:
				with open(export_lua, 'r', encoding='utf-8', errors='ignore') as f:
					content = f.read()
					if 'dofile(lfs.writedir()..[[Scripts\\DCSAutoMate\\DCSAutoMateExport.lua]])' not in content:
						return False
			except Exception:
				return False

		return True
