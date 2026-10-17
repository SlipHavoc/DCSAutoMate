"""DCSControlPanel — interactive control utility for DCSAutoMate.

Desktop GUI that lets the user observe and *drive* cockpit controls directly,
using the same `DCSDirectManager`/`DCSAutoMateExport.lua` pipeline as DCSAutoMate.
It replaces the retired DCSMonitor (now in `archive/DCSMonitor/`).

Each monitored control renders as a type-appropriate card:
  * discrete  -> one button per position (labels parsed from description)
  * continuous -> slider 0..1 mapped to argLim
  * relative  -> minus / plus buttons + step-size slider
  * wheel     -> minus / plus buttons sending signed click counts (radio_wheel_1)
  * read-only -> value label only (arg-only or indication controls)
"""

import os
import sys
import json
import threading
import time
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets

# Add the script directory to sys.path for frozen-exe support.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
	sys.path.insert(0, current_dir)

from network.DCSDirectManager import DCSDirectManager, TELEMETRY_CATALOGUE, TELEMETRY_MODULE, telemetryControl
from engine.simCommands import loadSimCommands, parseSimCommandEntry
from utils.SettingsManager import SettingsManager
from utils.version import APP_VERSION


# Poll intervals in milliseconds — interactive controls need fast feedback,
# read-only controls can tolerate a slower rate to reduce TCP churn.
POLL_INTERACTIVE_MS = 100
POLL_READONLY_MS = 500

# When True, the poll worker logs per-tick refs count, elapsed ms, and a
# running summary of DCSDirectManager.getQueryStats() to stdout.  Leave this
# off in normal use; flip on when diagnosing slow-update issues.
DEBUG_POLL = False

SAVE_FILE = os.path.join('config', 'DCSControlPanelSettings.json')


###############################################################################
# Helpers
###############################################################################

def parsePositionLabels(description, positions):
	"""Return generic per-position labels: ['Pos 0', 'Pos 1', ...].

	Earlier versions tried to parse labels from the description string (e.g.
	"Landing Gear Handle, UP/DOWN/EMERG DOWN"), but that convention isn't
	universal — controls like AH-64D `SAI.CageKnobPull` produce nonsensical
	splits.  Since the full description is already shown above the buttons,
	generic labels are clearer in every case.

	`description` is accepted (and ignored) so callers don't have to change.
	"""
	positions = max(1, int(positions or 1))
	return [f'Pos {i}' for i in range(positions)]


def moduleNamesForDropdown(controlMappings):
	"""Module names for the dropdown: the telemetry pseudo-module first, then mapped modules alphabetically."""
	return [TELEMETRY_MODULE] + sorted(controlMappings.keys())


def controlsForModule(controlMappings, moduleName):
	"""{canonical: control} for a module; the telemetry module lists the common LoGet* fields."""
	if moduleName == TELEMETRY_MODULE:
		return {name: telemetryControl(name) for name in TELEMETRY_CATALOGUE}
	return controlMappings.get(moduleName, {}).get('controls', {})


def formatControlLabel(dcsDirectManager, moduleRef):
	"""Return the canonical name portion of a 'module/canonical' ref.

	The module name is stripped because the user has already chosen it via the
	module dropdown.
	"""
	if '/' not in moduleRef:
		return moduleRef
	_, canonical = moduleRef.split('/', 1)
	return canonical


def _isNumber(value):
	return isinstance(value, (int, float)) and not isinstance(value, bool)


def changedRefs(before, after):
	"""Snapshot keys whose value changed, sorted.  Numbers must differ by more than float noise, and a number missing on one side counts as 0; text (e.g. loadout CLSIDs) must just differ."""
	changed = []
	for key in set(before) | set(after):
		valueBefore = before.get(key)
		valueAfter = after.get(key)
		if all(value is None or _isNumber(value) for value in (valueBefore, valueAfter)):
			if abs(float(valueBefore or 0.0) - float(valueAfter or 0.0)) > 1e-4:
				changed.append(key)
		elif valueBefore != valueAfter:
			changed.append(key)
	return sorted(changed, key=str)


def _isTelemetryRef(ref):
	return isinstance(ref, str) and ref.startswith(f'{TELEMETRY_MODULE}/')


def _rounded(value):
	return round(value, 4) if isinstance(value, float) else value


def formatSnapshotValue(value):
	"""Table text for a snapshot value: numbers to 4 places, text as-is, an empty string as "" so it doesn't look missing."""
	if value is None:
		return ''
	if _isNumber(value):
		return f'{float(value):.4f}'
	if value == '':
		return '""'
	return str(value)


def snapshotReport(before, after, controlIndex, reverseTranslate, module, rawScan, beforeTakenAt, afterTakenAt, includeSnapshots=False):
	"""JSON-ready comparison of two snapshots: each changed control's raw arg values and, for mapped controls, the values a script would send or read."""
	changes = []
	for ref in changedRefs(before, after):
		rawBefore = _rounded(before.get(ref))
		rawAfter = _rounded(after.get(ref))
		if _isTelemetryRef(ref):
			changes.append({'control': ref, 'description': telemetryControl(ref.partition('/')[2])['description'], 'arg': None, 'before': rawBefore, 'after': rawAfter, 'scriptBefore': rawBefore, 'scriptAfter': rawAfter})
			continue
		if rawScan:
			changes.append({'arg': ref, 'before': rawBefore, 'after': rawAfter})
			continue
		control = controlIndex.get(ref, {})
		argNum = control['displayArgs'][0] if control.get('wheel') and control.get('displayArgs') else control.get('arg')
		changes.append({
			'control': ref.partition('/')[2],
			'description': control.get('description', ''),
			'arg': argNum,
			'before': rawBefore,
			'after': rawAfter,
			'scriptBefore': _rounded(reverseTranslate(control, before[ref])) if ref in before else None,
			'scriptAfter': _rounded(reverseTranslate(control, after[ref])) if ref in after else None,
		})
	report = {'module': module, 'mode': 'raw' if rawScan else 'mapped', 'beforeTakenAt': beforeTakenAt, 'afterTakenAt': afterTakenAt, 'changes': changes}
	if includeSnapshots:
		def key(ref):
			if rawScan or _isTelemetryRef(ref):
				return str(ref)
			return ref.partition('/')[2]
		report['beforeSnapshot'] = {key(ref): _rounded(value) for ref, value in sorted(before.items(), key=lambda item: str(item[0]))}
		report['afterSnapshot'] = {key(ref): _rounded(value) for ref, value in sorted(after.items(), key=lambda item: str(item[0]))}
	return report


###############################################################################
# Card widgets
###############################################################################

class ControlCard(QtWidgets.QFrame):
	"""Base class for all per-control cards.

	Emits `removeRequested(ref)` when the card-level remove button is clicked.
	Subclasses implement `buildWidget()` and `updateValue(value)`.
	"""

	removeRequested = QtCore.Signal(str)
	moveRequested = QtCore.Signal(str, str)  # (ref, direction): 'top' | 'up' | 'down' | 'bottom'

	# Tracks the one card that currently has an active cockpit highlight.
	_activeHighlightCard = None

	# Poll interval class attribute — subclasses override for read-only cards.
	pollIntervalMs = POLL_INTERACTIVE_MS

	def __init__(self, ref, control, dcsDirectManager, parent=None):
		super().__init__(parent)
		self.ref = ref
		self.control = control
		self.dcsDirectManager = dcsDirectManager
		self.moduleName, self.canonical = ref.split('/', 1)
		self.currentValue = None
		self._sendHistory = []  # List of (hh:mm:ss, value) tuples, newest first, max 3.
		self._findButton = None
		self._findAutoTimer = None
		# When this card is deleted (e.g. via deleteLater after removal), clear any
		# active cockpit highlight so the class-level reference doesn't dangle.
		self.destroyed.connect(self._onCardDestroyed)

		self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
		self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)

		self._buildLayout()

	def _buildLayout(self):
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(8, 6, 8, 6)
		layout.setSpacing(3)

		# Header line: module/canonical name + copy button + remove button.
		headerRow = QtWidgets.QHBoxLayout()
		headerLabel = QtWidgets.QLabel(f'{self.moduleName} / {self.canonical}')
		headerFont = headerLabel.font()
		headerFont.setBold(True)
		headerLabel.setFont(headerFont)
		headerLabel.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
		headerRow.addWidget(headerLabel, 1)

		# Type tag (e.g. "discrete", "wheel", "continuous", "relative", "read-only").
		typeTag = self._typeTag()
		if typeTag:
			typeLabel = QtWidgets.QLabel(typeTag)
			typeLabel.setStyleSheet('color: #555; background: #eee; border: 1px solid #ccc; border-radius: 3px; padding: 0 4px;')
			typeFont = typeLabel.font()
			typeFont.setPointSizeF(typeFont.pointSizeF() * 0.85)
			typeLabel.setFont(typeFont)
			headerRow.addWidget(typeLabel, 0)

		for direction, symbol, tip in [
			('top', '\u23eb', 'Move to top'),
			('up', '\u2191', 'Move up'),
			('down', '\u2193', 'Move down'),
			('bottom', '\u23ec', 'Move to bottom'),
		]:
			moveBtn = QtWidgets.QPushButton(symbol)
			moveBtn.setFixedWidth(24)
			moveBtn.setToolTip(tip)
			moveBtn.clicked.connect(lambda checked=False, d=direction: self.moveRequested.emit(self.ref, d))
			headerRow.addWidget(moveBtn, 0)

		copyBtn = QtWidgets.QPushButton('\u2398') # Copy/paper icon.
		copyBtn.setText('Copy')
		copyBtn.setFixedWidth(48)
		copyBtn.setToolTip('Copy control name to clipboard')
		copyBtn.clicked.connect(self._onCopyName)
		headerRow.addWidget(copyBtn, 0)

		self._findButton = QtWidgets.QPushButton('Find')
		self._findButton.setCheckable(True)
		self._findButton.setFixedWidth(40)
		self._findButton.setToolTip('Highlight this control in the cockpit (auto-clears after 10s)')
		self._findButton.clicked.connect(self._onFindClicked)
		if not self.dcsDirectManager.getElementName(self.ref):
			self._findButton.hide()
		headerRow.addWidget(self._findButton, 0)

		removeBtn = QtWidgets.QPushButton('\u2715') # Multiplication sign X.
		removeBtn.setFixedWidth(24)
		removeBtn.setToolTip('Remove from monitored controls')
		removeBtn.clicked.connect(lambda: self.removeRequested.emit(self.ref))
		headerRow.addWidget(removeBtn, 0)
		layout.addLayout(headerRow)

		# Middle section: info column (description + current value) on the left,
		# send history on the right.  Sharing a row keeps the card vertically compact.
		midRow = QtWidgets.QHBoxLayout()
		midRow.setSpacing(8)

		leftCol = QtWidgets.QVBoxLayout()
		leftCol.setSpacing(2)

		# Description (may wrap).
		desc = self.control.get('description', '')
		if desc:
			descLabel = QtWidgets.QLabel(desc)
			descLabel.setWordWrap(True)
			descLabel.setStyleSheet('color: #555;')
			leftCol.addWidget(descLabel)

		# Crew access restriction (e.g. [0] = pilot only, [1] = copilot only).
		crewAccess = self.control.get('crewAccess')
		if crewAccess is not None:
			crewLabel = QtWidgets.QLabel('Crew: ' + ', '.join(str(c) for c in crewAccess))
			crewLabel.setStyleSheet('color: #888;')
			leftCol.addWidget(crewLabel)

		# Current value display (subclasses may hide or repurpose).
		self.valueLabel = QtWidgets.QLabel('Current: —')
		self.valueLabel.setStyleSheet('color: #006;')
		leftCol.addWidget(self.valueLabel)

		# Raw native arg value (before reverse translation) — shown whenever
		# the poll worker returns it, hidden until first value arrives.
		self.rawLabel = QtWidgets.QLabel()
		self.rawLabel.setStyleSheet('color: #888; font-family: monospace;')
		smallFont = self.rawLabel.font()
		smallFont.setPointSizeF(smallFont.pointSizeF() * 0.85)
		self.rawLabel.setFont(smallFont)
		self.rawLabel.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
		self.rawLabel.hide()
		leftCol.addWidget(self.rawLabel)

		midRow.addLayout(leftCol, 1)

		# Send history (right column) — hidden until the first command is sent.
		self._historyLabel = QtWidgets.QLabel()
		histFont = self._historyLabel.font()
		histFont.setFamily('monospace')
		histFont.setPointSizeF(histFont.pointSizeF() * 0.82)
		self._historyLabel.setFont(histFont)
		self._historyLabel.setStyleSheet('color: #888;')
		self._historyLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop)
		self._historyLabel.hide()
		midRow.addWidget(self._historyLabel, 0)

		layout.addLayout(midRow)

		# Widget slot — filled by subclass.
		self.widgetArea = QtWidgets.QWidget()
		self.widgetAreaLayout = QtWidgets.QVBoxLayout(self.widgetArea)
		self.widgetAreaLayout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(self.widgetArea)
		self.buildWidget(self.widgetAreaLayout)

	def buildWidget(self, layout):
		"""Override to populate the widget area with type-specific controls."""
		pass

	def updateValue(self, value):
		"""Called by the polling loop when a fresh value is available."""
		self.currentValue = value
		self.valueLabel.setText(f'Current: {self._formatValueForDisplay(value)}')

	def updateRawValue(self, rawNative):
		"""Called by the polling loop with the pre-translation native arg value."""
		if rawNative is None:
			return
		self.rawLabel.setText(f'raw: {rawNative:.4f}')
		self.rawLabel.show()

	def _formatValueForDisplay(self, value):
		if value is None:
			return '—'
		if isinstance(value, float):
			return f'{value:.3f}'
		return str(value)

	def _send(self, value):
		"""Send a control command, handling any exceptions quietly."""
		try:
			self.dcsDirectManager.sendControl(self.ref, value)
		except Exception as exc:
			# Don't crash the UI on send failures.
			print(f'[DCSControlPanel] sendControl({self.ref}, {value}) failed: {exc}')
			return
		# Record the sent value in the history display (newest first, max 3).
		ts = datetime.now().strftime('%H:%M:%S')
		self._sendHistory.insert(0, (ts, value))
		self._sendHistory = self._sendHistory[:3]
		self._updateHistoryLabel()

	def _updateHistoryLabel(self):
		"""Rebuild the history label text from self._sendHistory."""
		if not self._sendHistory:
			self._historyLabel.hide()
			return
		lines = [f'▶ {self._formatValueForDisplay(v)}  {ts}' for ts, v in self._sendHistory]
		self._historyLabel.setText('\n'.join(lines))
		self._historyLabel.show()

	def _typeTag(self):
		"""Short label describing the control's input shape, shown in the header."""
		if 'indicationId' in self.control:
			return 'indication'
		controlType = self.control.get('type', '')
		if controlType == 'relative' and self.control.get('wheel'):
			return 'wheel'
		if controlType == 'discrete' and ('indicatorArgLim' in self.control or 'indicatorPositions' in self.control):
			return 'discrete · indicator'
		if controlType:
			return controlType
		if 'arg' in self.control:
			return 'read-only'
		return ''

	def _onCopyName(self):
		clipboard = QtWidgets.QApplication.clipboard()
		if clipboard is not None:
			clipboard.setText(self.canonical)

	def _onFindClicked(self):
		if ControlCard._activeHighlightCard is self:
			# Toggle off — user clicked Find again on the same card.
			self._clearHighlight()
		else:
			# Clear any previous highlight first.
			if ControlCard._activeHighlightCard is not None:
				try:
					ControlCard._activeHighlightCard._clearHighlight()
				except RuntimeError:
					# Card was already deleted (removed from monitor while highlighted).
					ControlCard._activeHighlightCard = None
					self.dcsDirectManager.clearHighlight()
			# Activate this card's highlight.
			ControlCard._activeHighlightCard = self
			self._findButton.setChecked(True)
			self.dcsDirectManager.highlightControl(self.ref)
			# Auto-clear after 10 seconds.
			self._findAutoTimer = QtCore.QTimer(self)
			self._findAutoTimer.setSingleShot(True)
			self._findAutoTimer.timeout.connect(self._clearHighlight)
			self._findAutoTimer.start(10000)

	def _clearHighlight(self):
		if self._findAutoTimer is not None:
			try:
				self._findAutoTimer.stop()
			except RuntimeError:
				pass
			self._findAutoTimer = None
		self.dcsDirectManager.clearHighlight()
		if self._findButton is not None:
			try:
				self._findButton.setChecked(False)
			except RuntimeError:
				pass
		if ControlCard._activeHighlightCard is self:
			ControlCard._activeHighlightCard = None

	def _onCardDestroyed(self):
		if ControlCard._activeHighlightCard is self:
			ControlCard._activeHighlightCard = None
			try:
				self.dcsDirectManager.clearHighlight()
			except Exception:
				pass


class DiscreteCard(ControlCard):
	"""Discrete (position-based) control — one button per position."""

	def buildWidget(self, layout):
		self.buttons = []
		self.positionMap = self.control.get('positionMap')
		positions = int(self.control.get('positions', 2) or 2)
		labels = parsePositionLabels(self.control.get('description', ''), positions)

		# Indicator-range controls: the readback arg uses a different scale from
		# the command value, so position cannot be inferred from the polled value.
		# Pure encoders (arg=-1) have no readable cockpit position at all.
		# Buttons are send-only; highlighting and Current display are suppressed.
		self._isIndicatorRange = 'indicatorArgLim' in self.control or 'indicatorPositions' in self.control or self.control.get('arg') == -1
		if self._isIndicatorRange:
			self.valueLabel.setText('raw: —')

		# If positionMap has null entries (spring-loaded center), we STILL
		# show the button so the user can see all positions; the underlying
		# sendControl will handle the null-release semantics.  For non-null
		# entries we treat as normal send-and-hold.
		buttonRow = QtWidgets.QHBoxLayout()
		buttonRow.setSpacing(4)
		self.buttonGroup = QtWidgets.QButtonGroup(self)
		self.buttonGroup.setExclusive(False) # We manage highlight manually.

		for i in range(positions):
			label = labels[i] if i < len(labels) else f'Pos {i}'
			btn = QtWidgets.QPushButton(label)
			# Only make buttons checkable for controls where we can track state.
			if not self._isIndicatorRange:
				btn.setCheckable(True)
				btn.setStyleSheet('QPushButton:checked { color: white; }')
			btn.clicked.connect(lambda checked=False, idx=i: self._onPositionClicked(idx))
			self.buttons.append(btn)
			self.buttonGroup.addButton(btn, i)
			buttonRow.addWidget(btn)

		# pdp_special (PDP circuit breakers): detect by presence of 'sendValue'
		# in any positionMap entry.  These controls support a "collar" toggle
		# (send 0.9, hold ~4.5s, release 0.0) via an extra button.
		self._collarEntry = None
		if self.positionMap:
			for entry in self.positionMap:
				if entry is not None and 'sendValue' in entry and entry['sendValue'] == 0.9:
					self._collarEntry = entry
					break
		if self._collarEntry is not None:
			self._collarBtn = QtWidgets.QPushButton('Collar')
			self._collarBtn.clicked.connect(self._onCollarClicked)
			buttonRow.addWidget(self._collarBtn)

		layout.addLayout(buttonRow)

	def _onPositionClicked(self, index):
		self._send(index)
		# No optimistic highlight — wait for the poll to confirm the actual
		# position.  At 100ms poll interval the confirmation is nearly instant
		# for connected controls, and for controls where the poll returns nothing
		# (e.g. system unpowered) we correctly show no highlight at all.

	def _onCollarClicked(self):
		# Collar/un-collar sequence: send 0.9, wait 4500ms, release 0.0.
		# This is a blind toggle — the same sequence both engages and disengages
		# the collar, matching the physical CB collar behavior.
		entry = self._collarEntry
		self.dcsDirectManager.sendCommand(entry['deviceId'], entry['commandId'], 0.9)
		self._collarBtn.setEnabled(False)
		self._collarBtn.setText('Collaring…')
		QtCore.QTimer.singleShot(5000, self._onCollarRelease)

	def _onCollarRelease(self):
		entry = self._collarEntry
		self.dcsDirectManager.sendCommand(entry['deviceId'], entry['commandId'], 0.0)
		self._collarBtn.setEnabled(True)
		self._collarBtn.setText('Collar')

	def updateValue(self, value):
		if self._isIndicatorRange:
			# Don't update valueLabel or highlight — raw value display is handled
			# by updateRawValue; translated position index is meaningless here.
			self.currentValue = value
			return
		super().updateValue(value)
		# Discrete values come back as integer position indices.
		try:
			self._applyHighlight(int(value))
		except (TypeError, ValueError):
			pass

	def updateRawValue(self, rawNative):
		if self._isIndicatorRange:
			# For indicator-range controls show raw arg value as the primary
			# Current display — the translated position index is unreliable.
			if rawNative is not None:
				self.valueLabel.setText(f'raw: {rawNative:.4f}')
			# Suppress the separate rawLabel — valueLabel already carries it.
		else:
			super().updateRawValue(rawNative)

	def _applyHighlight(self, activeIndex):
		for i, btn in enumerate(self.buttons):
			btn.setChecked(i == activeIndex)


class ContinuousCard(ControlCard):
	"""Continuous control — slider 0..1 proportional over argLim."""

	def buildWidget(self, layout):
		self._userDragging = False
		self._lastSentValue = None
		# Minimum time between sends during drag — prevents flooding the TCP
		# socket when the slider fires many valueChanged events per second.
		self._minSendIntervalMs = 30
		self._lastSendTimestamp = 0
		self._pendingValue = None
		self._dragFlushTimer = QtCore.QTimer(self)
		self._dragFlushTimer.setSingleShot(True)
		self._dragFlushTimer.timeout.connect(self._flushPendingSend)

		argLim = self.control.get('argLim', [0.0, 1.0])
		self.argLim = argLim
		# `_AXIS` siblings have asymmetric ranges: argLim is the joystick-axis
		# input convention [-1, 1], but the slider min/max labels (and the
		# value-edit field) should reflect the cockpit arg's actual range so
		# the user sees meaningful endpoints.  Fall back to argLim when no
		# readback range is recorded.
		labelLim = self.control.get('readbackArgLim') or argLim

		row = QtWidgets.QHBoxLayout()
		self.minLabel = QtWidgets.QLabel(f'{labelLim[0]:g}')
		row.addWidget(self.minLabel)

		self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
		self.slider.setRange(0, 1000)
		self.slider.setValue(0)
		self.slider.sliderPressed.connect(self._onSliderPressed)
		self.slider.sliderReleased.connect(self._onSliderReleased)
		self.slider.valueChanged.connect(self._onSliderMoved)
		row.addWidget(self.slider, 1)

		self.maxLabel = QtWidgets.QLabel(f'{labelLim[1]:g}')
		row.addWidget(self.maxLabel)

		self.valueEdit = QtWidgets.QLineEdit()
		self.valueEdit.setFixedWidth(70)
		self.valueEdit.setPlaceholderText('0.00')
		self.valueEdit.editingFinished.connect(self._onValueEditChanged)
		row.addWidget(self.valueEdit)

		layout.addLayout(row)

	def _onSliderPressed(self):
		self._userDragging = True

	def _onSliderReleased(self):
		self._userDragging = False
		proportional = self.slider.value() / 1000.0
		# Always send final value on release so the control lands exactly
		# where the user let go, even if the throttle timer had pending sends.
		self._dragFlushTimer.stop()
		self._pendingValue = None
		self._sendThrottled(proportional, force=True)
		self.valueEdit.setText(f'{proportional:.3f}')

	def _onSliderMoved(self, value):
		proportional = value / 1000.0
		self.valueEdit.setText(f'{proportional:.3f}')
		if self._userDragging:
			# Realtime send during drag, throttled to avoid flooding TCP.
			self._sendThrottled(proportional)

	def _sendThrottled(self, proportional, force=False):
		now = QtCore.QDateTime.currentMSecsSinceEpoch()
		elapsed = now - self._lastSendTimestamp
		if force or elapsed >= self._minSendIntervalMs:
			self._lastSendTimestamp = now
			self._lastSentValue = proportional
			self._pendingValue = None
			self._send(proportional)
		else:
			# Defer — the single-shot timer will flush the latest value.
			self._pendingValue = proportional
			if not self._dragFlushTimer.isActive():
				self._dragFlushTimer.start(self._minSendIntervalMs - int(elapsed))

	def _flushPendingSend(self):
		if self._pendingValue is None:
			return
		value = self._pendingValue
		self._pendingValue = None
		self._lastSendTimestamp = QtCore.QDateTime.currentMSecsSinceEpoch()
		self._lastSentValue = value
		self._send(value)

	def _onValueEditChanged(self):
		text = self.valueEdit.text().strip()
		try:
			proportional = float(text)
		except ValueError:
			return
		proportional = max(0.0, min(1.0, proportional))
		self.slider.blockSignals(True)
		self.slider.setValue(round(proportional * 1000))
		self.slider.blockSignals(False)
		self._send(proportional)

	def updateValue(self, value):
		super().updateValue(value)
		# `value` from getControlState is already 0..1 proportional for
		# continuous controls — see DCSDirectManager._reverseTranslateValue.
		if self._userDragging:
			return
		try:
			proportional = float(value)
		except (TypeError, ValueError):
			return
		proportional = max(0.0, min(1.0, proportional))
		self.slider.blockSignals(True)
		self.slider.setValue(round(proportional * 1000))
		self.slider.blockSignals(False)
		if not self.valueEdit.hasFocus():
			self.valueEdit.setText(f'{proportional:.3f}')


class RelativeCard(ControlCard):
	"""Relative control — minus/plus buttons with a tunable step.

	For controls with a fixed incrementValue/decrementValue (e.g. multiswitch_stop),
	the step slider is hidden; buttons send +1/-1 which the translation layer
	normalises to the fixed increment/decrement values.
	"""

	def buildWidget(self, layout):
		row = QtWidgets.QHBoxLayout()
		row.setSpacing(4)

		minusBtn = QtWidgets.QPushButton('\u2212') # Minus sign.
		minusBtn.setFixedWidth(40)
		minusBtn.clicked.connect(lambda: self._sendDelta(-1))
		row.addWidget(minusBtn)

		plusBtn = QtWidgets.QPushButton('+')
		plusBtn.setFixedWidth(40)
		plusBtn.clicked.connect(lambda: self._sendDelta(+1))
		row.addWidget(plusBtn)

		row.addSpacing(12)

		isFixed = 'incrementValue' in self.control
		if isFixed:
			# Fixed step: show what the control will actually send.
			incVal = self.control.get('incrementValue', '')
			decVal = self.control.get('decrementValue', '')
			row.addWidget(QtWidgets.QLabel(f'fixed \u2212{abs(decVal):.3g} / +{incVal:.3g}'))
			self.stepSlider = None
			self.stepLabel = None
		else:
			row.addWidget(QtWidgets.QLabel('step:'))

			# Step slider 1..100 mapped to 0.01..1.0.  Default derived from the
			# control's own `step` field, or its sibling's if it has a siblingOf.
			defaultStep = self._defaultStep()
			sliderValue = max(1, min(100, round(defaultStep * 100)))
			self.stepSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
			self.stepSlider.setRange(1, 100)
			self.stepSlider.setValue(sliderValue)
			self.stepSlider.valueChanged.connect(self._onStepChanged)
			row.addWidget(self.stepSlider, 1)

			self.stepLabel = QtWidgets.QLabel(f'{sliderValue / 100.0:.2f}')
			self.stepLabel.setFixedWidth(50)
			row.addWidget(self.stepLabel)

		layout.addLayout(row)

	def _defaultStep(self):
		"""Derive a reasonable default step.

		Order of preference:
		 1. The control's own `step` field.
		 2. 0.05 as a generic fallback.
		"""
		ownStep = self.control.get('step')
		if isinstance(ownStep, (int, float)) and 0 < ownStep <= 1:
			return float(ownStep)

		return 0.05

	def _onStepChanged(self, value):
		self.stepLabel.setText(f'{value / 100.0:.2f}')

	def _sendDelta(self, sign):
		if self.stepSlider is None:
			# Fixed step control: send +1/-1 for normalisation in _translateValue.
			self._send(float(sign))
		else:
			step = self.stepSlider.value() / 100.0
			self._send(sign * step)


class WheelCard(ControlCard):
	"""Wheel control (radio_wheel_1) — minus/plus buttons send signed click counts.

	The underlying cockpit control is a 2-button rotary: each click moves
	 one notch CW or CCW with no provision to seek.  The dispatcher
	 interprets the value as a signed integer click count, so we send ±1.
	"""

	def buildWidget(self, layout):
		row = QtWidgets.QHBoxLayout()
		row.setSpacing(4)

		minusBtn = QtWidgets.QPushButton('\u2212') # Minus sign.
		minusBtn.setFixedWidth(40)
		minusBtn.clicked.connect(lambda: self._send(-1))
		row.addWidget(minusBtn)

		plusBtn = QtWidgets.QPushButton('+')
		plusBtn.setFixedWidth(40)
		plusBtn.clicked.connect(lambda: self._send(+1))
		row.addWidget(plusBtn)

		row.addStretch(1)
		layout.addLayout(row)

		# Debug row showing live arg values: pulse arg + every displayArg.
		# For Mi-8/Mi-24 wheels the pulse arg differs from the displayed
		# master arg and may be coupled to additional slave args via a
		# digit-carry chain — show them all so the user can see which arg
		# corresponds to what they're seeing in the cockpit.
		self._argValues = {}
		pulseArg = self.control.get('arg')
		self._argOrder = [] if pulseArg == -1 else [pulseArg]
		for da in self.control.get('displayArgs') or []:
			if da not in self._argOrder:
				self._argOrder.append(da)
		self.argsLabel = QtWidgets.QLabel(self._formatArgsLine())
		self.argsLabel.setStyleSheet('color: #555; font-family: monospace;')
		self.argsLabel.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
		layout.addWidget(self.argsLabel)

	def _formatArgsLine(self):
		parts = []
		for arg in self._argOrder:
			value = self._argValues.get(arg)
			if value is None:
				parts.append(f'arg.{arg}=—')
			else:
				parts.append(f'arg.{arg}={value:.3f}' if isinstance(value, float) else f'arg.{arg}={value}')
		return ' \u00B7 '.join(parts) # Middle-dot separator.

	def updateValue(self, value):
		super().updateValue(value)
		# The base poll returns displayArgs[0] (master display arg) for wheels
		# — see DCSDirectManager.getControlState.  Track it in the args row.
		displayArgs = self.control.get('displayArgs') or []
		if displayArgs:
			self._argValues[displayArgs[0]] = value
			self.argsLabel.setText(self._formatArgsLine())

	def updateExtraArg(self, arg, value):
		"""Side-channel update from the poll worker for non-master args
		(pulse arg and any slave args in the digit-carry chain).
		"""
		self._argValues[arg] = value
		self.argsLabel.setText(self._formatArgsLine())


class ToggleCard(ControlCard):
	"""Toggle control — a single button that fires the flip command once per click."""

	def buildWidget(self, layout):
		row = QtWidgets.QHBoxLayout()
		row.setSpacing(4)

		self._toggleBtn = QtWidgets.QPushButton('Toggle')
		self._toggleBtn.setFixedWidth(80)
		self._toggleBtn.setCheckable(True)
		self._toggleBtn.setStyleSheet('QPushButton:checked { color: white; }')
		self._toggleBtn.clicked.connect(lambda: self._send(1))
		row.addWidget(self._toggleBtn)

		row.addStretch(1)
		layout.addLayout(row)

	def updateValue(self, value):
		super().updateValue(value)
		try:
			self._toggleBtn.setChecked(int(value) == 1)
		except (TypeError, ValueError):
			pass


class ReadOnlyCard(ControlCard):
	"""Read-only control — value label only, no input widgets."""

	pollIntervalMs = POLL_READONLY_MS

	def buildWidget(self, layout):
		note = QtWidgets.QLabel('(read-only)')
		note.setStyleSheet('color: #888; font-style: italic;')
		layout.addWidget(note)


class RawCard(ControlCard):
	"""Raw control — quick-fire -1 / 0 / 1 buttons plus a custom value entry.

	No translation is applied; the value is sent to DCS as-is.  The correct
	value depends entirely on what the DCS module expects.  Use the module's
	Input/<variant>/keyboard/default.lua and joystick/default.lua files as
	a reference — the 'value' fields in those files are native DCS values.
	"""

	# Raw controls have no arg to read back, so there is nothing to poll.
	pollIntervalMs = POLL_READONLY_MS

	def buildWidget(self, layout):
		row = QtWidgets.QHBoxLayout()
		row.setSpacing(4)

		for label, value in [('-1', -1), ('0', 0), ('1', 1)]:
			btn = QtWidgets.QPushButton(label)
			btn.setFixedWidth(40)
			btn.clicked.connect(lambda checked=False, v=value: self._send(v))
			row.addWidget(btn)

		row.addSpacing(8)

		self._customEdit = QtWidgets.QLineEdit()
		self._customEdit.setPlaceholderText('custom value')
		self._customEdit.setFixedWidth(90)
		self._customEdit.returnPressed.connect(self._onCustomSend)
		row.addWidget(self._customEdit)

		sendBtn = QtWidgets.QPushButton('Send')
		sendBtn.setFixedWidth(50)
		sendBtn.clicked.connect(self._onCustomSend)
		row.addWidget(sendBtn)

		row.addStretch(1)
		layout.addLayout(row)

		note = QtWidgets.QLabel('Raw — no translation. Values: try 1 for AI crew commands; check keyboard/joystick default.lua for others.')
		note.setStyleSheet('color: #888; font-style: italic;')
		note.setWordWrap(True)
		layout.addWidget(note)

	def _onCustomSend(self):
		text = self._customEdit.text().strip()
		if not text:
			return
		try:
			value = int(text) if '.' not in text else float(text)
		except ValueError:
			self._customEdit.setStyleSheet('border: 1px solid red;')
			return
		self._customEdit.setStyleSheet('')
		self._send(value)

	def updateValue(self, value):
		# Raw controls have no arg to read back — suppress the "Current:" label.
		pass


def makeCard(ref, control, dcsDirectManager, parent=None):
	"""Factory — pick the right card subclass for a control dict."""
	if 'indicationId' in control:
		return ReadOnlyCard(ref, control, dcsDirectManager, parent)
	controlType = control.get('type', '')
	if controlType == 'discrete':
		return DiscreteCard(ref, control, dcsDirectManager, parent)
	if controlType == 'continuous':
		return ContinuousCard(ref, control, dcsDirectManager, parent)
	if controlType == 'relative':
		if control.get('wheel'):
			return WheelCard(ref, control, dcsDirectManager, parent)
		return RelativeCard(ref, control, dcsDirectManager, parent)
	if controlType == 'toggle':
		return ToggleCard(ref, control, dcsDirectManager, parent)
	if controlType == 'raw':
		return RawCard(ref, control, dcsDirectManager, parent)
	# Default: read-only (no type, unknown type, arg-only).
	return ReadOnlyCard(ref, control, dcsDirectManager, parent)


###############################################################################
# Polling worker
###############################################################################

class PollWorker(QtCore.QObject):
	"""Runs batched getControlState calls off the UI thread.

	Maintains two ref sets (fast/slow) and emits `valuesUpdated` to deliver
	results back to the main thread.  Kicked with `kick(fastRefs, slowRefs)`
	whenever the monitored set changes.
	"""

	valuesUpdated = QtCore.Signal(dict)

	def __init__(self, dcsDirectManager):
		super().__init__()
		self.dcsDirectManager = dcsDirectManager
		self._lock = threading.Lock()
		self._fastRefs = []
		self._slowRefs = []
		self._stopEvent = threading.Event()
		self._tickSinceSlow = 0
		self._tickCount = 0

	@QtCore.Slot(list, list)
	def setRefs(self, fastRefs, slowRefs):
		with self._lock:
			self._fastRefs = list(fastRefs)
			self._slowRefs = list(slowRefs)

	@QtCore.Slot()
	def stop(self):
		self._stopEvent.set()

	@QtCore.Slot()
	def pollAll(self):
		"""Force-poll all refs immediately, ignoring the slow-tick rate limiter."""
		if self._stopEvent.is_set():
			return
		with self._lock:
			fastRefs = list(self._fastRefs)
			slowRefs = list(self._slowRefs)
		self._tickSinceSlow = 0
		refs = fastRefs + slowRefs
		if not refs:
			return
		self._runPoll(refs, label='forceRefresh')

	@QtCore.Slot()
	def pollOnce(self):
		"""Perform one poll cycle.  Called from a QTimer in the worker thread."""
		if self._stopEvent.is_set():
			return
		with self._lock:
			fastRefs = list(self._fastRefs)
			slowRefs = list(self._slowRefs)

		# Always poll fast.  Poll slow every Nth tick where N = slow/fast.
		ratio = max(1, POLL_READONLY_MS // POLL_INTERACTIVE_MS)
		self._tickSinceSlow += 1
		doSlow = self._tickSinceSlow >= ratio
		if doSlow:
			self._tickSinceSlow = 0

		refs = list(fastRefs)
		if doSlow:
			refs.extend(slowRefs)
		if not refs:
			return

		self._runPoll(refs, label='slow' if doSlow else 'fast')

	def _runPoll(self, refs, label):
		"""Shared body of pollOnce / pollAll.

		Uses `pollControlStates` so all arg-style refs go in one BULKQ round
		trip — a slow or unresponsive arg can no longer stall the rest of the
		monitored set.  Adds the wheel "extra args" fan-out and emits the
		combined payload.  Logs per-tick stats when DEBUG_POLL is on.
		"""
		self._tickCount += 1
		startedAt = time.monotonic()

		try:
			results = self.dcsDirectManager.pollControlStates(refs)
		except Exception as exc:
			print(f'[DCSControlPanel] pollControlStates failed ({label}): {exc}')
			return

		payload = {}
		for result in results:
			if len(result) >= 3:
				payload[result[0]] = result[2]
			if len(result) >= 4 and result[3] is not None:
				payload[f'{result[0]}#raw'] = result[3]

		# Extra-arg side queries: wheel controls have a pulse arg and
		# (sometimes) a multi-arg displayArgs chain.  pollControlStates
		# returns just one value per ref (displayArgs[0] for wheels), so
		# fetch the remaining args here and stash them under synthetic
		# keys `<ref>#extra:<arg>` for the UI to route to updateExtraArg.
		extraArgsByRef = {}
		extraArgsAll = set()
		for ref in refs:
			if '/' in ref:
				moduleName, controlName = ref.split('/', 1)
			else:
				moduleName, controlName = None, ref
			control = self.dcsDirectManager._lookupControl(controlName, moduleName)
			if not control or not control.get('wheel'):
				continue
			displayArgs = control.get('displayArgs') or []
			if not displayArgs:
				continue
			# Master (displayArgs[0]) is already in the main payload.
			extras = list(displayArgs[1:])
			pulseArg = control.get('arg')
			if pulseArg is not None and pulseArg != -1 and pulseArg not in displayArgs:
				extras.append(pulseArg)
			if extras:
				extraArgsByRef[ref] = [int(a) for a in extras]
				extraArgsAll.update(int(a) for a in extras)

		if extraArgsAll:
			extraValues = self.dcsDirectManager.bulkQueryArgs(list(extraArgsAll), timeout=2.0)
			if extraValues:
				for ref, args in extraArgsByRef.items():
					for arg in args:
						val = extraValues.get(arg)
						if val is not None:
							payload[f'{ref}#extra:{arg}'] = val

		elapsedMs = (time.monotonic() - startedAt) * 1000.0
		if DEBUG_POLL:
			stats = self.dcsDirectManager.getQueryStats()
			print(
				f'[DCSControlPanel] poll#{self._tickCount} ({label}): '
				f'{len(refs)} refs, {elapsedMs:.1f} ms, payload={len(payload)} '
				f'| stats={stats}'
			)

		if payload:
			self.valuesUpdated.emit(payload)


###############################################################################
# Snapshot Tool
###############################################################################

class SnapshotPanel(QtWidgets.QWidget):
	"""Self-contained snapshot and diff panel for control discovery.

	Workflow: take a cockpit state snapshot, move a switch in the cockpit,
	click Find Changed, and the panel shows which controls changed and by
	how much.  Double-click any result to add it to the main monitor panel.

	Designed as a plain QWidget (not QDialog or QMainWindow) so it can be
	reparented into the DCSControlPanelApp sidebar in a future refactor
	without any internal changes.
	"""

	# Emitted with the 'module/canonical' ref when the user double-clicks a result row.
	controlSelected = QtCore.Signal(str)

	# Internal — delivers (action, result) from worker thread to UI thread.
	_snapshotDone = QtCore.Signal(object)

	def __init__(self, dcsDirectManager, currentModule=None, parent=None):
		super().__init__(parent)
		self._dcsDirectManager = dcsDirectManager
		self._snapshot = None		# Stored as {'mode': 'mapped'|'raw', 'data': dict, 'module': str|None, 'takenAt': str}
		self._lastFind = None		# The latest Find Changed result, same shape as _snapshot.
		self._snapshotDone.connect(self._onSnapshotDone)
		self._buildUi()
		self._refreshModuleCombo(currentModule)

	def _buildUi(self):
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(6, 6, 6, 6)
		layout.setSpacing(6)

		# Module selector
		moduleRow = QtWidgets.QHBoxLayout()
		moduleRow.addWidget(QtWidgets.QLabel('Module:'))
		self._moduleCombo = QtWidgets.QComboBox()
		moduleRow.addWidget(self._moduleCombo, 1)
		layout.addLayout(moduleRow)

		self._telemetryCheck = QtWidgets.QCheckBox('Include telemetry (loadout, engines, fuel, gear, position...)')
		self._telemetryCheck.setToolTip('Also compare the LoGet* telemetry, as telemetry/... refs a script can read.  Mission time is left out.')
		self._telemetryCheck.setChecked(True)
		layout.addWidget(self._telemetryCheck)

		# Status label
		self._statusLabel = QtWidgets.QLabel('No snapshot taken.')
		self._statusLabel.setWordWrap(True)
		layout.addWidget(self._statusLabel)

		# Action buttons
		btnRow = QtWidgets.QHBoxLayout()
		self._takeBtn = QtWidgets.QPushButton('Take Snapshot')
		self._takeBtn.clicked.connect(self._onTakeSnapshot)
		self._findBtn = QtWidgets.QPushButton('Find Changed')
		self._findBtn.setEnabled(False)
		self._findBtn.clicked.connect(self._onFindChanged)
		self._clearBtn = QtWidgets.QPushButton('Clear')
		self._clearBtn.clicked.connect(self._onClear)
		self._copyBtn = QtWidgets.QPushButton('Copy Changes')
		self._copyBtn.setToolTip('Copy the changed controls to the clipboard as JSON.')
		self._copyBtn.setEnabled(False)
		self._copyBtn.clicked.connect(self._onCopy)
		self._saveBtn = QtWidgets.QPushButton('Save...')
		self._saveBtn.setToolTip('Save the changed controls and both full snapshots to a JSON file.')
		self._saveBtn.setEnabled(False)
		self._saveBtn.clicked.connect(self._onSave)
		btnRow.addWidget(self._takeBtn)
		btnRow.addWidget(self._findBtn)
		btnRow.addWidget(self._clearBtn)
		btnRow.addWidget(self._copyBtn)
		btnRow.addWidget(self._saveBtn)
		layout.addLayout(btnRow)

		# Sim command row: send an iCommand between Take Snapshot and Find Changed to see what it does.
		simRow = QtWidgets.QHBoxLayout()
		simRow.addWidget(QtWidgets.QLabel('Sim command:'))
		simCommandNames = sorted(loadSimCommands(), key=str.lower)
		self._simCommandCombo = QtWidgets.QComboBox()
		self._simCommandCombo.setEditable(True)
		self._simCommandCombo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
		self._simCommandCombo.addItems(simCommandNames)
		self._simCommandCombo.setCurrentIndex(-1)
		self._simCommandCombo.lineEdit().setPlaceholderText('iCommand name or number')
		simCompleter = QtWidgets.QCompleter(simCommandNames, self._simCommandCombo)
		simCompleter.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
		simCompleter.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
		self._simCommandCombo.setCompleter(simCompleter)
		self._simCommandCombo.lineEdit().returnPressed.connect(self._onSendSimCommand)
		self._simValueEdit = QtWidgets.QLineEdit()
		self._simValueEdit.setPlaceholderText('value (optional)')
		self._simValueEdit.setFixedWidth(110)
		self._simValueEdit.returnPressed.connect(self._onSendSimCommand)
		self._simSendBtn = QtWidgets.QPushButton('Send')
		self._simSendBtn.setToolTip('Send the iCommand with LoSetCommand.  Commands that keep going until stopped need their stop command sent next.')
		self._simSendBtn.clicked.connect(self._onSendSimCommand)
		simRow.addWidget(self._simCommandCombo, 1)
		simRow.addWidget(self._simValueEdit)
		simRow.addWidget(self._simSendBtn)
		layout.addLayout(simRow)

		# Results table
		self._table = QtWidgets.QTableWidget(0, 5)
		self._table.setHorizontalHeaderLabels(['Description', 'Canonical Name', 'Before', 'After', 'Arg#'])
		hdr = self._table.horizontalHeader()
		hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
		hdr.setStretchLastSection(False)
		hdr.resizeSection(0, 200)
		hdr.resizeSection(1, 200)
		hdr.resizeSection(2, 70)
		hdr.resizeSection(3, 70)
		hdr.resizeSection(4, 50)
		self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
		self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
		self._table.doubleClicked.connect(self._onTableDoubleClick)
		layout.addWidget(self._table, 1)

	def _refreshModuleCombo(self, selectModule=None):
		self._moduleCombo.blockSignals(True)
		self._moduleCombo.clear()
		modules = sorted(self._dcsDirectManager.controlMappings.keys())
		for m in modules:
			self._moduleCombo.addItem(m)
		self._moduleCombo.addItem('(raw scan 0\u2013999)')
		if selectModule and selectModule in modules:
			self._moduleCombo.setCurrentText(selectModule)
		self._moduleCombo.blockSignals(False)

	def _isRawScanMode(self):
		return self._moduleCombo.currentText() == '(raw scan 0\u2013999)'

	def _selectedModuleName(self):
		if self._isRawScanMode():
			return None
		return self._moduleCombo.currentText() or None

	def _setButtonsEnabled(self, enabled):
		self._takeBtn.setEnabled(enabled)
		self._clearBtn.setEnabled(enabled)
		if not enabled:
			self._findBtn.setEnabled(False)
			self._copyBtn.setEnabled(False)
			self._saveBtn.setEnabled(False)

	def _readState(self, rawScan, moduleName, includeTelemetry):
		"""Cockpit args (and telemetry if asked for), or None if DCS didn't answer.  Runs on a worker thread."""
		if rawScan:
			result = self._dcsDirectManager.rawScanSnapshot()
		else:
			result = self._dcsDirectManager.snapshotCockpitState(moduleName)
		if result is not None and includeTelemetry:
			result.update(self._dcsDirectManager.snapshotTelemetry())
		return result

	def _onTakeSnapshot(self):
		self._setButtonsEnabled(False)
		self._statusLabel.setText('Taking snapshot...')
		rawScan = self._isRawScanMode()
		moduleName = self._selectedModuleName()
		includeTelemetry = self._telemetryCheck.isChecked()

		def worker():
			self._snapshotDone.emit(('take', rawScan, self._readState(rawScan, moduleName, includeTelemetry)))

		threading.Thread(target=worker, daemon=True).start()

	def _onFindChanged(self):
		self._setButtonsEnabled(False)
		self._statusLabel.setText('Finding changes...')
		rawScan = self._isRawScanMode()
		moduleName = self._selectedModuleName()
		# Use the snapshot's setting, so toggling the checkbox in between doesn't show every telemetry value as changed.
		includeTelemetry = self._snapshot is not None and self._snapshot['telemetry']

		def worker():
			self._snapshotDone.emit(('find', rawScan, self._readState(rawScan, moduleName, includeTelemetry)))

		threading.Thread(target=worker, daemon=True).start()

	def _onSendSimCommand(self):
		name = self._simCommandCombo.currentText().strip()
		commandId, value, error = parseSimCommandEntry(name, self._simValueEdit.text())
		if error:
			self._statusLabel.setText(f'Sim command not sent: {error}')
			return
		label = f'{name} ({commandId})' if name != str(commandId) else name
		if value is not None:
			label += f' = {value:g}'
		if self._dcsDirectManager.sendSimCommand(commandId, value):
			self._statusLabel.setText(f"Sent sim command {label} at {datetime.now().strftime('%H:%M:%S')}.")
		else:
			self._statusLabel.setText(f'Could not send sim command {label} (not connected?).')

	def _onSnapshotDone(self, payload):
		action, rawScan, result = payload
		self._takeBtn.setEnabled(True)
		self._clearBtn.setEnabled(True)

		if result is None:
			self._statusLabel.setText('Error: no response from DCS (not connected?).')
			if self._snapshot is not None:
				self._findBtn.setEnabled(True)
			self._setExportEnabled()
			return

		if action == 'take':
			includeTelemetry = self._telemetryCheck.isChecked()
			self._snapshot = {'mode': 'raw' if rawScan else 'mapped', 'data': result, 'module': None if rawScan else self._selectedModuleName(), 'telemetry': includeTelemetry, 'takenAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
			self._lastFind = None
			telemetryCount = sum(1 for ref in result if _isTelemetryRef(ref))
			ts = datetime.now().strftime('%H:%M:%S')
			counts = f'{len(result) - telemetryCount} controls' + (f' and {telemetryCount} telemetry values' if includeTelemetry else '')
			self._statusLabel.setText(f'Snapshot taken at {ts} \u2014 {counts}.')
			self._findBtn.setEnabled(True)
			self._setExportEnabled()
			self._table.setRowCount(0)

		elif action == 'find':
			if self._snapshot is None:
				self._statusLabel.setText('No snapshot to compare against.')
				return
			self._findBtn.setEnabled(True)
			self._lastFind = {'mode': 'raw' if rawScan else 'mapped', 'data': result, 'takenAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
			self._setExportEnabled()
			self._populateDiffTable(self._snapshot['data'], result, rawScan)

	def _setExportEnabled(self):
		ready = self._snapshot is not None and self._lastFind is not None and self._lastFind['mode'] == self._snapshot['mode']
		self._copyBtn.setEnabled(ready)
		self._saveBtn.setEnabled(ready)

	def _report(self, includeSnapshots):
		return snapshotReport(
			self._snapshot['data'], self._lastFind['data'], self._dcsDirectManager.controlIndex, self._dcsDirectManager._reverseTranslateValue,
			self._snapshot['module'], self._snapshot['mode'] == 'raw', self._snapshot['takenAt'], self._lastFind['takenAt'], includeSnapshots=includeSnapshots,
		)

	def _onCopy(self):
		report = self._report(includeSnapshots=False)
		QtWidgets.QApplication.clipboard().setText(json.dumps(report, indent='\t'))
		self._statusLabel.setText(f"Copied {len(report['changes'])} change(s) to the clipboard as JSON.")

	def _onSave(self):
		module = (self._snapshot['module'] or 'rawScan').replace(' ', '_')
		defaultName = f"snapshot-{module}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
		path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save snapshot comparison', defaultName, 'JSON files (*.json)')
		if not path:
			return
		report = self._report(includeSnapshots=True)
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(report, f, indent='\t')
		self._statusLabel.setText(f"Saved {len(report['changes'])} change(s) and both snapshots to {path}")

	def _populateDiffTable(self, before, after, rawScan):
		changed = changedRefs(before, after)

		self._table.setRowCount(0)
		for ref in changed:
			row = self._table.rowCount()
			self._table.insertRow(row)

			if _isTelemetryRef(ref):
				descItem = QtWidgets.QTableWidgetItem(telemetryControl(ref.partition('/')[2])['description'])
				nameItem = QtWidgets.QTableWidgetItem(ref)
				nameItem.setData(QtCore.Qt.ItemDataRole.UserRole, ref)
				argItem = QtWidgets.QTableWidgetItem('')
			elif rawScan:
				# Raw scan: ref is an int arg number.
				descItem = QtWidgets.QTableWidgetItem('')
				nameItem = QtWidgets.QTableWidgetItem('')
				argItem = QtWidgets.QTableWidgetItem(str(ref))
			else:
				# Mapped snapshot: ref is 'moduleName/canonical'.
				control = self._dcsDirectManager.controlIndex.get(ref, {})
				_, _, canonical = ref.partition('/')
				desc = control.get('description', '')
				if control.get('wheel') and control.get('displayArgs'):
					argNum = control['displayArgs'][0]
				else:
					argNum = control.get('arg', '')
				descItem = QtWidgets.QTableWidgetItem(desc)
				nameItem = QtWidgets.QTableWidgetItem(canonical)
				nameItem.setData(QtCore.Qt.ItemDataRole.UserRole, ref)
				argItem = QtWidgets.QTableWidgetItem(str(argNum))

			beforeItem = QtWidgets.QTableWidgetItem(formatSnapshotValue(before.get(ref)))
			afterItem = QtWidgets.QTableWidgetItem(formatSnapshotValue(after.get(ref)))

			for col, item in enumerate([descItem, nameItem, beforeItem, afterItem, argItem]):
				item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
				self._table.setItem(row, col, item)

		count = len(changed)
		self._statusLabel.setText(f'{count} change(s) found.' if count > 0 else 'No changes detected.')

	def _onTableDoubleClick(self, index):
		row = index.row()
		nameItem = self._table.item(row, 1)
		if nameItem:
			ref = nameItem.data(QtCore.Qt.ItemDataRole.UserRole)
			if ref:
				self.controlSelected.emit(ref)

	def _onClear(self):
		self._snapshot = None
		self._lastFind = None
		self._findBtn.setEnabled(False)
		self._setExportEnabled()
		self._table.setRowCount(0)
		self._statusLabel.setText('No snapshot taken.')


class SnapshotWindow(QtWidgets.QMainWindow):
	"""Thin standalone window hosting a SnapshotPanel as its central widget.

	The SnapshotPanel is accessible via .panel for signal wiring.
	This wrapper exists only to provide a window frame; all logic lives in
	SnapshotPanel so it can be reparented into the sidebar in a future refactor.
	"""

	def __init__(self, dcsDirectManager, currentModule=None, parent=None):
		super().__init__(parent)
		self.setWindowTitle('Snapshot Tool \u2014 DCS Control Panel')
		self.resize(800, 600)
		self.panel = SnapshotPanel(dcsDirectManager, currentModule=currentModule, parent=self)
		self.setCentralWidget(self.panel)


###############################################################################
# Indicator scan tool
###############################################################################

class IndicatorScanPanel(QtWidgets.QWidget):
	"""Scan a range of DCS indication IDs and show which fields return text.

	Useful for discovering which indication ID and field name contains specific
	cockpit text (e.g. CDU page content) without knowing the ID in advance.

	The scan queries each ID once via queryIndication(); results are shown in a
	table and can be filtered live by field name or text value.  Double-clicking
	a result emits controlSelected with the full 'module/canonical' ref so the
	caller can add it to the monitor panel.
	"""

	# Emitted with 'module/canonical' ref on double-click (if found in mapping).
	controlSelected = QtCore.Signal(str)

	# Internal cross-thread signals.
	_scanProgress = QtCore.Signal(int, int)		# (current, total)
	_scanFinished = QtCore.Signal(list)			# list of (indicationId, fieldName, value)

	_MAX_RANGE = 2000

	def __init__(self, dcsDirectManager, currentModule=None, parent=None):
		super().__init__(parent)
		self._dcsDirectManager = dcsDirectManager
		self._cancelFlag = False
		self._scanProgress.connect(self._onProgress)
		self._scanFinished.connect(self._onFinished)
		self._buildUi()
		self._refreshModuleCombo(currentModule)

	def _buildUi(self):
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(6, 6, 6, 6)
		layout.setSpacing(6)

		# Module selector
		moduleRow = QtWidgets.QHBoxLayout()
		moduleRow.addWidget(QtWidgets.QLabel('Module:'))
		self._moduleCombo = QtWidgets.QComboBox()
		moduleRow.addWidget(self._moduleCombo, 1)
		layout.addLayout(moduleRow)

		# Range row
		rangeRow = QtWidgets.QHBoxLayout()
		rangeRow.addWidget(QtWidgets.QLabel('Range:'))
		self._startSpin = QtWidgets.QSpinBox()
		self._startSpin.setRange(0, 9999)
		self._startSpin.setValue(0)
		rangeRow.addWidget(self._startSpin)
		rangeRow.addWidget(QtWidgets.QLabel('–'))
		self._endSpin = QtWidgets.QSpinBox()
		self._endSpin.setRange(0, 9999)
		self._endSpin.setValue(20)
		rangeRow.addWidget(self._endSpin)
		rangeRow.addStretch(1)
		layout.addLayout(rangeRow)

		# Filter + buttons row
		filterRow = QtWidgets.QHBoxLayout()
		filterRow.addWidget(QtWidgets.QLabel('Filter:'))
		self._filterEdit = QtWidgets.QLineEdit()
		self._filterEdit.setPlaceholderText('search field names or values…')
		self._filterEdit.textChanged.connect(self._applyFilter)
		filterRow.addWidget(self._filterEdit, 1)
		self._scanBtn = QtWidgets.QPushButton('Scan')
		self._scanBtn.clicked.connect(self._onScan)
		filterRow.addWidget(self._scanBtn)
		self._cancelBtn = QtWidgets.QPushButton('Cancel')
		self._cancelBtn.setEnabled(False)
		self._cancelBtn.clicked.connect(self._onCancel)
		filterRow.addWidget(self._cancelBtn)
		layout.addLayout(filterRow)

		# Progress bar (hidden until scan starts)
		self._progressBar = QtWidgets.QProgressBar()
		self._progressBar.setRange(0, 100)
		self._progressBar.hide()
		layout.addWidget(self._progressBar)

		# Results table
		self._table = QtWidgets.QTableWidget(0, 3)
		self._table.setHorizontalHeaderLabels(['ID', 'Field Name', 'Value'])
		hdr = self._table.horizontalHeader()
		hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
		hdr.resizeSection(0, 50)
		hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
		hdr.resizeSection(1, 200)
		hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
		self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
		self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
		self._table.doubleClicked.connect(self._onTableDoubleClick)
		layout.addWidget(self._table, 1)

		# Status label
		self._statusLabel = QtWidgets.QLabel('Ready.')
		layout.addWidget(self._statusLabel)

	def _refreshModuleCombo(self, selectModule=None):
		self._moduleCombo.blockSignals(True)
		self._moduleCombo.clear()
		modules = sorted(self._dcsDirectManager.controlMappings.keys())
		for m in modules:
			self._moduleCombo.addItem(m)
		if selectModule and selectModule in modules:
			self._moduleCombo.setCurrentText(selectModule)
		self._moduleCombo.blockSignals(False)

	def _onScan(self):
		start = self._startSpin.value()
		end = self._endSpin.value()
		if start > end:
			self._statusLabel.setText('Error: start must be ≤ end.')
			return
		count = end - start + 1
		if count > self._MAX_RANGE:
			self._statusLabel.setText(f'Error: range too large (max {self._MAX_RANGE} IDs).')
			return

		self._table.setRowCount(0)
		self._cancelFlag = False
		self._scanBtn.setEnabled(False)
		self._cancelBtn.setEnabled(True)
		self._progressBar.setValue(0)
		self._progressBar.show()
		self._statusLabel.setText('Scanning…')

		def worker():
			results = []
			total = end - start + 1
			for i, indicationId in enumerate(range(start, end + 1)):
				if self._cancelFlag:
					break
				indication = self._dcsDirectManager.queryIndication(indicationId, timeout=1.0)
				if indication:
					for fieldName, value in indication.items():
						if value and value.strip():
							results.append((indicationId, fieldName, value.strip()))
				if (i + 1) % 5 == 0 or i == total - 1:
					self._scanProgress.emit(i + 1, total)
			self._scanFinished.emit(results)

		threading.Thread(target=worker, daemon=True).start()

	def _onCancel(self):
		self._cancelFlag = True

	def _onProgress(self, current, total):
		pct = int(current * 100 / total) if total > 0 else 0
		self._progressBar.setValue(pct)
		self._statusLabel.setText(f'Scanning… {current}/{total}')

	def _onFinished(self, results):
		self._scanBtn.setEnabled(True)
		self._cancelBtn.setEnabled(False)
		self._progressBar.hide()

		if self._cancelFlag:
			self._statusLabel.setText(f'Cancelled — {len(results)} result(s) so far.')
		else:
			self._statusLabel.setText(f'Done — {len(results)} non-empty field(s) found.')

		self._table.setRowCount(0)
		for indicationId, fieldName, value in results:
			row = self._table.rowCount()
			self._table.insertRow(row)
			idItem = QtWidgets.QTableWidgetItem(str(indicationId))
			idItem.setData(QtCore.Qt.ItemDataRole.UserRole, indicationId)
			nameItem = QtWidgets.QTableWidgetItem(fieldName)
			valueItem = QtWidgets.QTableWidgetItem(value)
			for col, item in enumerate([idItem, nameItem, valueItem]):
				item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
				self._table.setItem(row, col, item)

		self._applyFilter()

	def _applyFilter(self):
		text = self._filterEdit.text().lower()
		for row in range(self._table.rowCount()):
			nameItem = self._table.item(row, 1)
			valueItem = self._table.item(row, 2)
			fieldName = nameItem.text().lower() if nameItem else ''
			value = valueItem.text().lower() if valueItem else ''
			hidden = bool(text) and text not in fieldName and text not in value
			self._table.setRowHidden(row, hidden)

	def _onTableDoubleClick(self, index):
		row = index.row()
		idItem = self._table.item(row, 0)
		nameItem = self._table.item(row, 1)
		if not idItem or not nameItem:
			return
		indicationId = idItem.data(QtCore.Qt.ItemDataRole.UserRole)
		fieldName = nameItem.text()
		moduleName = self._moduleCombo.currentText() or None
		if moduleName:
			ref = f'{moduleName}/ind.{indicationId}.{fieldName}'
			if ref in self._dcsDirectManager.controlIndex:
				self.controlSelected.emit(ref)
				return
		# Not in the mapping — copy canonical form to clipboard as a hint.
		canonical = f'ind.{indicationId}.{fieldName}'
		QtWidgets.QApplication.clipboard().setText(canonical)
		self._statusLabel.setText(f'Not in mapping — copied {canonical!r} to clipboard.')


class IndicatorScanWindow(QtWidgets.QMainWindow):
	"""Thin standalone window hosting an IndicatorScanPanel."""

	def __init__(self, dcsDirectManager, currentModule=None, parent=None):
		super().__init__(parent)
		self.setWindowTitle('Indicator Text Scan \u2014 DCS Control Panel')
		self.resize(700, 500)
		self.panel = IndicatorScanPanel(dcsDirectManager, currentModule=currentModule, parent=self)
		self.setCentralWidget(self.panel)


###############################################################################
# Main window
###############################################################################

class DCSControlPanelApp(QtWidgets.QMainWindow):
	"""Main window — picker on the left, scrollable card stack on the right."""

	# Signals fired from the UI thread to the poll worker.
	_updateWorkerRefs = QtCore.Signal(list, list)
	_forceRefresh = QtCore.Signal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle(f'DCS Control Panel {APP_VERSION}')
		self.resize(1300, 800)
		self.setMinimumSize(1000, 500)

		self.settingsManager = SettingsManager()
		self.config = self.settingsManager.config

		self.dcsDirectManager = DCSDirectManager(self.config)
		self.dcsDirectManager.start()

		# monitoredControls: list of 'module/canonical' refs, canonical form.
		self.monitoredControls = []
		# cards: dict ref -> ControlCard widget currently displayed.
		self.cards = {}

		# Snapshot tool window — created lazily, kept as a single instance.
		self._snapshotWindow = None
		# Indicator scan window — created lazily, kept as a single instance.
		self._scanWindow = None
		# mtime of SAVE_FILE at the last point the app wrote it or synced from it.
		# Used to detect external modifications before overwriting.
		self._lastSavedMtime = 0.0

		self._buildUi()
		uiState = self._loadMonitoredControls()
		self._lastSavedMtime = os.path.getmtime(SAVE_FILE) if os.path.exists(SAVE_FILE) else 0.0
		self._populateModuleDropdown()
		# Restore the last-used module/category/search from the settings file.
		if savedModule := uiState.get('module', ''):
			if self.moduleCombo.findText(savedModule) >= 0:
				self.moduleCombo.setCurrentText(savedModule)
		if savedCategory := uiState.get('category', ''):
			if self.categoryCombo.findText(savedCategory) >= 0:
				self.categoryCombo.setCurrentText(savedCategory)
		if savedSearch := uiState.get('search', ''):
			self.searchEdit.setText(savedSearch)
		# Start the poll worker BEFORE pushing the initial ref list — the
		# `_updateWorkerRefs` signal is connected to the worker's slot inside
		# `_startPollWorker`, so emitting beforehand loses the initial refs
		# and cards stay empty until the user adds/removes one.
		self._startPollWorker()
		self._rebuildCardsFromMonitored()
		self._refreshStatusBar()
		self._statusTimer = QtCore.QTimer(self)
		self._statusTimer.setInterval(1000)
		self._statusTimer.timeout.connect(self._refreshStatusBar)
		self._statusTimer.start()

	# ---- UI construction ----

	def _buildUi(self):
		central = QtWidgets.QWidget()
		self.setCentralWidget(central)

		rootLayout = QtWidgets.QHBoxLayout(central)
		rootLayout.setContentsMargins(5, 5, 5, 5)
		rootLayout.setSpacing(5)

		# Left column
		leftColumn = QtWidgets.QWidget()
		leftColumn.setMinimumWidth(340)
		leftColumn.setMaximumWidth(420)
		leftLayout = QtWidgets.QVBoxLayout(leftColumn)
		leftLayout.setContentsMargins(0, 0, 0, 0)
		leftLayout.setSpacing(6)

		# Module dropdown
		leftLayout.addWidget(QtWidgets.QLabel('Module:'))
		self.moduleCombo = QtWidgets.QComboBox()
		self.moduleCombo.currentTextChanged.connect(self._onModuleChanged)
		self.moduleCombo.currentTextChanged.connect(self._saveUiState)
		leftLayout.addWidget(self.moduleCombo)

		# Category dropdown
		leftLayout.addWidget(QtWidgets.QLabel('Category:'))
		self.categoryCombo = QtWidgets.QComboBox()
		self.categoryCombo.currentTextChanged.connect(self._refreshControlList)
		self.categoryCombo.currentTextChanged.connect(self._saveUiState)
		leftLayout.addWidget(self.categoryCombo)

		# Search
		searchRow = QtWidgets.QHBoxLayout()
		self.searchEdit = QtWidgets.QLineEdit()
		self.searchEdit.setPlaceholderText('Filter (name or description)...')
		self.searchEdit.textChanged.connect(self._refreshControlList)
		self.searchEdit.textChanged.connect(self._saveUiState)
		searchRow.addWidget(self.searchEdit, 1)
		clearBtn = QtWidgets.QPushButton('X')
		clearBtn.setFixedWidth(28)
		clearBtn.clicked.connect(lambda: self.searchEdit.setText(''))
		searchRow.addWidget(clearBtn)
		leftLayout.addLayout(searchRow)

		# Available controls list
		self.controlList = QtWidgets.QListWidget()
		self.controlList.itemDoubleClicked.connect(lambda _: self._addSelectedControl())
		leftLayout.addWidget(self.controlList, 1)

		addBtn = QtWidgets.QPushButton('Add to Monitor')
		addBtn.clicked.connect(self._addSelectedControl)
		leftLayout.addWidget(addBtn)

		clearAllBtn = QtWidgets.QPushButton('Clear All')
		clearAllBtn.clicked.connect(self._clearMonitored)
		leftLayout.addWidget(clearAllBtn)

		rootLayout.addWidget(leftColumn, 0)

		# Right column: thin toolbar + scrollable card stack.
		rightColumn = QtWidgets.QWidget()
		rightLayout = QtWidgets.QVBoxLayout(rightColumn)
		rightLayout.setContentsMargins(0, 0, 0, 0)
		rightLayout.setSpacing(4)

		toolRow = QtWidgets.QHBoxLayout()
		snapshotBtn = QtWidgets.QPushButton('Snapshot Tool...')
		snapshotBtn.setToolTip('Open the cockpit snapshot and diff tool')
		snapshotBtn.clicked.connect(self._openSnapshotTool)
		toolRow.addWidget(snapshotBtn)
		scanBtn = QtWidgets.QPushButton('Indicator Text Scan...')
		scanBtn.setToolTip('Scan indication IDs to find which fields contain specific text')
		scanBtn.clicked.connect(self._openIndicatorScanTool)
		toolRow.addWidget(scanBtn)
		toolRow.addStretch(1)
		syncBtn = QtWidgets.QPushButton('Sync from File')
		syncBtn.setToolTip('Reload DCSControlPanelSettings.json and refresh all control mappings')
		syncBtn.clicked.connect(self._syncFromFile)
		toolRow.addWidget(syncBtn)
		refreshBtn = QtWidgets.QPushButton('Force Refresh')
		refreshBtn.setToolTip('Reconnect to DCS and re-poll all monitored controls')
		refreshBtn.clicked.connect(self._onForceRefreshClicked)
		toolRow.addWidget(refreshBtn)
		rightLayout.addLayout(toolRow)

		self.scrollArea = QtWidgets.QScrollArea()
		self.scrollArea.setWidgetResizable(True)
		self.cardsContainer = QtWidgets.QWidget()
		self.cardsLayout = QtWidgets.QVBoxLayout(self.cardsContainer)
		self.cardsLayout.setContentsMargins(4, 4, 4, 4)
		self.cardsLayout.setSpacing(6)
		self.cardsLayout.addStretch(1)  # Keep cards top-aligned.
		self.scrollArea.setWidget(self.cardsContainer)
		rightLayout.addWidget(self.scrollArea, 1)
		rootLayout.addWidget(rightColumn, 1)

		# Status bar
		self.statusBar().showMessage('Starting...')

	# ---- Snapshot tool ----

	def _openSnapshotTool(self):
		"""Open (or raise) the cockpit snapshot/diff window."""
		if self._snapshotWindow is None or not self._snapshotWindow.isVisible():
			currentModule = self.moduleCombo.currentText() or None
			self._snapshotWindow = SnapshotWindow(
				self.dcsDirectManager,
				currentModule=currentModule,
			)
			self._snapshotWindow.panel.controlSelected.connect(self._addMonitoredByRef)
		self._snapshotWindow.show()
		self._snapshotWindow.raise_()
		self._snapshotWindow.activateWindow()

	def _openIndicatorScanTool(self):
		"""Open (or raise) the indicator text scan window."""
		if self._scanWindow is None or not self._scanWindow.isVisible():
			currentModule = self.moduleCombo.currentText() or None
			self._scanWindow = IndicatorScanWindow(
				self.dcsDirectManager,
				currentModule=currentModule,
			)
			self._scanWindow.panel.controlSelected.connect(self._addMonitoredByRef)
		self._scanWindow.show()
		self._scanWindow.raise_()
		self._scanWindow.activateWindow()

	# ---- Population ----

	def _populateModuleDropdown(self):
		modules = moduleNamesForDropdown(self.dcsDirectManager.controlMappings)
		self.moduleCombo.blockSignals(True)
		self.moduleCombo.clear()
		self.moduleCombo.addItems(modules)
		self.moduleCombo.blockSignals(False)
		if modules:
			self._onModuleChanged(modules[0])

	def _getCategoriesForModule(self, moduleName):
		controls = controlsForModule(self.dcsDirectManager.controlMappings, moduleName)
		categories = set()
		for key in controls:
			if '.' in key:
				categories.add(key.split('.', 1)[0])
			else:
				categories.add(key)
		return sorted(categories)

	def _onModuleChanged(self, moduleName):
		self.categoryCombo.blockSignals(True)
		self.categoryCombo.clear()
		self.categoryCombo.addItem('All')
		self.categoryCombo.addItems(self._getCategoriesForModule(moduleName))
		self.categoryCombo.setCurrentText('All')
		self.categoryCombo.blockSignals(False)
		self._refreshControlList()

	def _refreshControlList(self):
		moduleName = self.moduleCombo.currentText()
		if not moduleName:
			self.controlList.clear()
			return
		controls = controlsForModule(self.dcsDirectManager.controlMappings, moduleName)
		selectedCategory = self.categoryCombo.currentText() or 'All'
		filterText = self.searchEdit.text().strip().lower()

		self.controlList.clear()
		for canonical in sorted(controls.keys()):
			category = canonical.split('.', 1)[0] if '.' in canonical else canonical
			if selectedCategory != 'All' and category != selectedCategory:
				continue

			ref = f'{moduleName}/{canonical}'
			controlDict = controls.get(canonical, {}) or {}
			description = controlDict.get('description', '') if isinstance(controlDict, dict) else ''

			display = f'{canonical} — {description}' if description else canonical

			if filterText:
				hay = [canonical.lower(), description.lower()]
				if not any(filterText in h for h in hay):
					continue

			item = QtWidgets.QListWidgetItem(display)
			item.setData(QtCore.Qt.ItemDataRole.UserRole, ref)
			if description:
				item.setToolTip(f'{canonical}\n{description}')
			self.controlList.addItem(item)

	# ---- Monitored list management ----

	def _selectedAvailableRef(self):
		items = self.controlList.selectedItems()
		if not items:
			return None
		return items[0].data(QtCore.Qt.ItemDataRole.UserRole)

	def _addSelectedControl(self):
		ref = self._selectedAvailableRef()
		if not ref:
			return
		self._addMonitoredByRef(ref)

	def _addMonitoredByRef(self, ref):
		"""Add a control ref to the monitored list and create its card."""
		if ref in self.monitoredControls:
			return
		self.monitoredControls.append(ref)
		self._addCard(ref)
		self._saveMonitoredControls()
		self._pushWorkerRefs()

	def _removeMonitoredByRef(self, ref):
		if ref not in self.monitoredControls:
			return
		index = self.monitoredControls.index(ref)
		self.monitoredControls.pop(index)
		self._removeCard(ref)
		self._saveMonitoredControls()
		self._pushWorkerRefs()

	def _clearMonitored(self):
		for ref in list(self.monitoredControls):
			self._removeCard(ref)
		self.monitoredControls.clear()
		self._saveMonitoredControls()
		self._pushWorkerRefs()

	def _onCardMoveRequested(self, ref, direction):
		"""Move a card in response to a reorder button click on the card itself."""
		if ref not in self.monitoredControls:
			return
		index = self.monitoredControls.index(ref)
		last = len(self.monitoredControls) - 1
		if direction == 'up' and index > 0:
			self.monitoredControls[index], self.monitoredControls[index - 1] = (
				self.monitoredControls[index - 1],
				self.monitoredControls[index],
			)
		elif direction == 'down' and index < last:
			self.monitoredControls[index], self.monitoredControls[index + 1] = (
				self.monitoredControls[index + 1],
				self.monitoredControls[index],
			)
		elif direction == 'top' and index > 0:
			self.monitoredControls.insert(0, self.monitoredControls.pop(index))
		elif direction == 'bottom' and index < last:
			self.monitoredControls.append(self.monitoredControls.pop(index))
		else:
			return  # Already at boundary — nothing to do.
		self._reorderCards()
		self._saveMonitoredControls()

	# ---- Cards management ----

	def _addCard(self, ref):
		control = self.dcsDirectManager.getControl(ref)
		if not control:
			return
		card = makeCard(ref, control, self.dcsDirectManager)
		card.removeRequested.connect(self._removeMonitoredByRef)
		card.moveRequested.connect(self._onCardMoveRequested)
		# Insert before the stretch (last item).
		insertAt = max(0, self.cardsLayout.count() - 1)
		self.cardsLayout.insertWidget(insertAt, card)
		self.cards[ref] = card

	def _removeCard(self, ref):
		card = self.cards.pop(ref, None)
		if card is None:
			return
		self.cardsLayout.removeWidget(card)
		card.deleteLater()

	def _rebuildCardsFromMonitored(self):
		# Called once on load.
		for ref in self.monitoredControls:
			self._addCard(ref)
		self._pushWorkerRefs()

	def _reorderCards(self):
		# Remove all card widgets from layout and re-insert in monitoredControls order.
		for ref, card in list(self.cards.items()):
			self.cardsLayout.removeWidget(card)
		# Stretch is still at the end.
		for i, ref in enumerate(self.monitoredControls):
			card = self.cards.get(ref)
			if card:
				self.cardsLayout.insertWidget(i, card)

	# ---- Persistence ----

	def _loadMonitoredControls(self):
		"""Load monitored controls and UI state from SAVE_FILE.

		Returns the uiState dict (empty if file is absent, unreadable, or has no uiState).
		"""
		if not os.path.exists(SAVE_FILE):
			return {}
		try:
			with open(SAVE_FILE, 'r', encoding='utf-8') as f:
				raw = json.load(f)
		except (json.JSONDecodeError, OSError):
			return {}
		# New object format: { "controls": [...], "uiState": {...} }
		if isinstance(raw, dict):
			controlsList = raw.get('controls', [])
			uiState = raw.get('uiState', {})
		elif isinstance(raw, list):
			# Legacy flat-list format — read controls, no uiState.
			controlsList = raw
			uiState = {}
		else:
			return {}
		# Silent-drop unresolvable refs.
		resolved = []
		for ref in controlsList:
			if not isinstance(ref, str) or '/' not in ref:
				continue
			if self.dcsDirectManager.getControl(ref):
				resolved.append(self._canonicalize(ref))
		# De-dupe while preserving order.
		seen = set()
		self.monitoredControls = [r for r in resolved if not (r in seen or seen.add(r))]
		return uiState if isinstance(uiState, dict) else {}

	def _canonicalize(self, ref):
		"""No-op: refs are already in canonical form.  Retained for symmetry."""
		return ref

	def _writeSettingsFile(self):
		"""Write controls and current UI state to SAVE_FILE."""
		data = {
			'controls': self.monitoredControls,
			'uiState': {
				'module': self.moduleCombo.currentText(),
				'category': self.categoryCombo.currentText(),
				'search': self.searchEdit.text(),
			},
		}
		os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
		with open(SAVE_FILE, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent='\t')
		self._lastSavedMtime = os.path.getmtime(SAVE_FILE)

	def _saveUiState(self):
		"""Persist the current module/category/search selection to SAVE_FILE."""
		try:
			self._writeSettingsFile()
		except OSError as exc:
			print(f'[DCSControlPanel] Failed to save UI state: {exc}')

	def _hasExternalChanges(self):
		"""Return True if SAVE_FILE has been modified externally since the last app save/sync."""
		if not os.path.exists(SAVE_FILE):
			return False
		return os.path.getmtime(SAVE_FILE) > self._lastSavedMtime + 0.01

	def _syncFromFile(self):
		"""Reload SAVE_FILE and control mappings; add/remove cards to match.

		Preserves the current module, category, and search-filter selection so
		the left panel doesn't jump.
		"""
		currentModule = self.moduleCombo.currentText()
		currentCategory = self.categoryCombo.currentText()
		currentSearch = self.searchEdit.text()

		self.dcsDirectManager.reloadControlMappings()

		oldRefs = set(self.monitoredControls)
		self._loadMonitoredControls()
		newRefs = set(self.monitoredControls)

		for ref in oldRefs - newRefs:
			self._removeCard(ref)
		for ref in newRefs - oldRefs:
			self._addCard(ref)
		self._reorderCards()

		self._populateModuleDropdown()
		if currentModule and self.moduleCombo.findText(currentModule) >= 0:
			self.moduleCombo.blockSignals(True)
			self.moduleCombo.setCurrentText(currentModule)
			self.moduleCombo.blockSignals(False)
			# Restore category and search before refreshing so the list rebuilds correctly.
			self.categoryCombo.blockSignals(True)
			self.categoryCombo.setCurrentText(currentCategory)
			self.categoryCombo.blockSignals(False)
			self.searchEdit.blockSignals(True)
			self.searchEdit.setText(currentSearch)
			self.searchEdit.blockSignals(False)
			self._refreshControlList()

		self._pushWorkerRefs()
		self._lastSavedMtime = os.path.getmtime(SAVE_FILE) if os.path.exists(SAVE_FILE) else 0.0

	def _saveMonitoredControls(self):
		if self._hasExternalChanges():
			msg = QtWidgets.QMessageBox(self)
			msg.setWindowTitle('Settings file changed')
			msg.setText(
				'DCSControlPanelSettings.json has been modified externally.\n\n'
				'Sync from file (discard current change) or overwrite the file?'
			)
			syncBtn = msg.addButton('Sync from File', QtWidgets.QMessageBox.ButtonRole.RejectRole)
			msg.addButton('Overwrite', QtWidgets.QMessageBox.ButtonRole.AcceptRole)
			msg.setDefaultButton(syncBtn)
			msg.exec()
			if msg.clickedButton() is syncBtn:
				self._syncFromFile()
				return
		try:
			self._writeSettingsFile()
		except OSError as exc:
			print(f'[DCSControlPanel] Failed to save settings: {exc}')

	# ---- Polling worker ----

	def _startPollWorker(self):
		self.workerThread = QtCore.QThread(self)
		self.pollWorker = PollWorker(self.dcsDirectManager)
		self.pollWorker.moveToThread(self.workerThread)
		self._updateWorkerRefs.connect(self.pollWorker.setRefs)
		self._forceRefresh.connect(self.pollWorker.pollAll)
		self.pollWorker.valuesUpdated.connect(self._onValuesUpdated)

		# Timer lives in the worker thread so pollOnce runs off the UI thread.
		def startTimer():
			self._pollTimer = QtCore.QTimer()
			self._pollTimer.setInterval(POLL_INTERACTIVE_MS)
			self._pollTimer.timeout.connect(self.pollWorker.pollOnce)
			self._pollTimer.start()

		self.workerThread.started.connect(startTimer)
		self.workerThread.start()

	@QtCore.Slot()
	def _onForceRefreshClicked(self):
		"""Force Refresh button: drop the DCS-BIOS TCP connection, let the
		manager's background loop reconnect, then re-poll all monitored
		controls.  Symptom this addresses: a freshly added control sometimes
		never gets its current value pulled in (or takes a minute or more),
		because the in-flight poll loop is backlogged behind slow per-ref
		timeouts and the setRefs signal lands behind it.  A real reconnect
		clears any stuck request state in one shot.
		"""
		try:
			self.dcsDirectManager.reconnect()
		except Exception as exc:
			print(f'[DCSControlPanel] reconnect failed: {exc}')
		if hasattr(self, 'statusBar'):
			try:
				self.statusBar().showMessage('Reconnecting to DCS…', 1500)
			except Exception:
				pass
		# Give the background _runLoop a moment to re-open the socket and
		# reload mappings before we fire a fresh poll.
		QtCore.QTimer.singleShot(400, self._forceRefresh.emit)

	def _pushWorkerRefs(self):
		fastRefs = []
		slowRefs = []
		for ref, card in self.cards.items():
			if card.pollIntervalMs >= POLL_READONLY_MS:
				slowRefs.append(ref)
			else:
				fastRefs.append(ref)
		self._updateWorkerRefs.emit(fastRefs, slowRefs)

	@QtCore.Slot(dict)
	def _onValuesUpdated(self, payload):
		for ref, value in payload.items():
			# Synthetic `<ref>#extra:<arg>` entries route to updateExtraArg
			# on the matching wheel card (pulse arg + slave args).
			if '#extra:' in ref:
				baseRef, _, argStr = ref.partition('#extra:')
				card = self.cards.get(baseRef)
				if card is not None and hasattr(card, 'updateExtraArg'):
					try:
						card.updateExtraArg(int(argStr), value)
					except (ValueError, TypeError):
						pass
				continue
			# Synthetic `<ref>#raw` entries route to updateRawValue.
			if ref.endswith('#raw'):
				baseRef = ref[:-4]
				card = self.cards.get(baseRef)
				if card is not None:
					card.updateRawValue(value)
				continue
			card = self.cards.get(ref)
			if card is not None:
				card.updateValue(value)

	# ---- Status bar ----

	def _refreshStatusBar(self):
		msg = getattr(self.dcsDirectManager, 'outputString', '') or 'DCS Direct: (no status)'
		self.statusBar().showMessage(msg)

	# ---- Shutdown ----

	def closeEvent(self, event):
		try:
			self.pollWorker.stop()
		except Exception:
			pass
		try:
			self.workerThread.quit()
			self.workerThread.wait(1500)
		except Exception:
			pass
		try:
			self.dcsDirectManager.stop()
		except Exception:
			pass
		super().closeEvent(event)


###############################################################################
# Entry point
###############################################################################

if __name__ == '__main__':
	applicationPath = os.path.dirname(sys.executable)
	if applicationPath not in sys.path:
		sys.path.append(applicationPath)

	app = QtWidgets.QApplication(sys.argv)
	window = DCSControlPanelApp()
	window.show()
	sys.exit(app.exec())
