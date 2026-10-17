local isHookLogFileEnabled = false
local logFile = lfs.writedir() .. "Logs/DCSAutoMateHook.log"

local function resetLogFile()
	if not isHookLogFileEnabled then
		return
	end
	local f = io.open(logFile, "w")
	if f then
		f:write("")
		f:close()
	end
end

resetLogFile()

local function log(str)
	if not isHookLogFileEnabled then
		return
	end
	local f = io.open(logFile, "a")
	if f then
		f:write(os.date("%Y-%m-%d %H:%M:%S") .. ": " .. str .. "\n")
		f:close()
	end
end

local socket
local isDebugLoggingEnabled = false
local isUiWireLoggingEnabled = false

local monitorHotkeys = {
	"Ctrl+Shift+Z",
}

local function loadHookSettings()
	local settingsPath = lfs.writedir() .. "Scripts\\DCSAutoMate\\DCSAutoMateHookSettings.lua"
	local ok, result = pcall(dofile, settingsPath)
	if not ok or type(result) ~= 'table' then
		return
	end
	if type(result.hotkeys) == 'table' and #result.hotkeys > 0 then
		monitorHotkeys = result.hotkeys
	elseif type(result.hotkey) == 'string' and tostring(result.hotkey) ~= '' then
		monitorHotkeys = { tostring(result.hotkey) }
	end
	if type(result.isHookLogFileEnabled) == 'boolean' then
		isHookLogFileEnabled = result.isHookLogFileEnabled
	end
	if type(result.isDebugLoggingEnabled) == 'boolean' then
		isDebugLoggingEnabled = result.isDebugLoggingEnabled
	end
	if type(result.isUiWireLoggingEnabled) == 'boolean' then
		isUiWireLoggingEnabled = result.isUiWireLoggingEnabled
	end
	if type(result.uiRemoteControlPort) == 'number' then
		monitorUiTargetPort = result.uiRemoteControlPort
	end
	if type(result.uiRemoteControlReplyPort) == 'number' then
		monitorUiReplyPort = result.uiRemoteControlReplyPort
	end
end

pcall(loadHookSettings)

resetLogFile()
local monitorWindow = nil
local monitorTextBox = nil
local monitorModuleComboBox = nil
local monitorScriptComboBox = nil
local monitorVarsGrid = nil
local monitorVarsGridLabelTemplate = nil
local monitorVarsGridComboTemplate = nil
local monitorVarsGridEditBoxTemplate = nil
local monitorVarsGridValueCombosByVar = {}
local monitorVarsGridBackground = nil
local monitorSkin = nil
local monitorStartButton = nil
local monitorSkipWaitButton = nil
local monitorStopButton = nil
local monitorAutoSelectButton = nil
local monitorCopyOutputButton = nil
local monitorTestInputButton = nil
local monitorInputDialog = nil
local monitorInputTextBox = nil
local monitorInputOKButton = nil
local monitorInputCancelButton = nil
local monitorNotConnectedLabel = nil
local monitorConnected = false
local monitorModulesReceived = false
local monitorLastConnectionAttempt = 0
local updateMonitorUiState = nil
local monitorInput = nil
local monitorUiSender = nil
local monitorSendUiCommand = nil
local monitorUiTargetHost = "127.0.0.1"
local monitorUiTargetPort = 7786
local monitorUiReplyPort = 7779
local monitorPopulatingUi = false
local monitorSelectedModule = ""
local monitorSelectedScript = ""
local monitorScriptRunning = false
local monitorScriptPaused = false
local monitorIgnoreVarsGridChanges = false

local lockKeyboardInput = nil
local unlockKeyboardInput = nil

local appendMonitorText = nil
local monitorLines = {}
local monitorMaxLines = 50
local monitorLastText = ""

local monitorKeyboardLocked = false

-- monitorLayout: begin
-- Bounds {x, y, w, h} of every widget for a client area of clientW x clientH with varCount variable rows: controls stretch to the width, and the output box takes the rest of the height.
local function monitorLayout(clientW, clientH, varCount)
	local minWidth = 300
	local minOutputHeight = 100
	local varColumnWidth = 150
	local width = math.max(minWidth, math.floor(clientW))
	local gridY = 72
	local gridHeight = 20 + varCount * 24
	local buttonY = gridY + gridHeight + 12
	local buttonWidth = math.floor((width - 20 - 12) / 3)
	local skipWaitX = buttonWidth + 4
	local stopX = skipWaitX + buttonWidth + 4
	local copyX = stopX + buttonWidth + 4
	local outputY = buttonY + 20 + 12
	local outputHeight = math.max(minOutputHeight, math.floor(clientH) - outputY)
	return {
		autoSelect = {0, 0, width, 20},
		moduleCombo = {0, 24, width, 20},
		scriptCombo = {0, 48, width, 20},
		varsGrid = {0, gridY, width, gridHeight},
		varsGridBackground = {0, gridY, width, gridHeight},
		varColumnWidth = varColumnWidth,
		valueColumnWidth = width - varColumnWidth,
		startButton = {0, buttonY, buttonWidth, 20},
		skipWaitButton = {skipWaitX, buttonY, buttonWidth, 20},
		stopButton = {stopX, buttonY, buttonWidth, 20},
		copyButton = {copyX, buttonY, width - copyX, 20},
		outputText = {0, outputY, width, outputHeight},
		notConnected = {0, outputY, width, 20},
		background = {0, 0, width, outputY + outputHeight},
		minClientHeight = outputY + minOutputHeight,
	}
end
-- monitorLayout: end

-- Place every widget for the window's current size.  Runs on every resize (like DCS's own FileDialog) and after the variables change.
local function applyMonitorLayout()
	if not monitorWindow then
		return
	end
	local ok, err = pcall(function()
		local clientW, clientH = monitorWindow:getClientRectSize()
		local varCount = monitorVarsGrid and monitorVarsGrid:getRowCount() or 0
		local layout = monitorLayout(clientW, clientH, varCount)
		local widgets = {
			autoSelect = monitorAutoSelectButton,
			moduleCombo = monitorModuleComboBox,
			scriptCombo = monitorScriptComboBox,
			varsGrid = monitorVarsGrid,
			varsGridBackground = monitorVarsGridBackground,
			startButton = monitorStartButton,
			skipWaitButton = monitorSkipWaitButton,
			stopButton = monitorStopButton,
			copyButton = monitorCopyOutputButton,
			outputText = monitorTextBox,
			notConnected = monitorNotConnectedLabel,
			background = monitorBackgroundPanel,
		}
		for name, widget in pairs(widgets) do
			local bounds = layout[name]
			widget:setBounds(bounds[1], bounds[2], bounds[3], bounds[4])
		end
		if monitorVarsGrid then
			monitorVarsGrid:setColumnWidth(0, layout.varColumnWidth)
			monitorVarsGrid:setColumnWidth(1, layout.valueColumnWidth)
		end
		for _, valueWidget in pairs(monitorVarsGridValueCombosByVar) do
			local _, _, _, valueHeight = valueWidget:getBounds()
			valueWidget:setSize(layout.valueColumnWidth, valueHeight)
		end
	end)
	if not ok then
		log('Monitor layout failed: err=' .. tostring(err))
	end
end


local function populateVarsGrid(varNames, varLabels, varTypes)
	local okPopulate, errPopulate = pcall(function()
	if not monitorVarsGrid then
		log('VarsGrid populate skipped: grid widget is nil (DcsAutoMateVarsGrid not found)')
		return
	end
	if not monitorVarsGridLabelTemplate or not monitorVarsGridComboTemplate then
		log('VarsGrid populate skipped: templates missing')
		return
	end
	if not monitorSendUiCommand then
		log('VarsGrid populate skipped: monitorSendUiCommand not ready')
		return
	end

	monitorIgnoreVarsGridChanges = true
	pcall(function() monitorVarsGrid:removeAllRows() end)
	monitorVarsGridValueCombosByVar = {}

	local count = tostring(varNames and #varNames or 0)
	log('VarsGrid populate: vars=' .. count)

	local rowHeight = 24
	for i, varName in ipairs(varNames or {}) do
		local varLabelText = tostring(varName or '')
		if type(varLabels) == 'table' and varLabels[i] and tostring(varLabels[i]) ~= '' then
			varLabelText = tostring(varLabels[i])
		end
		local varType = 'dropdown'
		if type(varTypes) == 'table' and varTypes[i] and tostring(varTypes[i]) ~= '' then
			varType = tostring(varTypes[i])
		end

		local rowIndex = i - 1
		pcall(function() monitorVarsGrid:insertRow(rowHeight) end)
		pcall(function() monitorVarsGrid:setRowHeight(rowIndex, rowHeight) end)

		local label = nil
		local okLabel, labelResult = pcall(function() return monitorVarsGridLabelTemplate:clone() end)
		if okLabel then
			label = labelResult
		else
			log('VarsGrid label clone failed: err=' .. tostring(labelResult))
		end

		if label then
			pcall(function() label:setText(varLabelText) end)
			pcall(function() label:setVisible(true) end)
			pcall(function() monitorVarsGrid:setCell(0, rowIndex, label) end)
		end

		if varType == 'text' then
			local editBox = nil
			local okEdit, editResult = pcall(function() return monitorVarsGridEditBoxTemplate:clone() end)
			if okEdit then
				editBox = editResult
			else
				log('VarsGrid editBox clone failed: err=' .. tostring(editResult))
			end

			if editBox then
				editBox.dcsAutoMateVarName = tostring(varName or '')
				editBox.dcsAutoMateVarLabel = varLabelText
				pcall(function() editBox:setVisible(true) end)
				pcall(function() editBox:setEnabled(true) end)
				pcall(function() editBox:setText('') end)

				editBox:addFocusCallback(function(self)
					if self:getFocused() then
						lockKeyboardInput()
					else
						unlockKeyboardInput(true)
						local vName = tostring(self.dcsAutoMateVarName or '')
						local value = tostring(self:getText() or '')
						if vName ~= '' then
							appendMonitorText('Var: ' .. tostring(self.dcsAutoMateVarLabel or vName) .. ' = ' .. value)
							monitorSendUiCommand('varSelection', { module = monitorSelectedModule, script = monitorSelectedScript, var = vName, selectedValue = value })
						end
					end
				end)

				monitorVarsGridValueCombosByVar[tostring(varName or '')] = editBox
				pcall(function() monitorVarsGrid:setCell(1, rowIndex, editBox) end)
			end
		else
			local combo = nil
			local okCombo, comboResult = pcall(function() return monitorVarsGridComboTemplate:clone() end)
			if okCombo then
				combo = comboResult
			else
				log('VarsGrid combo clone failed: err=' .. tostring(comboResult))
			end

			if combo then
				combo.dcsAutoMateVarName = tostring(varName or '')
				combo.dcsAutoMateVarLabel = varLabelText
				combo.dcsAutoMateLabelToValue = {}
				combo.dcsAutoMateValueToItem = {}
				pcall(function() combo:setVisible(true) end)
				pcall(function() combo:setEnabled(true) end)
				pcall(function() combo:clear() end)
				pcall(function() local item = combo:newItem('(Loading...)'); combo:selectItem(item) end)

				combo.onChange = function(self)
					if monitorPopulatingUi or monitorIgnoreVarsGridChanges then
						return
					end
					local vName = tostring(self.dcsAutoMateVarName or '')
					local selectedLabel = tostring(self:getText() or '')
					if vName == '' or selectedLabel == '' then
						return
					end
					local valueKey = selectedLabel
					if self.dcsAutoMateLabelToValue and self.dcsAutoMateLabelToValue[selectedLabel] then
						valueKey = tostring(self.dcsAutoMateLabelToValue[selectedLabel])
					end
					appendMonitorText('Var: ' .. tostring(self.dcsAutoMateVarLabel or vName) .. ' = ' .. selectedLabel)
					monitorSendUiCommand('varSelection', { module = monitorSelectedModule, script = monitorSelectedScript, var = vName, selectedValue = valueKey })
				end

				monitorVarsGridValueCombosByVar[tostring(varName or '')] = combo
				pcall(function() monitorVarsGrid:setCell(1, rowIndex, combo) end)
			end
		end

		local okSend, errSend = pcall(function()
			monitorSendUiCommand('getVarOptions', { module = monitorSelectedModule, script = monitorSelectedScript, var = tostring(varName or '') })
		end)
		if not okSend then
			log('VarsGrid listVarValues failed: var=' .. tostring(varName or '') .. ' err=' .. tostring(errSend))
		end
	end

	-- Keep the size the player chose, but grow the window if the variables leave too little room for the output.
	if monitorWindow then
		local clientW, clientH = monitorWindow:getClientRectSize()
		local minClientHeight = monitorLayout(clientW, clientH, #(varNames or {})).minClientHeight
		if clientH < minClientHeight then
			local x, y, w, h = monitorWindow:getBounds()
			monitorWindow:setBounds(x, y, w, h + minClientHeight - clientH)
		end
	end
	applyMonitorLayout()

	end)
	monitorIgnoreVarsGridChanges = false
	if not okPopulate then
		log('VarsGrid populate failed: err=' .. tostring(errPopulate))
	end
end
local monitorIsHidden = true
local monitorLastText = nil
local monitorHasUiSupport = false
local monitorUiInitAttempted = false
local monitorUiError = nil
local monitorWindowDefaultSkin = nil
local monitorWindowSkinHidden = nil
local monitorLfs = nil
local monitorDialogLoader = nil
local monitorMaxLines = 50
local monitorLines = {}

local function parseMessageFields(msg)
	local fields = {}
	for part in string.gmatch(tostring(msg or ""), "[^;]+") do
		local key, value = string.match(part, "^([^=]+)=(.*)$")
		if key and value then
			fields[key] = value
		end
	end
	return fields
end

local function splitPipeList(value)
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

local function debugLog(str)
	if isDebugLoggingEnabled then
		log(str)
	end
end

local function truncateForLog(value, maxLen)
	local s = tostring(value or "")
	s = string.gsub(s, "\r", "\\r")
	s = string.gsub(s, "\n", "\\n")
	maxLen = tonumber(maxLen) or 400
	if #s > maxLen then
		return string.sub(s, 1, maxLen) .. "...(" .. tostring(#s) .. ")"
	end
	return s
end

local function sendUdpReply(replyPort, message)
	if not replyPort or not socket or not socket.udp then
		return false
	end

	local replySocket = socket.udp()
	replySocket:settimeout(0)
	local bytesOrNil, err = replySocket:sendto(tostring(message or ""), "127.0.0.1", replyPort)
	replySocket:close()

	if not bytesOrNil then
		log("UDP reply send failed: replyPort=" .. tostring(replyPort) .. " err=" .. tostring(err))
		return false
	end

	return true
end

local function sanitizeField(value)
	value = tostring(value or "")
	value = string.gsub(value, ";", ",")
	value = string.gsub(value, "\n", " ")
	value = string.gsub(value, "\r", " ")
	return value
end

local Terrain = nil

local function tryLoadTerrainModule()
	if Terrain ~= nil then
		return Terrain
	end
	if type(require) ~= "function" then
		Terrain = false
		return nil
	end
	local ok, mod = pcall(require, "terrain")
	if ok and mod then
		Terrain = mod
		return Terrain
	end
	Terrain = false
	return nil
end

local function splitWords(value)
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

local function parseMgrsText(mgrsText)
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

local function terrainGetGroundAltMeters(terrainModule, x, z)
	if not terrainModule then
		return 0
	end
	if terrainModule.GetSurfaceHeightWithSeabed then
		local ok, alt = pcall(terrainModule.GetSurfaceHeightWithSeabed, x, z)
		if ok and type(alt) == "number" then
			return alt
		end
	end
	if terrainModule.GetHeight then
		local ok, alt = pcall(terrainModule.GetHeight, x, z)
		if ok and type(alt) == "number" then
			return alt
		end
	end
	return 0
end

local function tryConvertCoordUsingTerrain(x, y, z)
	local terrainModule = tryLoadTerrainModule()
	if not terrainModule then
		return false, "terrain module unavailable"
	end

	local xNum = tonumber(x)
	local yNum = tonumber(y)
	local zNum = tonumber(z)
	if not xNum or not zNum then
		return false, "invalid x/z"
	end

	local groundAlt = terrainGetGroundAltMeters(terrainModule, xNum, zNum)
	if not yNum or yNum == 0 then
		yNum = groundAlt
	end

	if not terrainModule.convertMetersToLatLon then
		return false, "Terrain.convertMetersToLatLon unavailable"
	end

	local okLatLon, lat, lon = pcall(terrainModule.convertMetersToLatLon, xNum, zNum)
	if not okLatLon or type(lat) ~= "number" or type(lon) ~= "number" then
		return false, "Terrain.convertMetersToLatLon failed"
	end

	local mgrsText = ""
	if terrainModule.GetMGRScoordinates then
		local okMgrs, mgrsValue = pcall(terrainModule.GetMGRScoordinates, xNum, zNum)
		if okMgrs and mgrsValue then
			mgrsText = tostring(mgrsValue)
		end
	end

	local mgrsZone, mgrsDigraph, mgrsEasting, mgrsNorthing = parseMgrsText(mgrsText)

	mgrsText = sanitizeField(mgrsText)
	mgrsZone = sanitizeField(mgrsZone)
	mgrsDigraph = sanitizeField(mgrsDigraph)
	mgrsEasting = sanitizeField(mgrsEasting)
	mgrsNorthing = sanitizeField(mgrsNorthing)

	local responseText = string.format("ok=true;groundAlt=%.2f;lat=%.8f;lon=%.8f;mgrs=%s;mgrsZone=%s;mgrsDigraph=%s;mgrsEasting=%s;mgrsNorthing=%s;", groundAlt, lat, lon, mgrsText, mgrsZone, mgrsDigraph, mgrsEasting, mgrsNorthing)
	return true, responseText
end

local function buildMissionCoordConvertCode(x, y, z)
	return string.format([[
		local x = tonumber(%q)
		local y = tonumber(%q)
		local z = tonumber(%q)

		if (not coord or not coord.LOtoLL) and type(require) == "function" then
			local ok, mod = pcall(require, "coord")
			if ok and mod then
				coord = mod
			end
		end

		local groundAlt = 0
		if land and land.getHeight then
			groundAlt = land.getHeight({ x = x, y = z }) or 0
		end

		if not y or y == 0 then
			y = groundAlt
		end

		if not coord or not coord.LOtoLL then
			return "ok=false;error=coord.LOtoLL unavailable;hasRequire=" .. tostring(type(require)) .. ";hasCoord=" .. tostring(type(coord)) .. ";"
		end

		local lat, lon = coord.LOtoLL({ x = x, y = y, z = z })
		if not lat or not lon then
			return "ok=false;error=coord.LOtoLL failed;"
		end

		local mgrsText = ""
		local mgrsZone = ""
		local mgrsDigraph = ""
		local mgrsEasting = ""
		local mgrsNorthing = ""
		if coord and coord.LLtoMGRS then
			local mgrs = coord.LLtoMGRS(lat, lon)
			if type(mgrs) == "string" then
				mgrsText = mgrs
			elseif type(mgrs) == "table" then
				if mgrs.MGRS then
					mgrsText = mgrs.MGRS
				end
				-- DCS may vary key names by environment/version; keep a few safe fallbacks.
				mgrsZone = mgrs.UTMZone or mgrs.utmZone or mgrs.zone or mgrs.Zone or mgrs.zoneBand or ""
				mgrsDigraph = mgrs.Digraph or mgrs.digraph or mgrs.Digraphs or mgrs.MGRSDigraph or ""
				local e = tonumber(mgrs.Easting or mgrs.easting)
				local n = tonumber(mgrs.Northing or mgrs.northing)
				if e then
					mgrsEasting = tostring(math.floor(e + 0.5))
				end
				if n then
					mgrsNorthing = tostring(math.floor(n + 0.5))
				end

				local zoneNum = ""
				local zoneBand = ""
				if mgrsZone and mgrsZone ~= "" then
					zoneNum = string.match(tostring(mgrsZone), "^(%%d+)") or ""
					zoneBand = string.match(tostring(mgrsZone), "^%%d+(%%a)") or ""
				end
				if zoneNum ~= "" and zoneBand ~= "" and mgrsDigraph ~= "" and mgrsEasting ~= "" and mgrsNorthing ~= "" then
					mgrsText = zoneNum .. " " .. zoneBand .. " " .. tostring(mgrsDigraph) .. " " .. tostring(mgrsEasting) .. " " .. tostring(mgrsNorthing)
				end
			else
				mgrsText = tostring(mgrs or "")
			end
		end

		mgrsText = tostring(mgrsText or "")
		mgrsText = string.gsub(mgrsText, ";", ",")
		mgrsText = string.gsub(mgrsText, "\n", " ")
		mgrsText = string.gsub(mgrsText, "\r", " ")

		mgrsZone = tostring(mgrsZone or "")
		mgrsZone = string.gsub(mgrsZone, ";", ",")
		mgrsZone = string.gsub(mgrsZone, "\n", " ")
		mgrsZone = string.gsub(mgrsZone, "\r", " ")

		mgrsDigraph = tostring(mgrsDigraph or "")
		mgrsDigraph = string.gsub(mgrsDigraph, ";", ",")
		mgrsDigraph = string.gsub(mgrsDigraph, "\n", " ")
		mgrsDigraph = string.gsub(mgrsDigraph, "\r", " ")

		mgrsEasting = tostring(mgrsEasting or "")
		mgrsEasting = string.gsub(mgrsEasting, ";", ",")
		mgrsEasting = string.gsub(mgrsEasting, "\n", " ")
		mgrsEasting = string.gsub(mgrsEasting, "\r", " ")

		mgrsNorthing = tostring(mgrsNorthing or "")
		mgrsNorthing = string.gsub(mgrsNorthing, ";", ",")
		mgrsNorthing = string.gsub(mgrsNorthing, "\n", " ")
		mgrsNorthing = string.gsub(mgrsNorthing, "\r", " ")

		return string.format("ok=true;groundAlt=%%.2f;lat=%%.8f;lon=%%.8f;mgrs=%%s;mgrsZone=%%s;mgrsDigraph=%%s;mgrsEasting=%%s;mgrsNorthing=%%s;", groundAlt, lat, lon, mgrsText, mgrsZone, mgrsDigraph, mgrsEasting, mgrsNorthing)
	]], tostring(x), tostring(y), tostring(z))
end

local function tryHandleCoordConvertCommand(msg)
	local prefix = "DCSAUTOMATE_COORD_CONVERT;"
	if string.sub(msg, 1, #prefix) ~= prefix then
		return false
	end

	local args = {}
	for part in string.gmatch(msg, "[^;]+") do
		local key, value = string.match(part, "^([^=]+)=(.*)$")
		if key and value then
			args[key] = value
		end
	end

	local requestId = args.requestId or ""
	local replyPort = tonumber(args.replyPort)
	local x = args.x
	local y = args.y
	local z = args.z

	log("Coord convert request: requestId=" .. tostring(requestId) .. " replyPort=" .. tostring(replyPort) .. " x=" .. tostring(x) .. " y=" .. tostring(y) .. " z=" .. tostring(z))

	local terrainOk, terrainResponseOrError = tryConvertCoordUsingTerrain(x, y, z)
	if terrainOk then
		local envUsed = "hook"
		local replyMessage = "DCSAUTOMATE_COORD_CONVERT;requestId=" .. sanitizeField(requestId) .. ";env=" .. sanitizeField(envUsed) .. ";" .. tostring(terrainResponseOrError or "")
		log("Coord convert reply: requestId=" .. tostring(requestId) .. " env=" .. tostring(envUsed) .. " result=ok")
		debugLog("Coord convert reply (ok): replyPort=" .. tostring(replyPort) .. " bytes=" .. tostring(#replyMessage) .. " msg=" .. truncateForLog(replyMessage, 420))
		sendUdpReply(replyPort, replyMessage)
		return true
	end

	debugLog("Coord convert Terrain conversion unavailable/failed: " .. tostring(terrainResponseOrError))

	if not net or not net.dostring_in then
		log("Coord convert requested but net.dostring_in is not available")
		local combinedError = "Terrain conversion failed: " .. tostring(terrainResponseOrError) .. "; net.dostring_in not available"
		sendUdpReply(replyPort, "DCSAUTOMATE_COORD_CONVERT;requestId=" .. sanitizeField(requestId) .. ";ok=false;error=" .. sanitizeField(combinedError) .. ";")
		return true
	end

	local convertCode = buildMissionCoordConvertCode(x, y, z)
	debugLog("Coord convert mission code bytes=" .. tostring(#tostring(convertCode or "")) .. " preview=" .. truncateForLog(convertCode, 220))

	local function runInEnv(envName)
		local a1, a2 = net.dostring_in(envName, convertCode)
		debugLog("Coord convert dostring_in env=" .. tostring(envName) .. " returns: r1Type=" .. tostring(type(a1)) .. " r2Type=" .. tostring(type(a2)) .. " r1=" .. truncateForLog(a1, 260) .. " r2=" .. truncateForLog(a2, 260))
		return a1, a2
	end

	local envUsed = "mission"
	local r1, r2 = runInEnv("mission")

	local responseText = ""
	local errorText = nil

	if type(r1) == "boolean" then
		if r1 == true then
			responseText = tostring(r2 or "")
		else
			errorText = tostring(r2 or "Unknown error")
		end
	else
		responseText = tostring(r1 or "")
		if type(r2) == "string" and r2 ~= "" then
			errorText = r2
		end
	end

	if not errorText and string.find(responseText, "coord.LOtoLL unavailable", 1, true) then
		for _, envName in ipairs({ "server", "gui" }) do
			envUsed = envName
			r1, r2 = runInEnv(envName)

			responseText = ""
			errorText = nil
			if type(r1) == "boolean" then
				if r1 == true then
					responseText = tostring(r2 or "")
				else
					errorText = tostring(r2 or "Unknown error")
				end
			else
				responseText = tostring(r1 or "")
				if type(r2) == "string" and r2 ~= "" then
					errorText = r2
				end
			end

			if not errorText and string.find(responseText, "ok=true", 1, true) then
				break
			end
		end
	end

	if errorText then
		log("Coord convert error: " .. tostring(errorText))
		local replyMessage = "DCSAUTOMATE_COORD_CONVERT;requestId=" .. sanitizeField(requestId) .. ";ok=false;error=" .. sanitizeField(errorText) .. ";"
		debugLog("Coord convert reply (error): replyPort=" .. tostring(replyPort) .. " bytes=" .. tostring(#replyMessage) .. " msg=" .. truncateForLog(replyMessage, 420))
		sendUdpReply(replyPort, replyMessage)
		return true
	end

	local replyMessage = "DCSAUTOMATE_COORD_CONVERT;requestId=" .. sanitizeField(requestId) .. ";env=" .. sanitizeField(envUsed) .. ";" .. responseText
	local replyLabel = "ok"
	if string.find(responseText, "ok=false", 1, true) then
		replyLabel = "notOk"
	end
	log("Coord convert reply: requestId=" .. tostring(requestId) .. " env=" .. tostring(envUsed) .. " result=" .. tostring(replyLabel))
	debugLog("Coord convert reply (" .. replyLabel .. "): replyPort=" .. tostring(replyPort) .. " bytes=" .. tostring(#replyMessage) .. " msg=" .. truncateForLog(replyMessage, 420))
	sendUdpReply(replyPort, replyMessage)

	return true
end

log("DCSAutoMateHook loading...")

-- Setup paths to find LuaSocket
-- Assumes LuaSocket is in Saved Games\DCS\Scripts\LuaSocket
package.path = package.path .. ";.\\LuaSocket\\?.lua"
package.cpath = package.cpath .. ";.\\LuaSocket\\?.dll"
package.path = lfs.writedir() .. "Scripts\\?.lua;" .. package.path
package.path = lfs.writedir() .. "Scripts\\LuaSocket\\?.lua;" .. package.path
package.cpath = lfs.writedir() .. "Scripts\\LuaSocket\\?.dll;" .. package.cpath

local status
status, socket = pcall(require, "socket")
if not status then
	log("Error loading socket: " .. tostring(socket))
	-- Try to find where it might be looking
	log("package.path: " .. package.path)
	log("package.cpath: " .. package.cpath)
else
	log("Socket loaded successfully")
end

local msgListener = nil
if socket then
	msgListener = socket.udp()
	local success, err = msgListener:setsockname("*", monitorUiReplyPort)
	if not success then
		log("Error binding to port " .. tostring(monitorUiReplyPort) .. ": " .. tostring(err))
		msgListener:close()
		msgListener = nil
	else
		log("Listening on port " .. tostring(monitorUiReplyPort))
		msgListener:settimeout(0)
	end
end

	local function tryInitMonitorUi()
		if monitorUiInitAttempted then
			return monitorHasUiSupport
		end

		monitorUiInitAttempted = true

		local ok, errText = pcall(function()
			package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"
			monitorDialogLoader = require("DialogLoader")
			monitorSkin = require("Skin")
			monitorGui = require("dxgui")
			monitorLfs = require("lfs")
			monitorInput = require("Input")
			monitorListBoxItem = require("ListBoxItem")
			monitorWindowSkinHidden = monitorSkin.windowSkinChatMin()
		end)

		if not ok then
			monitorUiError = errText
			log("Monitor UI init failed: " .. tostring(errText))
			return false
		end


		monitorHasUiSupport = true
		return true
	end

	unlockKeyboardInput = function(releaseKeyboardKeys)
		if monitorKeyboardLocked then
			DCS.unlockKeyboardInput(releaseKeyboardKeys)
			monitorKeyboardLocked = false
		end
	end

	lockKeyboardInput = function()
		if monitorKeyboardLocked then
			return
		end
		local keyboardEvents = monitorInput.getDeviceKeys(monitorInput.getKeyboardDeviceName())
		DCS.lockKeyboardInput(keyboardEvents)
		monitorKeyboardLocked = true
	end

	appendMonitorText = function(text)
		text = tostring(text or "")
		if text == "" then
			return
		end

		for line in string.gmatch(text, "[^\r\n]+") do
			table.insert(monitorLines, line)
		end

		local maxLines = tonumber(monitorMaxLines) or 50
		while #monitorLines > maxLines do
			table.remove(monitorLines, 1)
		end

		local combined = table.concat(monitorLines, "\n")
		monitorLastText = combined
		if monitorTextBox then
			monitorTextBox:setText(combined)
			pcall(function()
				if monitorTextBox.getLineCount and monitorTextBox.setSelectionNew then
					local lineCount = tonumber(monitorTextBox:getLineCount()) or 0
					local lastLine = lineCount - 1
					if lastLine < 0 then
						lastLine = 0
					end
					monitorTextBox:setSelectionNew(lastLine, 0, lastLine, 0)
				elseif monitorTextBox.getLineCount and monitorTextBox.setSelection then
					local lineCount = tonumber(monitorTextBox:getLineCount()) or 0
					local lastLine = lineCount - 1
					if lastLine < 0 then
						lastLine = 0
					end
					monitorTextBox:setSelection(lastLine, 0, lastLine, 0)
				end
			end)
		end
	end

	local function createMonitorWindow()
		if monitorWindow or not tryInitMonitorUi() then
			return
		end

		local dlgPath = monitorLfs.writedir() .. "Scripts\\DCSAutoMate\\DCSAutoMateMonitorWindow.dlg"
		monitorWindow = monitorDialogLoader.spawnDialogFromFile(dlgPath)
		monitorWindowDefaultSkin = monitorWindow:getSkin()
		monitorBackgroundPanel = monitorWindow.DcsAutoMateBackground
		monitorTextBox = monitorWindow.DcsAutoMateMonitorText
		monitorModuleComboBox = monitorWindow.DcsAutoMateModuleCombo
		monitorScriptComboBox = monitorWindow.DcsAutoMateScriptCombo
		monitorVarsGrid = monitorWindow.DcsAutoMateVarsGrid
		monitorVarsGridBackground = monitorWindow.DcsAutoMateVarsGridBackground
		monitorVarsGridLabelTemplate = monitorWindow.DcsAutoMateVarsGridLabelTemplate
		monitorVarsGridComboTemplate = monitorWindow.DcsAutoMateVarsGridComboTemplate
		monitorVarsGridEditBoxTemplate = monitorWindow.DcsAutoMateVarsGridEditBoxTemplate
		monitorVarsGridValueCombosByVar = {}
		log('Monitor UI: DcsAutoMateVarsGrid is ' .. tostring(monitorVarsGrid))
		monitorStartButton = monitorWindow.DcsAutoMateStartButton
		monitorSkipWaitButton = monitorWindow.DcsAutoMateSkipWaitButton
		monitorStopButton = monitorWindow.DcsAutoMateStopButton
		monitorAutoSelectButton = monitorWindow.DcsAutoMateAutoSelectButton
		monitorCopyOutputButton = monitorWindow.DcsAutoMateCopyOutputButton
		monitorTestInputButton = monitorWindow.DcsAutoMateTestInputButton
		log('monitorTestInputButton is ' .. tostring(monitorTestInputButton))
		monitorNotConnectedLabel = monitorWindow.DcsAutoMateNotConnectedLabel

		if socket and socket.udp then
			monitorUiSender = socket.udp()
			monitorUiSender:settimeout(0)
		end

		local function sendUiCommand(command, fields)
			if not monitorUiSender then
				log("UI cmd send skipped: no sender; cmd=" .. tostring(command))
				return false
			end

			local parts = { "DCSAUTOMATE_UI", "cmd=" .. tostring(command or "") }
			if type(fields) == "table" then
				for key, value in pairs(fields) do
					table.insert(parts, tostring(key) .. "=" .. sanitizeField(value))
				end
			end
			local message = table.concat(parts, ";") .. ";"
			if isUiWireLoggingEnabled then
				log("UI wire TX: to=" .. tostring(monitorUiTargetHost) .. ":" .. tostring(monitorUiTargetPort) .. " bytes=" .. tostring(#tostring(message)) .. " msg=" .. truncateForLog(message, 900))
			end
			local ok, errText = monitorUiSender:sendto(message, monitorUiTargetHost, monitorUiTargetPort)
			if not ok then
				log("UI cmd send failed: cmd=" .. tostring(command) .. " err=" .. tostring(errText))
				return false
			end

			log("UI cmd sent: cmd=" .. tostring(command) .. " bytes=" .. tostring(#tostring(message)) .. " to=" .. tostring(monitorUiTargetHost) .. ":" .. tostring(monitorUiTargetPort))
			return true
		end

			monitorSendUiCommand = sendUiCommand

		updateMonitorUiState = function()
			if not monitorWindow or monitorIsHidden then return end

			local isConnected = monitorConnected

			if monitorNotConnectedLabel then monitorNotConnectedLabel:setVisible(not isConnected) end

			if monitorModuleComboBox then monitorModuleComboBox:setVisible(isConnected) end
			if monitorScriptComboBox then monitorScriptComboBox:setVisible(isConnected) end
			if monitorStartButton then monitorStartButton:setVisible(isConnected) end
			if monitorSkipWaitButton then monitorSkipWaitButton:setVisible(isConnected) end
			if monitorStopButton then monitorStopButton:setVisible(isConnected) end
			if monitorAutoSelectButton then monitorAutoSelectButton:setVisible(isConnected) end
			if monitorCopyOutputButton then monitorCopyOutputButton:setVisible(isConnected) end
			if monitorTestInputButton then monitorTestInputButton:setVisible(isConnected) end
			if monitorVarsGridBackground then monitorVarsGridBackground:setVisible(isConnected) end
			if monitorVarsGrid then monitorVarsGrid:setVisible(isConnected) end
			if monitorTextBox then monitorTextBox:setVisible(isConnected) end
		end

		local function toggleMonitor(hotkey)
			if monitorIsHidden then
				monitorWindow:setVisible(true)
				monitorWindow:setSkin(monitorWindowDefaultSkin)
				monitorWindow:setHasCursor(true)
				if monitorBackgroundPanel then
					monitorBackgroundPanel:setVisible(true)
				end

				monitorConnected = false
				monitorModulesReceived = false
				monitorLastConnectionAttempt = 0
				monitorIsHidden = false
				updateMonitorUiState()

				sendUiCommand("getModules")
			else
				monitorWindow:setSkin(monitorWindowSkinHidden)
				monitorWindow:setHasCursor(false)
				if monitorBackgroundPanel then
					monitorBackgroundPanel:setVisible(false)
				end
				if monitorModuleComboBox then
					monitorModuleComboBox:setVisible(false)
				end
				if monitorScriptComboBox then
					monitorScriptComboBox:setVisible(false)
				end
				if monitorStartButton then
					monitorStartButton:setVisible(false)
				end
				if monitorSkipWaitButton then
					monitorSkipWaitButton:setVisible(false)
				end
				if monitorStopButton then
					monitorStopButton:setVisible(false)
				end
				if monitorAutoSelectButton then
					monitorAutoSelectButton:setVisible(false)
				end
				if monitorCopyOutputButton then
					monitorCopyOutputButton:setVisible(false)
				end
				if monitorTestInputButton then
					monitorTestInputButton:setVisible(false)
				end
				if monitorVarsGridBackground then
					monitorVarsGridBackground:setVisible(false)
				end
				if monitorVarsGrid then
					monitorVarsGrid:setVisible(false)
				end
				if monitorTextBox then
					monitorTextBox:setVisible(false)
				end
				if monitorNotConnectedLabel then
					monitorNotConnectedLabel:setVisible(false)
				end
				monitorIsHidden = true
			end

			local x, y, w, h = monitorWindow:getBounds()
			log("Monitor hotkey fired: " .. tostring(hotkey) .. "; hidden=" .. tostring(monitorIsHidden) .. " bounds=" .. tostring(x) .. "," .. tostring(y) .. "," .. tostring(w) .. "," .. tostring(h))
		end

		for _, hotkey in ipairs(monitorHotkeys) do
			monitorWindow:addHotKeyCallback(
				hotkey,
				function()
					toggleMonitor(hotkey)
				end
			)
		end

		monitorWindow:setBounds(200, 200, 460, 380)
		pcall(function() monitorWindow:addSizeCallback(applyMonitorLayout) end)
		applyMonitorLayout()
		monitorWindow:setVisible(true)
		monitorWindow:setSkin(monitorWindowSkinHidden)
		monitorWindow:setHasCursor(false)
		if monitorBackgroundPanel then
			monitorBackgroundPanel:setVisible(false)
		end
		if monitorModuleComboBox then
			monitorModuleComboBox:setVisible(false)
		end
		if monitorScriptComboBox then
			monitorScriptComboBox:setVisible(false)
		end
		if monitorStartButton then
			monitorStartButton:setVisible(false)
		end
		if monitorSkipWaitButton then
			monitorSkipWaitButton:setVisible(false)
		end
		if monitorStopButton then
			monitorStopButton:setVisible(false)
		end
		if monitorAutoSelectButton then
			monitorAutoSelectButton:setVisible(false)
		end
		if monitorCopyOutputButton then
			monitorCopyOutputButton:setVisible(false)
		end
		if monitorTestInputButton then
			monitorTestInputButton:setVisible(false)
		end
		if monitorVarsGridBackground then
			monitorVarsGridBackground:setVisible(false)
		end
		if monitorVarsGrid then
			monitorVarsGrid:setVisible(false)
		end
		if monitorTextBox then
			monitorTextBox:setVisible(false)
		end
		if monitorNotConnectedLabel then
			monitorNotConnectedLabel:setVisible(false)
		end
		monitorIsHidden = true

		local function initUiCombos()
			monitorPopulatingUi = true
			if monitorModuleComboBox then
				monitorModuleComboBox:clear()
				local item = monitorModuleComboBox:newItem("(Loading modules...)")
				monitorModuleComboBox:selectItem(item)
			end
			if monitorScriptComboBox then
				monitorScriptComboBox:clear()
				local item = monitorScriptComboBox:newItem("(Select a module)")
				monitorScriptComboBox:selectItem(item)
			end
			if monitorVarsGrid then
				pcall(function() monitorVarsGrid:removeAllRows() end)
				monitorVarsGridValueCombosByVar = {}
			end
			monitorPopulatingUi = false
		end

		local ok, errText = pcall(initUiCombos)
		if not ok then
			log("Monitor UI init failed: " .. tostring(errText))
		end

		if monitorModuleComboBox then
			monitorModuleComboBox.onChange = function(self)
				if monitorPopulatingUi then
					return
				end
				local selectedModule = tostring(self:getText() or "")
				monitorSelectedModule = selectedModule
				appendMonitorText("Module: " .. selectedModule)
				sendUiCommand("valueChanged", { type = "module", value = selectedModule })
				sendUiCommand("getScripts", { module = selectedModule })
			end
		end

		if monitorScriptComboBox then
			monitorScriptComboBox.onChange = function(self)
				if monitorPopulatingUi then
					return
				end
				local selectedScript = tostring(self:getText() or "")
				monitorSelectedScript = selectedScript
				appendMonitorText("Script: " .. selectedScript)
				sendUiCommand("valueChanged", { type = "script", value = selectedScript })
				sendUiCommand("getVars", { module = monitorSelectedModule, script = selectedScript })
			end
		end

		if monitorStartButton then
			monitorStartButton.onChange = function()
				if not monitorScriptRunning then
					appendMonitorText("Run: Start")
					sendUiCommand("start")
				elseif not monitorScriptPaused then
					appendMonitorText("Run: Pause")
					sendUiCommand("pause")
				else
					appendMonitorText("Run: Resume")
					sendUiCommand("resume")
				end
			end
		end

		if monitorStopButton then
			monitorStopButton.onChange = function()
				appendMonitorText("Run: Stop")
				sendUiCommand("stop")
			end
		end

		if monitorSkipWaitButton then
			monitorSkipWaitButton.onChange = function()
				appendMonitorText("Run: Skip Wait")
				sendUiCommand("skipWait")
			end
		end

		if monitorCopyOutputButton then
			monitorCopyOutputButton.onChange = function()
				local text = tostring(monitorLastText or "")
				if monitorGui and monitorGui.CopyTextToClipboard then
					monitorGui.CopyTextToClipboard(text)
				end
			end
		end

		if monitorAutoSelectButton then
			monitorAutoSelectButton.onChange = function()
				if monitorSendUiCommand then
					monitorSendUiCommand('autoSelectTelemetry', {})
				end
			end
		end

		log("Monitor window created: " .. tostring(dlgPath) .. " hotkeys=" .. tostring(table.concat(monitorHotkeys, ", ")))
	end

local function tryHandleUiReplyMessage(msg)
	local prefix = "DCSAUTOMATE_UI;"
	if string.sub(tostring(msg or ""), 1, #prefix) ~= prefix then
		return false
	end

	if not monitorConnected then
		monitorConnected = true
		if updateMonitorUiState then
			updateMonitorUiState()
		end
	end

	local fields = parseMessageFields(msg)
	local event = tostring(fields.event or "")

	if event == "modulesList" and monitorModuleComboBox then
		monitorModulesReceived = true
		local items = splitPipeList(fields.items)
		local selectedName = tostring(fields.selected or "")
		monitorPopulatingUi = true
		monitorModuleComboBox:clear()
		local selectedItem = nil
		local firstItem = nil
		for _, name in ipairs(items) do
			local item = monitorModuleComboBox:newItem(name)
			if not firstItem then
				firstItem = item
			end
			if selectedName ~= "" and name == selectedName then
				selectedItem = item
			end
		end
		local itemToSelect = selectedItem or firstItem
		if itemToSelect then
			monitorModuleComboBox:selectItem(itemToSelect)
		end
		monitorSelectedModule = tostring(monitorModuleComboBox:getText() or "")
		monitorPopulatingUi = false

		-- Trigger next step
		if monitorSelectedModule ~= "" then
			monitorSendUiCommand("getScripts", { module = monitorSelectedModule })
		end
		return true

	elseif event == "scriptsList" and monitorScriptComboBox then
		local items = splitPipeList(fields.items)
		local selectedName = tostring(fields.selected or "")
		monitorPopulatingUi = true
		monitorScriptComboBox:clear()
		local selectedItem = nil
		local firstItem = nil
		for _, name in ipairs(items) do
			local item = monitorScriptComboBox:newItem(name)
			if not firstItem then
				firstItem = item
			end
			if selectedName ~= "" and name == selectedName then
				selectedItem = item
			end
		end
		local itemToSelect = selectedItem or firstItem
		if itemToSelect then
			monitorScriptComboBox:selectItem(itemToSelect)
		end
		monitorSelectedScript = tostring(monitorScriptComboBox:getText() or "")
		monitorPopulatingUi = false

		-- Trigger next step
		if monitorSelectedModule ~= "" and monitorSelectedScript ~= "" then
			monitorSendUiCommand("getVars", { module = monitorSelectedModule, script = monitorSelectedScript })
		end
		return true

	elseif event == "varsList" then
		local items = splitPipeList(fields.items)
		local labels = splitPipeList(fields.labels)
		local types = splitPipeList(fields.types)
		populateVarsGrid(items, labels, types)
		return true

	elseif event == "varOptions" then
		local varName = tostring(fields.var or "")
		local values = splitPipeList(fields.values)
		local labels = splitPipeList(fields.items) -- items are labels in the new protocol
		local selectedValue = tostring(fields.selected or "")

		if varName ~= "" and monitorVarsGridValueCombosByVar and monitorVarsGridValueCombosByVar[varName] then
			local combo = monitorVarsGridValueCombosByVar[varName]
			if combo.newItem then
				monitorIgnoreVarsGridChanges = true
				pcall(function() combo:clear() end)
				combo.dcsAutoMateLabelToValue = {}
				combo.dcsAutoMateValueToItem = {}

				local selectedItem = nil
				for index, label in ipairs(labels or {}) do
					local valueKey = tostring((values and values[index]) or label or "")
					local item = combo:newItem(tostring(label or ""))
					combo.dcsAutoMateLabelToValue[tostring(label or "")] = valueKey
					combo.dcsAutoMateValueToItem[valueKey] = item

					if selectedValue ~= "" and valueKey == selectedValue then
						selectedItem = item
					end
				end

				if selectedItem then
					combo:selectItem(selectedItem)
				elseif combo:getItemCount() > 0 then
					combo:selectItem(combo:getItem(0))
				end

				monitorIgnoreVarsGridChanges = false
			elseif combo.setText then
				if selectedValue ~= "" then
					monitorIgnoreVarsGridChanges = true
					pcall(function() combo:setText(selectedValue) end)
					monitorIgnoreVarsGridChanges = false
				end
			end
		end
		return true

	elseif event == "varSelection" then
		local varName = tostring(fields.var or "")
		local selectedValue = tostring(fields.selectedValue or "")

		if varName ~= "" and monitorVarsGridValueCombosByVar and monitorVarsGridValueCombosByVar[varName] then
			local combo = monitorVarsGridValueCombosByVar[varName]
			if combo.dcsAutoMateValueToItem and combo.dcsAutoMateValueToItem[selectedValue] then
				monitorIgnoreVarsGridChanges = true
				combo:selectItem(combo.dcsAutoMateValueToItem[selectedValue])
				monitorIgnoreVarsGridChanges = false
			elseif combo.setText then
				monitorIgnoreVarsGridChanges = true
				pcall(function() combo:setText(selectedValue) end)
				monitorIgnoreVarsGridChanges = false
			end
		end
		return true

	elseif event == "valueChanged" then
		local type = tostring(fields.type or "")
		local value = tostring(fields.value or "")

		if type == "module" and monitorModuleComboBox then
			-- Find item with this text
			local count = monitorModuleComboBox:getItemCount()
			for i = 0, count - 1 do
				local item = monitorModuleComboBox:getItem(i)
				if item and item:getText() == value then
					monitorPopulatingUi = true
					monitorModuleComboBox:selectItem(item)
					monitorSelectedModule = value
					monitorPopulatingUi = false

					-- Trigger update sequence
					monitorSendUiCommand("getScripts", { module = monitorSelectedModule })
					break
				end
			end
		elseif type == "script" and monitorScriptComboBox then
			-- Find item with this text
			local count = monitorScriptComboBox:getItemCount()
			for i = 0, count - 1 do
				local item = monitorScriptComboBox:getItem(i)
				if item and item:getText() == value then
					monitorPopulatingUi = true
					monitorScriptComboBox:selectItem(item)
					monitorSelectedScript = value
					monitorPopulatingUi = false

					-- Trigger update sequence
					if monitorSelectedModule ~= "" then
						monitorSendUiCommand("getVars", { module = monitorSelectedModule, script = monitorSelectedScript })
					end
					break
				end
			end
		end
		return true

	elseif event == "scriptState" then
		local running = tostring(fields.running or "") == "true"
		local paused = tostring(fields.paused or "") == "true"
		monitorScriptRunning = running
		monitorScriptPaused = paused

		if monitorModuleComboBox and monitorModuleComboBox.setEnabled then
			monitorModuleComboBox:setEnabled(not running)
		end
		if monitorScriptComboBox and monitorScriptComboBox.setEnabled then
			monitorScriptComboBox:setEnabled(not running)
		end
		if monitorAutoSelectButton and monitorAutoSelectButton.setEnabled then
			monitorAutoSelectButton:setEnabled(not running)
		end

		if monitorVarsGridValueCombosByVar then
			for _, combo in pairs(monitorVarsGridValueCombosByVar) do
				if combo.setEnabled then
					combo:setEnabled(not running)
				end
			end
		end

		if monitorStartButton and monitorStartButton.setEnabled then
			monitorStartButton:setEnabled(true) -- Always enabled if we can start/pause/resume
			if not running then
				monitorStartButton:setText("Start")
			elseif paused then
				monitorStartButton:setText("Resume")
			else
				monitorStartButton:setText("Pause")
			end
		end
		if monitorStopButton and monitorStopButton.setEnabled then
			monitorStopButton:setEnabled(running)
		end
		if monitorSkipWaitButton and monitorSkipWaitButton.setEnabled then
			monitorSkipWaitButton:setEnabled(running and tostring(fields.waiting or "") == "true")
		end

		return true

	elseif event == "log" then
		appendMonitorText(tostring(fields.text or ""))
		return true

	elseif event == "clear" then
		monitorLines = {}
		monitorLastText = ""
		if monitorTextBox then
			monitorTextBox:setText("")
		end
		return true

	elseif event == "highlight" then
		local elementName = tostring(fields.elementName or "")
		if elementName ~= "" and not string.find(elementName, '"') then
			local luaCode = string.format('a_cockpit_remove_highlight(1)\na_cockpit_highlight(1, "%s", 0, "")', elementName)
			local ok, err = pcall(function() net.dostring_in('mission', luaCode) end)
			if not ok then
				log("highlight failed: elementName=" .. elementName .. " err=" .. tostring(err))
			else
				log("highlight ok: elementName=" .. elementName)
			end
		else
			log("highlight skipped: empty or invalid elementName=" .. elementName)
		end
		return true

	elseif event == "highlightClear" then
		local ok, err = pcall(function() net.dostring_in('mission', 'a_cockpit_remove_highlight(1)') end)
		if not ok then
			log("highlightClear failed: " .. tostring(err))
		else
			log("highlightClear ok")
		end
		return true
	end

	return false
end

local dcsAutoMateHook = {}

-- Write DCS's own iCommand name -> number tables (the ones keybinding files are loaded with) to Logs/DCSAutoMateSimCommands.json.
local simCommandsExported = false
local function exportSimCommands()
	if simCommandsExported then
		return
	end
	simCommandsExported = true
	local ok, err = pcall(function()
		local input = require("Input")
		if type(input) ~= "table" or type(input.getEnvTable) ~= "function" then
			log("Sim command export: Input.getEnvTable is not available")
			return
		end
		local envTable = input.getEnvTable()
		if type(envTable) ~= "table" then
			log("Sim command export: Input.getEnvTable() returned " .. type(envTable))
			return
		end
		local sections = {}
		for sectionName, section in pairs(envTable) do
			if type(sectionName) == "string" and type(section) == "table" then
				local names = {}
				for name, value in pairs(section) do
					if type(name) == "string" and type(value) == "number" and name:match("^[%w_]+$") then
						names[#names + 1] = name
					end
				end
				table.sort(names)
				local lines = {}
				for _, name in ipairs(names) do
					lines[#lines + 1] = string.format('\t\t"%s": %s', name, tostring(section[name]))
				end
				sections[#sections + 1] = { name = sectionName, count = #names, text = string.format('\t"%s": {\n%s\n\t}', sectionName, table.concat(lines, ",\n")) }
			else
				log("Sim command export: skipping envTable." .. tostring(sectionName) .. " (" .. type(section) .. ")")
			end
		end
		table.sort(sections, function(a, b) return a.name < b.name end)
		local parts = {}
		for _, section in ipairs(sections) do
			parts[#parts + 1] = section.text
			log("Sim command export: envTable." .. section.name .. " has " .. tostring(section.count) .. " numeric entries")
		end
		local path = lfs.writedir() .. "Logs/DCSAutoMateSimCommands.json"
		local f = io.open(path, "w")
		if not f then
			log("Sim command export: could not open " .. path)
			return
		end
		f:write("{\n" .. table.concat(parts, ",\n") .. "\n}\n")
		f:close()
		log("Sim command export: wrote " .. path)
	end)
	if not ok then
		log("Sim command export failed: " .. tostring(err))
	end
end

function dcsAutoMateHook.onSimulationStart()
	exportSimCommands()
end

-- wireRxLabel: begin
-- Hook log label for a received message, or nil if wire logging doesn't cover it.
local function wireRxLabel(text)
	local uiPrefix = "DCSAUTOMATE_UI;"
	local coordPrefix = "DCSAUTOMATE_COORD_CONVERT;"
	if string.sub(text, 1, #uiPrefix) == uiPrefix then
		return "UI wire RX"
	elseif string.sub(text, 1, #coordPrefix) == coordPrefix then
		return "Coord wire RX"
	end
	return nil
end
-- wireRxLabel: end

function dcsAutoMateHook.onSimulationFrame()
	if not monitorWindow then
		local ok, errText = pcall(createMonitorWindow)
		if not ok then
			log("Monitor window creation failed: " .. tostring(errText))
		end
	end

	if monitorWindow and not monitorIsHidden then
		if not monitorConnected or not monitorModulesReceived then
			local now = os.clock()
			if now - monitorLastConnectionAttempt > 2 then
				monitorLastConnectionAttempt = now
				if monitorSendUiCommand then
					monitorSendUiCommand("getModules")
				end
			end
		end
	end

	if not msgListener then
		return
	end

	local msg, ip, port = msgListener:receivefrom()
	if msg then
		if isUiWireLoggingEnabled then
			local label = wireRxLabel(tostring(msg))
			if label then
				log(label .. ": from=" .. tostring(ip) .. ":" .. tostring(port) .. " bytes=" .. tostring(#tostring(msg)) .. " msg=" .. truncateForLog(msg, 900))
			end
		end
		if tryHandleCoordConvertCommand(msg) then
			return
		end
		if tryHandleUiReplyMessage(msg) then
			return
		end

		appendMonitorText(msg)
	end
end

DCS.setUserCallbacks(dcsAutoMateHook)
log("DCSAutoMateHook callbacks set")
