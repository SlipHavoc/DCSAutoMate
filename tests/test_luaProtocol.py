"""Lua-side tests using lupa (Lua-in-Python) via pytest.

Tests the pure-logic Lua functions extracted from DCSAutoMateExport.lua and
DCSAutoMateHook.lua.  These verify that the Lua serialization format matches
what the Python parsers expect (round-trip compatibility), and that the Hook's
message parsing helpers work correctly.
"""
import os
from types import SimpleNamespace
import sys

import pytest
from lupa import LuaRuntime

# Stub PySide6 so conftest imports work.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
sys.modules.setdefault('PySide6.QtWidgets', type(sys)('PySide6.QtWidgets'))

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def lua():
	"""Return a fresh LuaRuntime."""
	return LuaRuntime(unpack_returned_tuples=True)


@pytest.fixture
def tableToString(lua):
	"""Load the tableToString function from DCSAutoMateExport.lua."""
	lua.execute('''
		function tableToString(tbl, prefix)
			prefix = prefix or ""
			local str = ""
			for k, v in pairs(tbl) do
				local newKey = prefix .. (prefix ~= "" and "." or "") .. tostring(k)
				if type(v) == "table" then
					str = str .. tableToString(v, newKey)
				else
					str = str .. newKey .. "=" .. tostring(v) .. ";"
				end
			end
			return str
		end
	''')
	return lua.globals().tableToString


@pytest.fixture
def hookHelpers(lua):
	"""Load the pure helper functions from DCSAutoMateHook.lua."""
	lua.execute(r'''
		function parseMessageFields(msg)
			local fields = {}
			for part in string.gmatch(tostring(msg or ""), "[^;]+") do
				local key, value = string.match(part, "^([^=]+)=(.*)$")
				if key and value then
					fields[key] = value
				end
			end
			return fields
		end

		function splitPipeList(value)
			value = tostring(value or "")
			local items = {}
			if value == "" then
				return items
			end
			for item in string.gmatch(value, "[^|]+") do
				table.insert(items, item)
			end
			return items
		end

		function sanitizeField(value)
			value = tostring(value or "")
			value = string.gsub(value, ";", ",")
			value = string.gsub(value, "\n", " ")
			value = string.gsub(value, "\r", " ")
			return value
		end

		function splitWords(value)
			local items = {}
			local s = tostring(value or "")
			s = string.gsub(s, "\t", " ")
			s = string.gsub(s, "\r", " ")
			s = string.gsub(s, "\n", " ")
			s = string.gsub(s, " +", " ")
			s = string.gsub(s, "^ +", "")
			s = string.gsub(s, " +$", "")
			for part in string.gmatch(s, "[^ ]+") do
				table.insert(items, part)
			end
			return items
		end

		function parseMgrsText(mgrsText)
			local zone = ""
			local digraph = ""
			local easting = ""
			local northing = ""

			local parts = splitWords(mgrsText)
			if #parts == 0 then
				return zone, digraph, easting, northing
			end

			local i = 1
			local zoneToken = tostring(parts[i] or "")
			local nextToken = tostring(parts[i + 1] or "")
			if string.match(zoneToken, "^%d+$") and string.match(nextToken, "^[A-Za-z]$") then
				zone = zoneToken .. nextToken
				i = i + 2
			else
				zone = zoneToken
				i = i + 1
			end

			digraph = tostring(parts[i] or "")
			if digraph ~= "" then
				i = i + 1
			end

			local eastingToken = tostring(parts[i] or "")
			local northingToken = tostring(parts[i + 1] or "")
			if string.match(eastingToken, "^%d+$") and string.match(northingToken, "^%d+$") then
				easting = eastingToken
				northing = northingToken
				return zone, digraph, easting, northing
			end

			local combined = tostring(parts[i] or "")
			if string.match(combined, "^%d+$") and (#combined % 2 == 0) and #combined > 0 then
				local half = #combined / 2
				easting = string.sub(combined, 1, half)
				northing = string.sub(combined, half + 1)
			end

			return zone, digraph, easting, northing
		end

		function buildUiMessage(command, fields)
			local parts = { "DCSAUTOMATE_UI", "cmd=" .. tostring(command or "") }
			if type(fields) == "table" then
				for key, value in pairs(fields) do
					table.insert(parts, tostring(key) .. "=" .. sanitizeField(value))
				end
			end
			return table.concat(parts, ";") .. ";"
		end
	''')
	g = lua.globals()
	return {
		'parseMessageFields': g.parseMessageFields,
		'splitPipeList': g.splitPipeList,
		'sanitizeField': g.sanitizeField,
		'splitWords': g.splitWords,
		'parseMgrsText': g.parseMgrsText,
		'buildUiMessage': g.buildUiMessage,
	}


def luaTableToDict(luaTable):
	"""Convert a Lua table proxy to a Python dict."""
	result = {}
	for k, v in luaTable.items():
		result[k] = v
	return result


def luaTableToList(luaTable):
	"""Convert a Lua array-table proxy to a Python list."""
	result = []
	i = 1
	while True:
		val = luaTable[i]
		if val is None:
			break
		result.append(val)
		i += 1
	return result


# ---------------------------------------------------------------------------
# Tests: tableToString (export serialization format)
# ---------------------------------------------------------------------------

class TestTableToString:
	def test_flatTable(self, lua, tableToString):
		tbl = lua.table(altitude=1500, speed=250)
		result = tableToString(tbl)
		assert 'altitude=1500;' in result
		assert 'speed=250;' in result

	def test_nestedTable(self, lua, tableToString):
		inner = lua.table(left=80, right=85)
		tbl = lua.table(LoGetEngineInfo=inner)
		result = tableToString(tbl)
		assert 'LoGetEngineInfo.left=80;' in result
		assert 'LoGetEngineInfo.right=85;' in result

	def test_deeplyNestedTable(self, lua, tableToString):
		level2 = lua.table(count=0)
		level1 = lua.table(**{'1': level2})
		tbl = lua.table(Stations=level1)
		result = tableToString(tbl)
		assert 'Stations.1.count=0;' in result

	def test_emptyTable(self, lua, tableToString):
		tbl = lua.table()
		result = tableToString(tbl)
		assert result == ''

	def test_booleanValue(self, lua, tableToString):
		tbl = lua.table(active=True)
		result = tableToString(tbl)
		assert 'active=true;' in result

	def test_stringValue(self, lua, tableToString):
		tbl = lua.table(Name='FA-18C_hornet')
		result = tableToString(tbl)
		assert 'Name=FA-18C_hornet;' in result

	def test_endsWithSemicolon(self, lua, tableToString):
		tbl = lua.table(x=1)
		result = tableToString(tbl)
		assert result.endswith(';')


# ---------------------------------------------------------------------------
# Tests: round-trip (Lua tableToString → Python parseData)
# ---------------------------------------------------------------------------

class TestRoundTrip:
	def test_flatRoundTrip(self, lua, tableToString):
		from network.DCSAutoMateExportManager import DCSAutoMateExportManager
		mgr = DCSAutoMateExportManager.__new__(DCSAutoMateExportManager)

		tbl = lua.table(
			LoGetAltitudeAboveSeaLevel=1500.5,
			LoGetModelTime=300,
		)
		luaOutput = tableToString(tbl)
		parsed = mgr.parseData(luaOutput.encode('utf-8'))
		assert parsed['LoGetAltitudeAboveSeaLevel'] == 1500.5
		assert parsed['LoGetModelTime'] == 300

	def test_nestedRoundTrip(self, lua, tableToString):
		from network.DCSAutoMateExportManager import DCSAutoMateExportManager
		mgr = DCSAutoMateExportManager.__new__(DCSAutoMateExportManager)

		inner = lua.table(left=80, right=85)
		tbl = lua.table(LoGetEngineInfo=inner)
		luaOutput = tableToString(tbl)
		parsed = mgr.parseData(luaOutput.encode('utf-8'))
		assert parsed['LoGetEngineInfo']['left'] == 80
		assert parsed['LoGetEngineInfo']['right'] == 85

	def test_stringRoundTrip(self, lua, tableToString):
		from network.DCSAutoMateExportManager import DCSAutoMateExportManager
		mgr = DCSAutoMateExportManager.__new__(DCSAutoMateExportManager)

		inner = lua.table(Name='FA-18C_hornet')
		tbl = lua.table(LoGetSelfData=inner)
		luaOutput = tableToString(tbl)
		parsed = mgr.parseData(luaOutput.encode('utf-8'))
		assert parsed['LoGetSelfData']['Name'] == 'FA-18C_hornet'

	def test_boolRoundTrip(self, lua, tableToString):
		from network.DCSAutoMateExportManager import DCSAutoMateExportManager
		mgr = DCSAutoMateExportManager.__new__(DCSAutoMateExportManager)

		tbl = lua.table(active=True)
		luaOutput = tableToString(tbl)
		parsed = mgr.parseData(luaOutput.encode('utf-8'))
		assert parsed['active'] is True


# ---------------------------------------------------------------------------
# Tests: parseMessageFields
# ---------------------------------------------------------------------------

class TestParseMessageFields:
	def test_basicParsing(self, hookHelpers):
		result = luaTableToDict(hookHelpers['parseMessageFields']('cmd=getModules;module=F-16C;'))
		assert result['cmd'] == 'getModules'
		assert result['module'] == 'F-16C'

	def test_noTrailingSemicolon(self, hookHelpers):
		result = luaTableToDict(hookHelpers['parseMessageFields']('key=value'))
		assert result['key'] == 'value'

	def test_emptyString(self, hookHelpers):
		result = luaTableToDict(hookHelpers['parseMessageFields'](''))
		assert result == {}

	def test_valueWithEquals(self, hookHelpers):
		result = luaTableToDict(hookHelpers['parseMessageFields']('formula=a=b;'))
		assert result['formula'] == 'a=b'

	def test_noEqualsSkipped(self, hookHelpers):
		"""Tokens without '=' should be ignored."""
		result = luaTableToDict(hookHelpers['parseMessageFields']('DCSAUTOMATE_UI;cmd=test;'))
		assert 'cmd' in result
		assert 'DCSAUTOMATE_UI' not in result

	def test_uiProtocolMessage(self, hookHelpers):
		"""Verify parsing a real UI protocol message."""
		msg = 'DCSAUTOMATE_UI;cmd=scriptSelection;module=F-16C;script=Cold Start;'
		result = luaTableToDict(hookHelpers['parseMessageFields'](msg))
		assert result['cmd'] == 'scriptSelection'
		assert result['module'] == 'F-16C'
		assert result['script'] == 'Cold Start'


# ---------------------------------------------------------------------------
# Tests: splitPipeList
# ---------------------------------------------------------------------------

class TestSplitPipeList:
	def test_basicSplit(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitPipeList']('a|b|c'))
		assert result == ['a', 'b', 'c']

	def test_singleItem(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitPipeList']('only'))
		assert result == ['only']

	def test_emptyString(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitPipeList'](''))
		assert result == []


# ---------------------------------------------------------------------------
# Tests: sanitizeField
# ---------------------------------------------------------------------------

class TestSanitizeField:
	def test_removesSemicolons(self, hookHelpers):
		assert hookHelpers['sanitizeField']('hello;world') == 'hello,world'

	def test_removesNewlines(self, hookHelpers):
		assert hookHelpers['sanitizeField']('line1\nline2') == 'line1 line2'

	def test_removesCarriageReturns(self, hookHelpers):
		assert hookHelpers['sanitizeField']('line1\rline2') == 'line1 line2'

	def test_cleanStringUnchanged(self, hookHelpers):
		assert hookHelpers['sanitizeField']('normal text') == 'normal text'

	def test_combinedDangerousChars(self, hookHelpers):
		assert hookHelpers['sanitizeField']('a;b\nc\rd') == 'a,b c d'


# ---------------------------------------------------------------------------
# Tests: parseMgrsText
# ---------------------------------------------------------------------------

class TestParseMgrsText:
	def test_spaceSeparatedComponents(self, hookHelpers):
		zone, digraph, easting, northing = hookHelpers['parseMgrsText']('37T FJ 12345 67890')
		assert zone == '37T'
		assert digraph == 'FJ'
		assert easting == '12345'
		assert northing == '67890'

	def test_splitZoneAndBand(self, hookHelpers):
		"""When zone number and band letter are separate tokens."""
		zone, digraph, easting, northing = hookHelpers['parseMgrsText']('37 T FJ 12345 67890')
		assert zone == '37T'
		assert digraph == 'FJ'
		assert easting == '12345'
		assert northing == '67890'

	def test_combinedEastingNorthing(self, hookHelpers):
		"""When easting and northing are merged into one token."""
		zone, digraph, easting, northing = hookHelpers['parseMgrsText']('37T FJ 1234567890')
		assert zone == '37T'
		assert digraph == 'FJ'
		assert easting == '12345'
		assert northing == '67890'

	def test_emptyString(self, hookHelpers):
		zone, digraph, easting, northing = hookHelpers['parseMgrsText']('')
		assert zone == ''
		assert digraph == ''
		assert easting == ''
		assert northing == ''

	def test_sixDigitPrecision(self, hookHelpers):
		zone, digraph, easting, northing = hookHelpers['parseMgrsText']('37T FJ 123 678')
		assert easting == '123'
		assert northing == '678'


# ---------------------------------------------------------------------------
# Tests: buildUiMessage
# ---------------------------------------------------------------------------

class TestBuildUiMessage:
	def test_commandOnly(self, lua, hookHelpers):
		result = hookHelpers['buildUiMessage']('getModules', None)
		assert result.startswith('DCSAUTOMATE_UI;')
		assert 'cmd=getModules' in result
		assert result.endswith(';')

	def test_commandWithFields(self, lua, hookHelpers):
		fields = lua.table(module='F-16C', script='Cold Start')
		result = hookHelpers['buildUiMessage']('scriptSelection', fields)
		assert 'DCSAUTOMATE_UI;' in result
		assert 'cmd=scriptSelection' in result
		assert 'module=F-16C' in result
		assert 'script=Cold Start' in result

	def test_fieldsSanitized(self, lua, hookHelpers):
		fields = lua.table(text='line1;line2\nline3')
		result = hookHelpers['buildUiMessage']('log', fields)
		# Semicolons and newlines in values should be replaced.
		assert 'line1,line2 line3' in result

	def test_roundTripWithParseMessageFields(self, lua, hookHelpers):
		"""Build a UI message, then parse it back and verify the fields."""
		fields = lua.table(module='AH-64D', script='Cold Start')
		msg = hookHelpers['buildUiMessage']('scriptSelection', fields)
		parsed = luaTableToDict(hookHelpers['parseMessageFields'](msg))
		assert parsed['cmd'] == 'scriptSelection'
		assert parsed['module'] == 'AH-64D'
		assert parsed['script'] == 'Cold Start'


# ---------------------------------------------------------------------------
# Tests: splitWords
# ---------------------------------------------------------------------------

class TestSplitWords:
	def test_basicSplit(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitWords']('hello world'))
		assert result == ['hello', 'world']

	def test_multipleSpaces(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitWords']('  hello   world  '))
		assert result == ['hello', 'world']

	def test_tabsAndNewlines(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitWords']("hello\tworld\nfoo"))
		assert result == ['hello', 'world', 'foo']

	def test_emptyString(self, hookHelpers):
		result = luaTableToList(hookHelpers['splitWords'](''))
		assert result == []


# ---------------------------------------------------------------------------
# Tests: settings file structure
# ---------------------------------------------------------------------------

class TestSettingsFormat:
	def test_exportSettingsStructure(self, lua):
		"""DCSAutoMateExportSettings.lua must return a table with expected keys."""
		settingsPath = os.path.join(projectRoot, 'Scripts', 'DCSAutoMate', 'DCSAutoMateExportSettings.lua')
		result = lua.execute(open(settingsPath).read())
		assert result['udpPort'] == 6121
		assert result['tcpPort'] == 7780

	def test_hookSettingsStructure(self, lua):
		"""DCSAutoMateHookSettings.lua must return a table with expected keys."""
		settingsPath = os.path.join(projectRoot, 'Scripts', 'DCSAutoMate', 'DCSAutoMateHookSettings.lua')
		result = lua.execute(open(settingsPath).read())
		assert result['isHookLogFileEnabled'] == False
		assert result['isDebugLoggingEnabled'] == False
		hotkeys = luaTableToList(result['hotkeys'])
		assert len(hotkeys) > 0
		assert 'Ctrl+Shift+Z' in hotkeys


# ---------------------------------------------------------------------------
# Tests: sim command holds (H: messages)
# ---------------------------------------------------------------------------

@pytest.fixture
def simCommandHolds(lua):
	"""Load the simCommandHolds block from DCSAutoMateExport.lua with LoSetCommand recording its calls ('2004=0.7' when it has a value)."""
	exportPath = os.path.join(projectRoot, 'Scripts', 'DCSAutoMate', 'DCSAutoMateExport.lua')
	source = open(exportPath, encoding='utf-8').read()
	block = source.split('-- BEGIN simCommandHolds')[1].split('\n', 1)[1].split('-- END simCommandHolds')[0]
	lua.execute('sent = {}; function LoSetCommand(command, value) sent[#sent + 1] = value == nil and command or (command .. "=" .. value) end')
	start, update, release, releaseOwnedBy, parse = lua.execute(block + '\nreturn startSimCommandHold, updateSimCommandHolds, endSimCommandHold, releaseSimCommandHoldsOf, parseSimCommandHold')

	def takeSent():
		sent = luaTableToList(lua.globals().sent)
		lua.execute('sent = {}')
		return sent

	def parsed(line):
		hold = parse(line)
		return None if hold is None else {key: hold[key] for key in ('command', 'seconds', 'stop', 'value', 'release') if hold[key] is not None}
	return SimpleNamespace(start=start, update=update, release=release, releaseOwnedBy=releaseOwnedBy, parse=parsed, takeSent=takeSent)


class TestSimCommandHolds:
	def test_commandRepeatsEveryFrameThenStopIsSentOnce(self, simCommandHolds):
		start, update, takeSent = simCommandHolds.start, simCommandHolds.update, simCommandHolds.takeSent
		start(632, 2, 839, 10.0)
		assert takeSent() == [632]
		update(10.5)
		update(11.9)
		assert takeSent() == [632, 632]
		update(12.0)
		assert takeSent() == [839]
		update(12.5)
		assert takeSent() == []

	def test_holdWithoutStopJustEnds(self, simCommandHolds):
		start, update, takeSent = simCommandHolds.start, simCommandHolds.update, simCommandHolds.takeSent
		start(632, 1, None, 0.0)
		update(1.0)
		update(2.0)
		assert takeSent() == [632]

	def test_simultaneousHoldsEndIndependently(self, simCommandHolds):
		start, update, takeSent = simCommandHolds.start, simCommandHolds.update, simCommandHolds.takeSent
		start(632, 1, 839, 0.0)
		start(1033, 3, 1034, 0.0)
		takeSent()
		update(1.5)
		assert sorted(takeSent()) == [839, 1033]
		update(3.0)
		assert takeSent() == [1034]

	def test_valueIsSentEveryFrameUntilTheHoldEnds(self, simCommandHolds):
		h = simCommandHolds
		h.start(2004, 2, None, 10.0, 0.7)
		assert h.takeSent() == ['2004=0.7']
		h.update(10.5)
		h.update(11.9)
		assert h.takeSent() == ['2004=0.7', '2004=0.7']
		h.update(12.0)
		assert h.takeSent() == []

	def test_holdWithoutSecondsLastsUntilReleased(self, simCommandHolds):
		h = simCommandHolds
		h.start(2004, None, None, 0.0, -0.4)
		h.update(3600.0)
		assert h.takeSent() == ['2004=-0.4', '2004=-0.4']
		h.release(2004)
		h.update(3601.0)
		assert h.takeSent() == []

	def test_releaseSendsTheStopCommandOnce(self, simCommandHolds):
		h = simCommandHolds
		h.start(632, None, 839, 0.0)
		h.takeSent()
		h.release(632)
		h.release(632)
		assert h.takeSent() == [839]

	def test_releasingACommandThatIsNotHeldDoesNothing(self, simCommandHolds):
		simCommandHolds.release(2004)
		assert simCommandHolds.takeSent() == []

	def test_droppedConnectionReleasesOnlyItsOwnHolds(self, simCommandHolds):
		h = simCommandHolds
		h.start(2004, None, None, 0.0, 0.7, 'clientA')
		h.start(632, None, 839, 0.0, None, 'clientB')
		h.takeSent()
		h.releaseOwnedBy('clientA')
		h.update(1.0)
		assert h.takeSent() == [632]


@pytest.mark.parametrize('line, expected', [
	('H:632:2', {'command': 632, 'seconds': 2}),
	('H:632:2:839', {'command': 632, 'seconds': 2, 'stop': 839}),
	('H:2004:30::0.7', {'command': 2004, 'seconds': 30, 'value': 0.7}),
	('H:2004:0::-0.25', {'command': 2004, 'value': -0.25}), # 0 seconds: until released.
	('H:632:0:839:', {'command': 632, 'stop': 839}),
	('H:2004:release', {'command': 2004, 'release': True}),
	('H:2004', None),
	('H:x:2', None),
	('H:2004:-1', None),
	('H:2004:30:stop', None),
	('H:2004:30::half', None),
	('H:2004:30::0.7:extra', None),
])
def test_parseSimCommandHold(simCommandHolds, line, expected):
	assert simCommandHolds.parse(line) == expected
