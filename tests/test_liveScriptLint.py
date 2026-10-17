"""Live-script lint: a generator function called without `yield from` silently runs none of its commands."""
import ast
import os

import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(projectRoot, 'DCSAutoMateScripts')


def _containsYield(function):
	"""True if this function's own body yields (nested defs don't count)."""
	stack = list(function.body)
	while stack:
		node = stack.pop()
		if isinstance(node, (ast.Yield, ast.YieldFrom)):
			return True
		if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
			continue
		stack.extend(ast.iter_child_nodes(node))
	return False


def findUnconsumedGeneratorCalls(source):
	"""Return (line, name) for each call to a generator function that isn't `yield from name(...)`.

	Names are resolved per scope: a function's nested defs, then the module's top-level defs.
	"""
	tree = ast.parse(source)
	parents = {}
	for node in ast.walk(tree):
		for child in ast.iter_child_nodes(node):
			parents[child] = node

	def generatorNamesIn(body):
		return {n.name for n in body if isinstance(n, ast.FunctionDef) and _containsYield(n)}

	def enclosingScopes(node):
		while node in parents:
			node = parents[node]
			if isinstance(node, (ast.FunctionDef, ast.Module)):
				yield node

	problems = []
	for node in ast.walk(tree):
		if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
			continue
		for scope in enclosingScopes(node):
			if node.func.id in {n.name for n in scope.body if isinstance(n, ast.FunctionDef)}:
				if node.func.id in generatorNamesIn(scope.body) and not isinstance(parents.get(node), ast.YieldFrom):
					problems.append((node.lineno, node.func.id))
				break
	return problems


def test_flagsPlainCallToNestedGenerator():
	source = (
		'def ColdStart(config, vars, helper):\n'
		'\tdef checkHelmet():\n'
		'\t\tyield\n'
		'\tcheckHelmet()\n'
		'\tyield\n'
	)
	assert findUnconsumedGeneratorCalls(source) == [(4, 'checkHelmet')]


def test_acceptsYieldFrom():
	source = (
		'def ColdStart(config, vars, helper):\n'
		'\tdef checkHelmet():\n'
		'\t\tyield\n'
		'\tyield from checkHelmet()\n'
	)
	assert findUnconsumedGeneratorCalls(source) == []


def test_sameNameInAnotherFunctionIsResolvedSeparately():
	"""AH-64D defines setPltTsdShowOptions in two script functions; only the one that yields needs yield from."""
	source = (
		'def ColdStart(config, vars, helper):\n'
		'\tdef setShowOptions():\n'
		'\t\tpass\n'
		'\tsetShowOptions()\n'
		'def HotStart(config, vars, helper):\n'
		'\tdef setShowOptions():\n'
		'\t\tyield\n'
		'\tyield from setShowOptions()\n'
	)
	assert findUnconsumedGeneratorCalls(source) == []


def test_ordinaryNestedFunctionsAreFine():
	source = (
		'def ColdStart(config, vars, helper):\n'
		'\tdef pressButton(name):\n'
		'\t\treturn name\n'
		'\tpressButton("A")\n'
	)
	assert findUnconsumedGeneratorCalls(source) == []


@pytest.mark.parametrize('fileName', sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.py')))
def test_scriptsConsumeEveryGeneratorCall(fileName):
	with open(os.path.join(SCRIPTS_DIR, fileName), encoding='utf-8') as f:
		source = f.read()
	assert findUnconsumedGeneratorCalls(source) == [], 'call these with "yield from", or their commands never run'
