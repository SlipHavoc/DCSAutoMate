import sys
import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from DCSBIOSExportManager import DCSBIOSExportManager
from DCSAutoMateExportManager import DCSAutoMateExportManager
import pyperclip
import importlib

class DCSMonitorApp:
	def __init__(self, root):
		self.refreshRate = 1000 # milliseconds

		self.root = root
		self.root.title('DCS Monitor')
		self.root.geometry('1600x900')
		root.protocol('WM_DELETE_WINDOW', lambda: (self.dcsBiosManager.stop(), self.dcsAutoMateManager.stop(), root.destroy()))

		self.jsonDirectory = os.path.join(
			os.environ['USERPROFILE'],
			'Saved Games',
			'DCS.openbeta',
			'Scripts',
			'DCS-BIOS',
			'doc',
			'json'
		)
		self.saveFile = 'DCSMonitorControls.json'

		self.dcsBiosManager = DCSBIOSExportManager({})
		self.dcsBiosManager.start()
		self.dcsAutoMateManager = DCSAutoMateExportManager({})
		self.dcsAutoMateManager.start()

		self.customControls = self.getCustomControls()
		self.modules = self.loadModules()
		self.monitoredControls = []
		self.loadMonitoredControls()
		self.createWidgets()
		self.updateControlList()

		self.updateDataMonitoring()
		self.selectModule()

	def createWidgets(self):
		controlsFrame = tk.Frame(self.root)
		controlsFrame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')

		moduleFrame = tk.Frame(controlsFrame)
		moduleFrame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
		tk.Label(moduleFrame, text='Modules:').grid(row=0, column=0, sticky='w')
		self.moduleVar = tk.StringVar()
		self.moduleDropdown = ttk.Combobox(moduleFrame, values=list(self.modules.keys()), textvariable=self.moduleVar)
		self.moduleDropdown.grid(row=0, column=1, sticky='ew')
		self.moduleDropdown.bind('<<ComboboxSelected>>', self.selectModule)

		categoryFrame = tk.Frame(controlsFrame)
		categoryFrame.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
		tk.Label(categoryFrame, text='Category:').grid(row=0, column=0, sticky='w')
		self.categoryVar = tk.StringVar()
		self.categoryDropdown = ttk.Combobox(categoryFrame, textvariable=self.categoryVar)
		self.categoryDropdown.grid(row=0, column=1, sticky='ew')
		self.categoryDropdown.bind('<<ComboboxSelected>>', self.updateControlList)

		controlFrame = tk.Frame(controlsFrame)
		controlFrame.grid(row=2, column=0, padx=10, pady=5, sticky='nsew')
		tk.Label(controlFrame, text='Controls:').grid(row=0, column=0, sticky='w')
		self.controlList = tk.Listbox(controlFrame, selectmode=tk.SINGLE)
		self.controlList.grid(row=1, column=0, sticky='nsew')
		addButton = tk.Button(controlFrame, text='Add to Monitor', command=self.addControl)
		addButton.grid(row=2, column=0, pady=5, sticky='e')

		self.refreshButton = tk.Button(controlFrame, text='Refresh Custom Controls', command=self.refreshCustomControls)
		self.refreshButton.grid(row=3, column=0, pady=5, sticky='e')
		self.refreshButton.grid_remove()  # Initially hide the button

		monitorFrame = tk.Frame(controlsFrame)
		monitorFrame.grid(row=4, column=0, padx=10, pady=5, sticky='nsew')
		tk.Label(monitorFrame, text='Monitored Controls:').grid(row=0, column=0, sticky='w')
		self.monitoredList = tk.Listbox(monitorFrame, selectmode=tk.SINGLE)
		self.monitoredList.grid(row=1, column=0, sticky='nsew')
		controlButtons = tk.Frame(monitorFrame)
		controlButtons.grid(row=2, column=0, pady=5, sticky='ew')
		topButton = tk.Button(controlButtons, text='Top', command=lambda: self.moveControlTo('top'))
		topButton.grid(row=0, column=0, padx=5)
		upButton = tk.Button(controlButtons, text='Up', command=lambda: self.moveControl(-1))
		upButton.grid(row=0, column=1, padx=5)
		downButton = tk.Button(controlButtons, text='Down', command=lambda: self.moveControl(1))
		downButton.grid(row=0, column=2, padx=5)
		bottomButton = tk.Button(controlButtons, text='Bottom', command=lambda: self.moveControlTo('bottom'))
		bottomButton.grid(row=0, column=3, padx=5)
		removeButton = tk.Button(controlButtons, text='Remove', command=self.removeControl)
		removeButton.grid(row=1, column=0, pady=5, columnspan=2)
		clearButton = tk.Button(controlButtons, text='Clear', command=self.clearControls)
		clearButton.grid(row=1, column=2, pady=5, columnspan=2)

		outputFrameBios = tk.Frame(self.root)
		outputFrameBios.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
		tk.Label(outputFrameBios, text='DCS BIOS Output:').grid(row=0, column=0, sticky='w')
		biosTextFrame = tk.Frame(outputFrameBios)
		biosTextFrame.grid(row=1, column=0, sticky='nsew')
		biosScrollY = tk.Scrollbar(biosTextFrame, orient=tk.VERTICAL)
		biosScrollX = tk.Scrollbar(biosTextFrame, orient=tk.HORIZONTAL)
		self.outputTextBios = tk.Text(biosTextFrame, state=tk.DISABLED, wrap=tk.NONE, yscrollcommand=biosScrollY.set, xscrollcommand=biosScrollX.set)
		biosScrollY.config(command=self.outputTextBios.yview)
		biosScrollX.config(command=self.outputTextBios.xview)
		biosScrollY.grid(row=0, column=1, sticky='ns')
		biosScrollX.grid(row=1, column=0, sticky='ew')
		self.outputTextBios.grid(row=0, column=0, sticky='nsew')
		copyButtonBios = tk.Button(outputFrameBios, text='Copy to Clipboard', command=self.copyToClipboardBios)
		copyButtonBios.grid(row=2, column=0, pady=5, sticky='e')

		outputFrameAutoMate = tk.Frame(self.root)
		outputFrameAutoMate.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
		tk.Label(outputFrameAutoMate, text='DCSAutoMateExport Output:').grid(row=0, column=0, sticky='w')
		autoMateTextFrame = tk.Frame(outputFrameAutoMate)
		autoMateTextFrame.grid(row=1, column=0, sticky='nsew')
		autoMateScrollY = tk.Scrollbar(autoMateTextFrame, orient=tk.VERTICAL)
		autoMateScrollX = tk.Scrollbar(autoMateTextFrame, orient=tk.HORIZONTAL)
		self.outputTextAutoMate = tk.Text(autoMateTextFrame, state=tk.DISABLED, wrap=tk.NONE, yscrollcommand=autoMateScrollY.set, xscrollcommand=autoMateScrollX.set, width=70)
		autoMateScrollY.config(command=self.outputTextAutoMate.yview)
		autoMateScrollX.config(command=self.outputTextAutoMate.xview)
		autoMateScrollY.grid(row=0, column=1, sticky='ns')
		autoMateScrollX.grid(row=1, column=0, sticky='ew')
		self.outputTextAutoMate.grid(row=0, column=0, sticky='nsew')
		copyButtonAutoMate = tk.Button(outputFrameAutoMate, text='Copy to Clipboard', command=self.copyToClipboardAutoMate)
		copyButtonAutoMate.grid(row=2, column=0, pady=5, sticky='e')

		for control in self.monitoredControls:
			self.monitoredList.insert(tk.END, control)

		self.moduleVar.set(list(self.modules.keys())[0])
		self.selectModule()

	def loadModules(self):
		modules = {}

		if os.path.exists('DCSMonitorCustomControls.py'):
			modules['CustomControls'] = {}
		for filename in os.listdir(self.jsonDirectory):
			if filename.endswith('.json') and filename != 'AircraftAliases.json':
				with open(os.path.join(self.jsonDirectory, filename), 'r') as file:
					modules[filename[:-5]] = json.load(file)

		# Sort the modules so that the special modules are at the top.
		specialModules = ['CustomControls', 'CommonData', 'MetadataStart', 'MetadataEnd']
		sortedModules = {key: modules[key] for key in specialModules if key in modules}
		sortedModules.update({k: modules[k] for k in sorted(modules.keys()) if k not in specialModules})
		return sortedModules

	def selectModule(self, *args):
		selectedModule = self.moduleVar.get()
		if selectedModule == 'CustomControls':
			self.customControls = self.getCustomControls()
			self.refreshButton.grid()  # Show the button
			self.categoryVar.set('All') # Category for custom controls is always 'All'.
			self.categoryDropdown['values'] = ['All']
			self.updateControlList()
		else:
			self.refreshButton.grid_remove()  # Hide the button
			self.categoryVar.set('All')
			moduleControls = self.modules[selectedModule]
			categories = set()
			for category in moduleControls:
				categories.add(category)
			self.categoryDropdown['values'] = ['All'] + sorted(categories)
			self.updateControlList()
			if categories:
				self.categoryVar.set('All')
				self.updateControlList()

	def getCustomControls(self):
		if os.path.exists('DCSMonitorCustomControls.py'):
			try:
				module = importlib.import_module('DCSMonitorCustomControls')
				importlib.reload(module)
				# Get the custom controls from the module.
				self.dcsMonitorCustomControls = module.DCSMonitorCustomControls()
				customControls = self.dcsMonitorCustomControls.getCustomControls() # Returns a dictionary of control names and function callbacks.
				return customControls
			except Exception as e:
				messagebox.showerror('Error', f'Error calling getCustomControls function in DCSMonitorCustomControls.py: {e}')

	def refreshCustomControls(self):
		if self.moduleVar.get() == 'CustomControls':
			self.customControls = self.getCustomControls()
			self.updateControlList()

			# If there are any controls in the monitored list that don't exist in the custom controls, remove them.
			for control in [ctrl for ctrl in self.monitoredControls if ctrl.split('/')[0] == 'CustomControls']:
				if control not in self.customControls:
					self.monitoredControls.remove(control)

	def updateControlList(self, *args):
		selectedModule = self.moduleVar.get()
		if not selectedModule:
			return

		self.controlList.delete(0, tk.END)
		if selectedModule == 'CustomControls':
			for control in sorted(self.customControls.keys()):
				self.controlList.insert(tk.END, control)
		else:
			moduleControls = self.modules[selectedModule]
			selectedCategory = self.categoryVar.get()

			controlsList = []
			for category, controls in moduleControls.items():
				for control in controls:
					if selectedCategory == 'All' or category == selectedCategory:
						controlsList.append(control)

			for control in sorted(controlsList):
				self.controlList.insert(tk.END, f'{selectedModule}/{control}')
		self.controlList.config(width=0)
		self.monitoredList.config(width=0)

	def addControl(self):
		selected = self.controlList.curselection()
		if not selected:
			return
		control = self.controlList.get(selected[0])
		if control not in self.monitoredControls:
			self.monitoredControls.append(control)
			self.monitoredList.insert(tk.END, control)
		self.monitoredList.config(width=0)
		self.saveMonitoredControls()

	def moveControl(self, direction):
		selected = self.monitoredList.curselection()
		if not selected:
			return
		index = selected[0]
		newIndex = index + direction
		if 0 <= newIndex < len(self.monitoredControls):
			self.monitoredControls[index], self.monitoredControls[newIndex] = (
				self.monitoredControls[newIndex],
				self.monitoredControls[index],
			)
			self.monitoredList.delete(0, tk.END)
			for control in self.monitoredControls:
				self.monitoredList.insert(tk.END, control)
			self.monitoredList.select_set(newIndex)
		self.saveMonitoredControls()

	def moveControlTo(self, position):
		selected = self.monitoredList.curselection()
		if not selected:
			return
		index = selected[0]
		control = self.monitoredControls.pop(index)
		if position == 'top':
			self.monitoredControls.insert(0, control)
		elif position == 'bottom':
			self.monitoredControls.append(control)
		self.monitoredList.delete(0, tk.END)
		for control in self.monitoredControls:
			self.monitoredList.insert(tk.END, control)
		self.monitoredList.select_set(0 if position == 'top' else tk.END)
		self.saveMonitoredControls()

	def removeControl(self):
		selected = self.monitoredList.curselection()
		if not selected:
			return
		index = selected[0]
		self.monitoredControls.pop(index)
		self.monitoredList.delete(index)
		self.saveMonitoredControls()

	def clearControls(self):
		self.monitoredControls.clear()
		self.monitoredList.delete(0, tk.END)
		self.saveMonitoredControls()

	def loadMonitoredControls(self):
		if os.path.exists(self.saveFile):
			with open(self.saveFile, 'r') as file:
				self.monitoredControls = json.load(file)
		# If there are any controls in the monitored list that don't exist in the custom controls, remove them.
		for control in [ctrl for ctrl in self.monitoredControls if ctrl.split('/')[0] == 'CustomControls']:
			if control not in self.customControls:
				self.monitoredControls.remove(control)

	def saveMonitoredControls(self):
		with open(self.saveFile, 'w') as file:
			json.dump(self.monitoredControls, file)

	def updateDataMonitoring(self):
		# Save the current scroll position.
		biosScrollYPos = self.outputTextBios.yview()
		biosScrollXPos = self.outputTextBios.xview()

		self.outputTextBios.config(state=tk.NORMAL)
		self.outputTextBios.delete(1.0, tk.END)

		# Get the control state data from custom controls and DCS-BIOS.
		for control in self.monitoredControls:
			if control in self.customControls:
				value = self.customControls[control](self.dcsAutoMateManager.dataStorage, dcsBiosManager=self.dcsBiosManager)
				self.outputTextBios.insert(tk.END, f'{value}\n')
			else:
				value = self.dcsBiosManager.getControlState([control])[0]
				self.outputTextBios.insert(tk.END, f'{value}\n')

		## First the custom controls.
		#for control in self.customControls:
		#	value = self.customControls[control](self.dcsAutoMateManager.dataStorage)
		#	self.outputTextBios.insert(tk.END, f'{value}\n')
		## Then the standard DCS BIOS controls.
		#biosResults = self.dcsBiosManager.getControlState(self.monitoredControls)
		#for result in biosResults:
		#	self.outputTextBios.insert(tk.END, f'{result}\n')
		self.outputTextBios.see(tk.END)
		self.outputTextBios.config(state=tk.DISABLED)
		# Restore the scroll position.
		self.outputTextBios.yview_moveto(biosScrollYPos[0])
		self.outputTextBios.xview_moveto(biosScrollXPos[0])

		# Save the current scroll position
		autoMateScrollYPos = self.outputTextAutoMate.yview()
		autoMateScrollXPos = self.outputTextAutoMate.xview()
		# Pretty-print the JSON data
		prettyPrintedData = json.dumps(self.dcsAutoMateManager.dataStorage, indent=4)
		self.outputTextAutoMate.config(state=tk.NORMAL)
		self.outputTextAutoMate.delete(1.0, tk.END)
		self.outputTextAutoMate.insert(tk.END, prettyPrintedData)
		self.outputTextAutoMate.config(state=tk.DISABLED)
		# Restore the scroll position
		self.outputTextAutoMate.yview_moveto(autoMateScrollYPos[0])
		self.outputTextAutoMate.xview_moveto(autoMateScrollXPos[0])

		self.root.after(self.refreshRate, self.updateDataMonitoring)

	def copyToClipboardAutoMate(self):
		# Get the contents of the outputTextBios text box
		outputText = self.outputTextAutoMate.get(1.0, tk.END).strip()
		# Copy the contents to the clipboard
		pyperclip.copy(outputText)
		messagebox.showinfo('Copied', 'DCSAutoMate output copied to clipboard')

	def copyToClipboardBios(self):
		# Get the contents of the outputTextBios text box
		outputText = self.outputTextBios.get(1.0, tk.END).strip()
		# Copy the contents to the clipboard
		pyperclip.copy(outputText)
		messagebox.showinfo('Copied', 'DCS BIOS output copied to clipboard')

if __name__ == '__main__':
	# When running this program as an exe, we need to have its own path appended to the sys.path in order for it to find script files in the DCSAutoMateScripts subfolder.
	applicationPath = os.path.dirname(sys.executable)
	sys.path.append(applicationPath)

	root = tk.Tk()
	app = DCSMonitorApp(root)
	root.mainloop()
