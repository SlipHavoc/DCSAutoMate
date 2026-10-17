"""Can a paused live script still need the cockpit, or still use the comms menu?  Used to tell the player when they can leave the cockpit or use the comms menu again.

The cockpit is needed for keyboard commands, and for reading ind. (display text) controls, which DCS only updates while the cockpit is shown.
Comms menu sim commands would be thrown off by the player's own use of the menu.
The answer is True whenever the scan is unsure, and False only when no such step is reachable from where the script is paused.
"""
import ast
import functools
import inspect
import os
import re

from engine.simCommands import isCommsMenuCommand

KEYBOARD_COMMAND = 'scriptKeyboard'
_indicationPattern = re.compile(r'^(?:[^/]+/)?ind\.')
_loopTypes = (ast.For, ast.AsyncFor, ast.While)
_scopeTypes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def isIndicationControl(control):
	"""True for ind. controls ('ind.3.AlignTime' or 'A-10C_2/ind.3.AlignTime'), which only update while the cockpit is shown."""
	return isinstance(control, str) and bool(_indicationPattern.match(control))


def _needsCockpit(value):
	return value == KEYBOARD_COMMAND or isIndicationControl(value)


def _usesCommsMenu(value):
	return isinstance(value, str) and isCommsMenuCommand(value)


def rowNeedsCockpit(command):
	"""True if a command-list row needs the cockpit: a keyboard command, or a wait/loop check on an ind. control."""
	cmd = command.get('cmd', '')
	if cmd == KEYBOARD_COMMAND:
		return True
	return cmd in ('scriptCockpitState', 'scriptLoopUntilStart', 'scriptLoopUntilEnd') and isIndicationControl(command.get('control'))


def mayStillNeedCockpit(generator):
	"""True if the paused generator (or one it is running with yield from) might still send a keyboard command or read an ind. control."""
	return _mayStillReach(generator, _needsCockpit)


def mayStillUseCommsMenu(generator):
	"""True if the paused generator (or one it is running with yield from) might still send a comms menu sim command."""
	return _mayStillReach(generator, _usesCommsMenu)


def _mayStillReach(generator, isStep):
	frame = generator.gi_frame
	if frame is None:
		return False
	inner = generator.gi_yieldfrom
	if inspect.isgenerator(inner) and _mayStillReach(inner, isStep):
		return True
	functionNode = _findFunctionNode(generator.gi_code)
	if functionNode is None:
		return True
	scanner = _Scanner({**frame.f_globals, **frame.f_locals}, _nestedDefs(functionNode), isStep)
	if scanner.stepNameEscapes(functionNode):
		return True
	pausedLine = frame.f_lineno
	loopSpans = [(n.lineno, n.end_lineno) for n in _walkScope(functionNode) if isinstance(n, _loopTypes) and n.lineno <= pausedLine <= n.end_lineno]
	for node in _walkScope(functionNode):
		lineno = getattr(node, 'lineno', None)
		if lineno is not None and (lineno > pausedLine or any(start <= lineno <= end for start, end in loopSpans)):
			if scanner.nodeMaySend(node):
				return True
	return False


class _Scanner:
	"""Checks AST nodes for steps matching isStep, following calls to functions it can resolve by name."""

	def __init__(self, namespace, staticDefs, isStep):
		self.namespace = namespace
		self.staticDefs = staticDefs
		self.isStep = isStep
		self.visited = set()

	def nodeMaySend(self, node):
		if isinstance(node, ast.Constant) and self.isStep(node.value):
			return True
		if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
			return self.calledFunctionMaySend(node.func.id)
		return False

	def calledFunctionMaySend(self, name):
		if name in self.staticDefs:
			return self.bodyMaySend(self.staticDefs[name])
		target = self.namespace.get(name)
		if not inspect.isfunction(target) or target in self.visited:
			return False
		self.visited.add(target)
		functionNode = _findFunctionNode(target.__code__)
		if functionNode is None:
			return True
		closure = {}
		for varName, cell in zip(target.__code__.co_freevars, target.__closure__ or ()):
			try:
				closure[varName] = cell.cell_contents
			except ValueError:
				pass
		inner = _Scanner({**target.__globals__, **closure}, _nestedDefs(functionNode), self.isStep)
		inner.visited = self.visited
		return inner.bodyMaySend(functionNode)

	def bodyMaySend(self, functionNode):
		if id(functionNode) in self.visited:
			return False
		self.visited.add(id(functionNode))
		if self.stepNameEscapes(functionNode):
			return True
		return any(self.nodeMaySend(node) for node in _walkScope(functionNode))

	def stepNameEscapes(self, functionNode):
		"""True if a step value ('scriptKeyboard', an ind. control, a comms menu command name) is used other than as a direct call argument (e.g. stored in a variable), which the scan can't follow."""
		for parent in ast.walk(functionNode):
			for child in ast.iter_child_nodes(parent):
				if isinstance(child, ast.Constant) and self.isStep(child.value):
					if not ((isinstance(parent, ast.Call) and child in parent.args) or isinstance(parent, ast.keyword)):
						return True
		return False


def _walkScope(functionNode):
	"""Every node in a function's own body, without descending into nested defs, lambdas or classes."""
	stack = list(functionNode.body)
	while stack:
		node = stack.pop()
		if isinstance(node, _scopeTypes):
			continue
		yield node
		stack.extend(ast.iter_child_nodes(node))


def _nestedDefs(functionNode):
	return {node.name: node for node in ast.walk(functionNode) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not functionNode}


def _findFunctionNode(code):
	filename = code.co_filename
	try:
		tree = _parseFile(filename, os.path.getmtime(filename))
	except (OSError, SyntaxError):
		return None
	for node in ast.walk(tree):
		if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == code.co_name:
			if min([node.lineno] + [d.lineno for d in node.decorator_list]) == code.co_firstlineno:
				return node
	return None


@functools.lru_cache(maxsize=64)
def _parseFile(filename, modifiedTime):
	with open(filename, encoding='utf-8') as f:
		return ast.parse(f.read(), filename)
