---@diagnostic disable: undefined-global
-- DCSAutoMateExport.lua
-- Combined DCS export script for DCSAutoMate.
-- Handles both UDP telemetry broadcasting and TCP command/control.
--
-- Install: Add this line to your Saved Games/DCS/Scripts/Export.lua:
--   dofile(lfs.writedir()..[[Scripts\DCSAutoMate\DCSAutoMateExport.lua]])
--
-- UDP Telemetry (default port 6121, multicast 239.255.61.21):
--   Broadcasts flight data (airspeed, altitude, engine info, etc.) once per second.
--   Used by DCSAutoMate for module auto-detection and realtime data display.
--
-- TCP Command Protocol (default port 7780):
--   Commands (client -> DCS):
--     C:device:command:value     -- performClickableAction(command, value) on device
--     S:device:command:value     -- SetCommand(command, value) on device (for potentiometers/axes)
--     L:command[:value]          -- LoSetCommand(command[, value]) for simulator (iCommand) commands
--     H:command:seconds[:stop[:value]] -- Hold a simulator command: LoSetCommand(command[, value]) every frame for seconds (0 = until released), then LoSetCommand(stop)
--     H:command:release          -- End that hold now (sending its stop command); a client's holds also end when it disconnects
--     G:functionName             -- Call a LoGet* function (e.g. LoGetEngineInfo), reply G:functionName:json
--     Q:device:arg               -- Query get_argument_value(arg) on device (on-demand)
--     W:device:arg:interval      -- Subscribe to arg updates (interval in seconds, e.g. 0.1)
--     X:device:arg               -- Unsubscribe from arg updates
--     T:indicatorId              -- Query list_indication(indicatorId) for display text
--     E                          -- Query LoGetEngineInfo()
--     I                          -- Query module identification (LoGetSelfData().Name)
--     BULKQ:[arg1,arg2,...]      -- Query a JSON array of arg numbers in one round-trip
--     BULKQ:scan:N               -- Scan all args 0..N and return all values
--
--   Responses (DCS -> client):
--     R:device:arg:value          -- Response to Q query
--     U:device:arg:value          -- Subscription update
--     D:indicatorId:jsonText      -- Display text response
--     E:jsonEngineData            -- Engine data response
--     I:moduleName                -- Module identification response
--     BULKR:jsonObject            -- Response to BULKQ ({"argNum":value,...})
--     OK                          -- Command acknowledged
--     ERR:message                 -- Error response


-- ---------------------------------------------------------------------------
-- Package paths
-- ---------------------------------------------------------------------------

package.path = package.path .. ";.\\LuaSocket\\?.lua"
package.cpath = package.cpath .. ";.\\LuaSocket\\?.dll"
package.path = package.path .. ";" .. lfs.currentdir() .. "/LuaSocket/?.lua"
package.cpath = package.cpath .. ";" .. lfs.currentdir() .. "/LuaSocket/?.dll"
package.path = lfs.writedir() .. "?.lua;" .. package.path


-- ---------------------------------------------------------------------------
-- Logging (writes to Saved Games/DCS/Logs/DCSAutoMateExport.log)
-- ---------------------------------------------------------------------------

local logFile = lfs.writedir() .. "Logs/DCSAutoMateExport.log"

local function resetLogFile()
	local f = io.open(logFile, "w")
	if f then
		f:write("")
		f:close()
	end
end

resetLogFile()

local function logToFile(str)
	local f = io.open(logFile, "a")
	if f then
		f:write(os.date("%Y-%m-%d %H:%M:%S") .. ": " .. tostring(str or "") .. "\n")
		f:close()
	end
end


-- ---------------------------------------------------------------------------
-- Settings
-- ---------------------------------------------------------------------------

local udpPort = 6121
local udpMulticastGroup = "239.255.61.21"
local tcpPort = 7780

local function loadExportSettings()
	local settingsPath = lfs.writedir() .. "Scripts\\DCSAutoMate\\DCSAutoMateExportSettings.lua"
	local ok, result = pcall(dofile, settingsPath)
	if not ok or type(result) ~= 'table' then
		logToFile("Failed to load export settings: " .. tostring(ok) .. ", " .. tostring(result))
		return
	end
	if type(result.udpPort) == 'number' then
		udpPort = result.udpPort
	end
	if type(result.tcpPort) == 'number' then
		tcpPort = result.tcpPort
	end
	-- Support legacy setting names.
	if type(result.dcsAutoMateUdpPort) == 'number' then
		udpPort = result.dcsAutoMateUdpPort
	end
end

pcall(loadExportSettings)


-- ---------------------------------------------------------------------------
-- Shared dependencies
-- ---------------------------------------------------------------------------

local socket = require("socket")
local JSON = loadfile("Scripts/JSON.lua")()

logToFile("DCSAutoMateExport loading...")


-- ===========================================================================
-- UDP Telemetry Sender
-- ===========================================================================

local UDPMulticastSender = {}
UDPMulticastSender.__index = UDPMulticastSender

function UDPMulticastSender:new(multicastGroup, port)
	local self = setmetatable({}, UDPMulticastSender)
	self.multicastGroup = multicastGroup
	self.port = port
	self.udp = socket.udp()
	self.udp:setpeername(multicastGroup, port)
	self.udp:setoption("ip-multicast-ttl", 1)
	return self
end

function UDPMulticastSender:sendData(data)
	self.udp:send(data)
end

function UDPMulticastSender:close()
	if self.udp then
		self.udp:close()
	end
end

local udpSender = UDPMulticastSender:new(udpMulticastGroup, udpPort)

local function tableToString(tbl, prefix)
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

local function sendTelemetry()
	local telemetryData = {
		LoGetIndicatedAirSpeed = LoGetIndicatedAirSpeed(), -- m/s
		LoGetVerticalVelocity = LoGetVerticalVelocity(),
		LoGetTrueAirSpeed = LoGetTrueAirSpeed(), -- m/s
		LoGetAltitudeAboveSeaLevel = LoGetAltitudeAboveSeaLevel(),
		LoGetAltitudeAboveGroundLevel = LoGetAltitudeAboveGroundLevel(),
		LoGetMachNumber = LoGetMachNumber(),
		LoGetRadarAltimeter = LoGetRadarAltimeter(),
		LoGetEngineInfo = LoGetEngineInfo(),
		LoGetSelfData = LoGetSelfData(),
		LoGetPayloadInfo = LoGetPayloadInfo(),
		LoGetMechInfo = LoGetMechInfo(),
		LoGetHeightWithObjects = LoGetHeightWithObjects(),
		LoGetFMData = LoGetFMData(),
		LoGetPilotName = LoGetPilotName(),
		LoGetVersionInfo = LoGetVersionInfo(),
		LoGetModelTime = LoGetModelTime(),
		LoGetMissionStartTime = LoGetMissionStartTime(),
	}
	local dataString = tableToString(telemetryData)
	udpSender:sendData(dataString)
end


-- ===========================================================================
-- TCP Command Server
-- ===========================================================================

local cmdServer = nil
local clients = {}
local subscriptions = {} -- {key = "device:arg", device = N, arg = N, interval = N, lastSent = N, clients = {}}

-- Safe wrapper for pcall on DCS API functions.
local function safeCall(fn, ...)
	local status, result = pcall(fn, ...)
	if status then
		return result
	else
		return nil
	end
end

-- Encode a value as a simple JSON-ish string for responses.
local function encodeValue(val)
	if val == nil then
		return "null"
	elseif type(val) == "table" then
		return JSON:encode(val)
	elseif type(val) == "string" then
		return JSON:encode(val)
	else
		return tostring(val)
	end
end

-- Send a message to a specific client socket.
local function sendToClient(client, msg)
	local success, err = client:send(msg .. "\n")
	if not success then
		return false
	end
	return true
end

-- BEGIN simCommandHolds (tests/test_luaProtocol.py loads this block)
local simCommandHolds = {}

local function sendSimCommand(command, value)
	if value == nil then
		LoSetCommand(command)
	else
		LoSetCommand(command, value)
	end
end

-- Holding a key repeats its command every frame; the stop command is its key-up.  An axis held at a value overrides the player's own axis, which DCS only reads when it moves.
-- seconds nil = until released.  owner is the TCP client, so a dropped connection releases its holds.
local function startSimCommandHold(command, seconds, stopCommand, now, value, owner)
	sendSimCommand(command, value)
	simCommandHolds[command] = { endTime = seconds and now + seconds or nil, stopCommand = stopCommand, value = value, owner = owner }
end

local function endSimCommandHold(command)
	local hold = simCommandHolds[command]
	if not hold then
		return
	end
	simCommandHolds[command] = nil
	if hold.stopCommand then
		LoSetCommand(hold.stopCommand)
	end
end

local function releaseSimCommandHoldsOf(owner)
	for command, hold in pairs(simCommandHolds) do
		if hold.owner == owner then
			endSimCommandHold(command)
		end
	end
end

local function updateSimCommandHolds(now)
	for command, hold in pairs(simCommandHolds) do
		if hold.endTime and now >= hold.endTime then
			endSimCommandHold(command)
		else
			sendSimCommand(command, hold.value)
		end
	end
end

-- "H:command:seconds[:stop[:value]]" (0 seconds = until released) or "H:command:release" -> {command, seconds, stop, value} or {command, release = true}; nil if malformed.
local function parseSimCommandHold(line)
	local fields = {}
	for field in (line .. ":"):gmatch("([^:]*):") do
		fields[#fields + 1] = field
	end
	local command = fields[2] and fields[2]:match("^%d+$") and tonumber(fields[2])
	if fields[1] ~= "H" or not command or #fields < 3 or #fields > 5 then
		return nil
	end
	if fields[3] == "release" then
		return #fields == 3 and { command = command, release = true } or nil
	end
	local seconds = fields[3]:match("^[%d%.]+$") and tonumber(fields[3])
	local stopText, valueText = fields[4] or "", fields[5] or ""
	local stop = stopText ~= "" and stopText:match("^%d+$") and tonumber(stopText)
	local value = valueText ~= "" and tonumber(valueText)
	if not seconds or (stopText ~= "" and not stop) or (valueText ~= "" and not value) then
		return nil
	end
	return { command = command, seconds = seconds > 0 and seconds or nil, stop = stop or nil, value = value or nil }
end
-- END simCommandHolds

-- Process a single command line from a client.
local function processCommand(client, line)
	-- Strip trailing whitespace/CR.
	line = line:gsub("%s+$", "")

	if line == "" then
		return
	end

	local prefix = line:sub(1, 1)

	-- C:device:command:value -- performClickableAction
	if prefix == "C" then
		local dev, cmd, val = line:match("^C:(%d+):(%d+):([%d%.%-%+]+)$")
		if dev and cmd and val then
			local device = GetDevice(tonumber(dev))
			if device then
				local ok, err = pcall(function() device:performClickableAction(tonumber(cmd), tonumber(val)) end)
				if ok then
					sendToClient(client, "OK")
				else
					sendToClient(client, "ERR:performClickableAction failed: " .. tostring(err))
				end
			else
				sendToClient(client, "ERR:invalid device " .. dev)
			end
		else
			sendToClient(client, "ERR:bad C format")
		end
		return
	end

	-- S:device:command:value[:arg] -- SetCommand (+ optional set_argument_value on device 0)
	-- The optional :arg field is needed for defineSetCommandTumb controls (e.g. ILS frequency
	-- knobs) where SetCommand alone does not move the cockpit arg; set_argument_value on
	-- device 0 (MAIN_PANEL) must also be called, exactly as DCS BIOS does internally.
	if prefix == "S" then
		local dev, cmd, val, arg = line:match("^S:(%d+):(%d+):([%d%.%-%+]+):?(%d*)$")
		if dev and cmd and val then
			local device = GetDevice(tonumber(dev))
			if device then
				local ok, err = pcall(function()
					device:SetCommand(tonumber(cmd), tonumber(val))
					if arg ~= "" then
						GetDevice(0):set_argument_value(tonumber(arg), tonumber(val))
					end
				end)
				if ok then
					sendToClient(client, "OK")
				else
					sendToClient(client, "ERR:SetCommand failed: " .. tostring(err))
				end
			else
				sendToClient(client, "ERR:invalid device " .. dev)
			end
		else
			sendToClient(client, "ERR:bad S format")
		end
		return
	end

	-- Q:device:arg -- on-demand query
	-- Note: cockpit argument values are always read from device 0 (mainpanel),
	-- regardless of which device owns the command. The device parameter is kept
	-- in the protocol for clarity but is not used for the read.
	if prefix == "Q" then
		local dev, arg = line:match("^Q:(%d+):(%d+)$")
		if dev and arg then
			local mainpanel = GetDevice(0)
			if mainpanel then
				local ok, val = pcall(function() return mainpanel:get_argument_value(tonumber(arg)) end)
				if ok then
					sendToClient(client, "R:" .. dev .. ":" .. arg .. ":" .. tostring(val))
				else
					sendToClient(client, "ERR:get_argument_value failed for arg " .. arg)
				end
			else
				sendToClient(client, "ERR:mainpanel not available")
			end
		else
			sendToClient(client, "ERR:bad Q format")
		end
		return
	end

	-- W:device:arg:interval -- subscribe to arg updates
	if prefix == "W" then
		local dev, arg, interval = line:match("^W:(%d+):(%d+):([%d%.]+)$")
		if dev and arg and interval then
			local key = dev .. ":" .. arg
			if not subscriptions[key] then
				subscriptions[key] = {
					device = tonumber(dev),
					arg = tonumber(arg),
					interval = tonumber(interval),
					lastSent = 0,
					clients = {},
				}
			end
			subscriptions[key].clients[client] = true
			subscriptions[key].interval = tonumber(interval)
			sendToClient(client, "OK")
		else
			sendToClient(client, "ERR:bad W format")
		end
		return
	end

	-- X:device:arg -- unsubscribe
	if prefix == "X" then
		local dev, arg = line:match("^X:(%d+):(%d+)$")
		if dev and arg then
			local key = dev .. ":" .. arg
			if subscriptions[key] then
				subscriptions[key].clients[client] = nil
				-- Clean up if no more subscribers.
				local hasClients = false
				for _ in pairs(subscriptions[key].clients) do
					hasClients = true
					break
				end
				if not hasClients then
					subscriptions[key] = nil
				end
			end
			sendToClient(client, "OK")
		else
			sendToClient(client, "ERR:bad X format")
		end
		return
	end

	-- T:indicatorId -- query display text
	if prefix == "T" then
		local id = line:match("^T:(%d+)$")
		if id then
			local text = safeCall(list_indication, tonumber(id))
			if text then
				sendToClient(client, "D:" .. id .. ":" .. encodeValue(text))
			else
				sendToClient(client, "D:" .. id .. ":null")
			end
		else
			sendToClient(client, "ERR:bad T format")
		end
		return
	end

	-- G:functionName -- call a LoGet* export function (no arguments) and return its result as JSON.
	-- Response: G:functionName:json (null if the function failed or returned nothing)
	if prefix == "G" then
		local name = line:match("^G:(LoGet%w+)$")
		local fn = name and _G[name]
		if type(fn) == "function" then
			local ok, result = pcall(fn)
			sendToClient(client, "G:" .. name .. ":" .. (ok and encodeValue(result) or "null"))
		else
			sendToClient(client, "ERR:bad G function " .. tostring(name or line))
		end
		return
	end

	-- L:command[:value] -- LoSetCommand, for simulator (iCommand) commands that have no cockpit device
	if prefix == "L" then
		local cmd, val = line:match("^L:(%d+):?([%d%.%-%+]*)$")
		if cmd then
			local ok, err = pcall(function()
				if val ~= "" then
					LoSetCommand(tonumber(cmd), tonumber(val))
				else
					LoSetCommand(tonumber(cmd))
				end
			end)
			if ok then
				sendToClient(client, "OK")
			else
				sendToClient(client, "ERR:LoSetCommand failed: " .. tostring(err))
			end
		else
			sendToClient(client, "ERR:bad L format")
		end
		return
	end

	-- H:command:seconds[:stop[:value]] -- LoSetCommand(command[, value]) every frame for seconds (sim time; 0 = until released), then LoSetCommand(stop)
	-- H:command:release                -- end that hold now (sending its stop command)
	if prefix == "H" then
		local hold = parseSimCommandHold(line)
		if hold then
			local ok, err = pcall(function()
				if hold.release then
					endSimCommandHold(hold.command)
				else
					startSimCommandHold(hold.command, hold.seconds, hold.stop, LoGetModelTime(), hold.value, client)
				end
			end)
			if ok then
				sendToClient(client, "OK")
			else
				sendToClient(client, "ERR:LoSetCommand hold failed: " .. tostring(err))
			end
		else
			sendToClient(client, "ERR:bad H format")
		end
		return
	end

	-- E -- query engine info
	if prefix == "E" and line == "E" then
		local info = safeCall(LoGetEngineInfo)
		if info then
			sendToClient(client, "E:" .. encodeValue(info))
		else
			sendToClient(client, "E:null")
		end
		return
	end

	-- I -- query module identification
	if prefix == "I" and line == "I" then
		local selfData = safeCall(LoGetSelfData)
		if selfData and selfData.Name then
			sendToClient(client, "I:" .. selfData.Name)
		else
			sendToClient(client, "I:unknown")
		end
		return
	end

	-- BULKQ:[json_array] -- bulk query a list of arg numbers in one round-trip.
	-- BULKQ:scan:N       -- scan all args 0..N and return all values.
	-- Response: BULKR:{"argNum":value,...}
	-- Calls update_arguments() first to flush fresh values from the DCS engine
		if prefix == "B" and line:sub(1, 6) == "BULKQ:" then
		local mainpanel = GetDevice(0)
		if not mainpanel then
			sendToClient(client, "ERR:mainpanel not available")
			return
		end
		-- Flush fresh argument values from the DCS engine before reading.
		pcall(function() mainpanel:update_arguments() end)

		local results = {}

		-- BULKQ:scan:N — scan args 0..N.
		local maxArg = line:match("^BULKQ:scan:(%d+)$")
		if maxArg then
			maxArg = tonumber(maxArg)
			for arg = 0, maxArg do
				local ok, val = pcall(function() return mainpanel:get_argument_value(arg) end)
				if ok then
					results[tostring(arg)] = val
				end
			end
			sendToClient(client, "BULKR:" .. JSON:encode(results))
			return
		end

		-- BULKQ:[json_array] — targeted query for specific arg numbers.
		local jsonStr = line:match("^BULKQ:(%[.*)$")
		if jsonStr then
			local ok, argList = pcall(function() return JSON:decode(jsonStr) end)
			if not ok or type(argList) ~= "table" then
				sendToClient(client, "ERR:BULKQ bad JSON")
				return
			end
			for _, arg in ipairs(argList) do
				local argNum = tonumber(arg)
				if argNum then
					local getOk, val = pcall(function() return mainpanel:get_argument_value(argNum) end)
					if getOk then
						results[tostring(argNum)] = val
					end
				end
			end
			sendToClient(client, "BULKR:" .. JSON:encode(results))
			return
		end

		sendToClient(client, "ERR:bad BULKQ format")
		return
	end

	sendToClient(client, "ERR:unknown command")
end

-- Process subscription updates.
local function processSubscriptions(t)
	local mainpanel = GetDevice(0)
	if not mainpanel then return end

	for key, sub in pairs(subscriptions) do
		if t - sub.lastSent >= sub.interval then
			local ok, val = pcall(function() return mainpanel:get_argument_value(sub.arg) end)
			if ok then
				local msg = "U:" .. sub.device .. ":" .. sub.arg .. ":" .. tostring(val)
				local deadClients = {}
				for client, _ in pairs(sub.clients) do
					if not sendToClient(client, msg) then
						deadClients[#deadClients + 1] = client
					end
				end
				-- Remove dead clients.
				for _, client in ipairs(deadClients) do
					sub.clients[client] = nil
				end
			end
			sub.lastSent = t
		end
	end

	-- Clean up subscriptions with no clients.
	local emptyKeys = {}
	for key, sub in pairs(subscriptions) do
		local hasClients = false
		for _ in pairs(sub.clients) do
			hasClients = true
			break
		end
		if not hasClients then
			emptyKeys[#emptyKeys + 1] = key
		end
	end
	for _, key in ipairs(emptyKeys) do
		subscriptions[key] = nil
	end
end

-- Accept new TCP connections and process incoming commands (called every frame).
local function processTcpClients()
	if not cmdServer then return end

	-- Accept new connections.
	local newClient = cmdServer:accept()
	while newClient do
		newClient:settimeout(0)
		clients[newClient] = { buffer = "" }
		newClient = cmdServer:accept()
	end

	-- Process data from connected clients.
	local deadClients = {}
	for client, state in pairs(clients) do
		-- Read available data.
		local data, err, partial = client:receive(4096)
		local received = data or partial
		if received and received ~= "" then
			state.buffer = state.buffer .. received
			-- Process complete lines.
			while true do
				local newlinePos = state.buffer:find("\n")
				if not newlinePos then break end
				local line = state.buffer:sub(1, newlinePos - 1)
				state.buffer = state.buffer:sub(newlinePos + 1)
				processCommand(client, line)
			end
		end
		if err == "closed" then
			deadClients[#deadClients + 1] = client
		end
	end

	-- Remove disconnected clients.
	for _, client in ipairs(deadClients) do
		-- A dropped DCSAutoMate mustn't leave a control held.
		pcall(releaseSimCommandHoldsOf, client)
		-- Remove from subscriptions.
		for _, sub in pairs(subscriptions) do
			sub.clients[client] = nil
		end
		clients[client] = nil
		pcall(function() client:close() end)
	end
end


-- ===========================================================================
-- DCS Export API Hooks
-- ===========================================================================

-- Chain any previously defined handlers so other export scripts still work.
local PrevLuaExportStart = LuaExportStart
local PrevLuaExportStop = LuaExportStop
local PrevLuaExportBeforeNextFrame = LuaExportBeforeNextFrame
local PrevLuaExportActivityNextEvent = LuaExportActivityNextEvent

function LuaExportStart()
	if PrevLuaExportStart then
		PrevLuaExportStart()
	end
	-- Initialize TCP command server.
	cmdServer = socket.tcp()
	cmdServer:setoption("reuseaddr", true)
	cmdServer:bind("127.0.0.1", tcpPort)
	cmdServer:listen(5)
	cmdServer:settimeout(0)
	clients = {}
	subscriptions = {}
	logToFile("TCP command server started on port " .. tcpPort)
end

function LuaExportStop()
	-- Close all TCP client connections.
	for client, _ in pairs(clients) do
		pcall(function() client:close() end)
	end
	clients = {}
	subscriptions = {}
	simCommandHolds = {}

	-- Close TCP server.
	if cmdServer then
		cmdServer:close()
		cmdServer = nil
	end

	-- Close UDP sender.
	if udpSender then
		udpSender:close()
	end

	logToFile("DCSAutoMateExport stopping...")

	if PrevLuaExportStop then
		PrevLuaExportStop()
	end
end

function LuaExportBeforeNextFrame()
	processTcpClients()
	local ok, err = pcall(updateSimCommandHolds, LoGetModelTime())
	if not ok then
		logToFile("Sim command hold failed, dropping all holds: " .. tostring(err))
		simCommandHolds = {}
	end
	if PrevLuaExportBeforeNextFrame then
		PrevLuaExportBeforeNextFrame()
	end
end

-- Track the last time we sent UDP telemetry (once per second).
local lastTelemetrySendTime = 0

function LuaExportActivityNextEvent(t)
	-- TCP subscription updates at ~20 Hz.
	processSubscriptions(t)

	-- UDP telemetry broadcast at ~1 Hz.
	if t - lastTelemetrySendTime >= 1 then
		sendTelemetry()
		lastTelemetrySendTime = t
	end

	if PrevLuaExportActivityNextEvent then
		PrevLuaExportActivityNextEvent(t)
	end

	return t + 0.05
end
