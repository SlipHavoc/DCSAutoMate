---@diagnostic disable: undefined-global
-- Add the following to \Saved Games\DCS\Scripts\Export.lua
--dofile(lfs.writedir()..[[Scripts\DCSAutoMateExport.lua]])

package.path = package.path .. ";.\\LuaSocket\\?.lua"
package.cpath = package.cpath .. ";.\\LuaSocket\\?.dll"

package.path = lfs.writedir() .. "?.lua;" .. package.path

-- all requires must come after updates to package.path


local socket = require("socket")

-- Define the UDPMulticastSender class
local UDPMulticastSender = {}
UDPMulticastSender.__index = UDPMulticastSender

-- Constructor
function UDPMulticastSender:new(multicast_group, port)
    local self = setmetatable({}, UDPMulticastSender)
    self.multicast_group = multicast_group
    self.port = port
    self.udp = socket.udp()
    self.udp:setpeername(multicast_group, port)
    self.udp:setoption("ip-multicast-ttl", 1)
    return self
end

-- Method to send data
function UDPMulticastSender:sendData(data)
    local success, err = self.udp:send(data)
    -- if not success then
    --     print("Error sending data: " .. err)
    -- else
    --     print("Data sent: " .. data)
    -- end
end

-- Method to close the UDP socket
function UDPMulticastSender:close()
    if self.udp then
        self.udp:close()
    end
end

local sender = UDPMulticastSender:new("239.255.61.21", 6121)

-- DCS Export functions

function LuaExportActivityNextEvent(t)
	-- -- Example usage: send a test message periodically
    --sender:sendData("Periodic update from DCS!")

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

	-- local allDcsData = {
	-- 	--Object
	-- 	--Allows for all objects to be accessible. For example this is how tacview knows and returns where every single object in the game is at.
	-- 	--LoGetObjectById = LoGetObjectById(),
	-- 	LoGetWorldObjects = LoGetWorldObjects(),

	-- 	--Sensor
	-- 	--Exports sensor data from your aircraft.
	-- 	LoGetTWSInfo = LoGetTWSInfo(),
	-- 	LoGetTargetInformation = LoGetTargetInformation(),
	-- 	LoGetLockedTargetInformation = LoGetLockedTargetInformation(),
	-- 	LoGetF15_TWS_Contacts = LoGetF15_TWS_Contacts(),
	-- 	LoGetSightingSystemInfo = LoGetSightingSystemInfo(),
	-- 	LoGetWingTargets = LoGetWingTargets(),

	-- 	--Ownship
	-- 	--Exports data about your own aircraft. For example simple radio uses one of these to get the players current location and radio information.
	-- 	LoGetPlayerPlaneId = LoGetPlayerPlaneId(),
	-- 	LoGetIndicatedAirSpeed = LoGetIndicatedAirSpeed(),
	-- 	LoGetAngleOfAttack = LoGetAngleOfAttack(),
	-- 	LoGetAngleOfSideSlip = LoGetAngleOfSideSlip(),
	-- 	LoGetAccelerationUnits = LoGetAccelerationUnits(),
	-- 	LoGetVerticalVelocity = LoGetVerticalVelocity(),
	-- 	LoGetADIPitchBankYaw = LoGetADIPitchBankYaw(),
	-- 	LoGetTrueAirSpeed = LoGetTrueAirSpeed(),
	-- 	LoGetAltitudeAboveSeaLevel = LoGetAltitudeAboveSeaLevel(),
	-- 	LoGetAltitudeAboveGroundLevel = LoGetAltitudeAboveGroundLevel(),
	-- 	LoGetMachNumber = LoGetMachNumber(),
	-- 	LoGetRadarAltimeter = LoGetRadarAltimeter(),
	-- 	LoGetMagneticYaw = LoGetMagneticYaw(),
	-- 	LoGetGlideDeviation = LoGetGlideDeviation(),
	-- 	LoGetSideDeviation = LoGetSideDeviation(),
	-- 	LoGetSlipBallPosition = LoGetSlipBallPosition(),
	-- 	LoGetBasicAtmospherePressure = LoGetBasicAtmospherePressure(),
	-- 	LoGetControlPanel_HSI = LoGetControlPanel_HSI(),
	-- 	LoGetEngineInfo = LoGetEngineInfo(),
	-- 	LoGetSelfData = LoGetSelfData(),
	-- 	LoGetCameraPosition = LoGetCameraPosition(),
	-- 	LoSetCameraPosition = LoSetCameraPosition(),
	-- 	--LoSetCommand = LoSetCommand(),
	-- 	LoGetMCPState = LoGetMCPState(),
	-- 	LoGetRoute = LoGetRoute(),
	-- 	LoGetNavigationInfo = LoGetNavigationInfo(),
	-- 	LoGetPayloadInfo = LoGetPayloadInfo(),
	-- 	LoGetWingInfo = LoGetWingInfo(),
	-- 	LoGetMechInfo = LoGetMechInfo(),
	-- 	LoGetRadioBeaconsStatus = LoGetRadioBeaconsStatus(),
	-- 	LoGetVectorVelocity = LoGetVectorVelocity(),
	-- 	LoGetVectorWindVelocity = LoGetVectorWindVelocity(),
	-- 	LoGetSnares = LoGetSnares(),
	-- 	LoGetAngularVelocity = LoGetAngularVelocity(),
	-- 	LoGetHeightWithObjects = LoGetHeightWithObjects(),
	-- 	LoGetFMData = LoGetFMData(),

	-- 	--Always
	-- 	LoGetPilotName = LoGetPilotName(),
	-- 	LoGetAltitude = LoGetAltitude(),
	-- 	--LoGetNameByType = LoGetNameByType(),
	-- 	--LoGeoCoordinatesToLoCoordinates = LoGeoCoordinatesToLoCoordinates(),
	-- 	--LoCoordinatesToGeoCoordinates = LoCoordinatesToGeoCoordinates(),
	-- 	LoGetVersionInfo = LoGetVersionInfo(),
	-- 	LoGetWindAtPoint = LoGetWindAtPoint(),
	-- 	LoGetModelTime = LoGetModelTime(),
	-- 	LoGetMissionStartTime = LoGetMissionStartTime(),
	-- }

	-- local dataString = tableToString(allDcsData)

	local DcsAutoMateData = {
		--Object
		--Allows for all objects to be accessible. For example this is how tacview knows and returns where every single object in the game is at.
		--LoGetObjectById = LoGetObjectById(),
		--LoGetWorldObjects = LoGetWorldObjects(),

		--Sensor
		--Exports sensor data from your aircraft.
		--LoGetTWSInfo = LoGetTWSInfo(),
		--LoGetTargetInformation = LoGetTargetInformation(),
		--LoGetLockedTargetInformation = LoGetLockedTargetInformation(),
		--LoGetF15_TWS_Contacts = LoGetF15_TWS_Contacts(),
		--LoGetSightingSystemInfo = LoGetSightingSystemInfo(),
		--LoGetWingTargets = LoGetWingTargets(),

		--Ownship
		--Exports data about your own aircraft. For example simple radio uses one of these to get the players current location and radio information.
		--LoGetPlayerPlaneId = LoGetPlayerPlaneId(),
		LoGetIndicatedAirSpeed = LoGetIndicatedAirSpeed(), -- m/s
		--LoGetAngleOfAttack = LoGetAngleOfAttack(),
		--LoGetAngleOfSideSlip = LoGetAngleOfSideSlip(),
		--LoGetAccelerationUnits = LoGetAccelerationUnits(),
		LoGetVerticalVelocity = LoGetVerticalVelocity(),
		--LoGetADIPitchBankYaw = LoGetADIPitchBankYaw(),
		LoGetTrueAirSpeed = LoGetTrueAirSpeed(), -- m/s
		LoGetAltitudeAboveSeaLevel = LoGetAltitudeAboveSeaLevel(),
		LoGetAltitudeAboveGroundLevel = LoGetAltitudeAboveGroundLevel(),
		LoGetMachNumber = LoGetMachNumber(),
		LoGetRadarAltimeter = LoGetRadarAltimeter(),
		--LoGetMagneticYaw = LoGetMagneticYaw(),
		--LoGetGlideDeviation = LoGetGlideDeviation(),
		--LoGetSideDeviation = LoGetSideDeviation(),
		--LoGetSlipBallPosition = LoGetSlipBallPosition(),
		--LoGetBasicAtmospherePressure = LoGetBasicAtmospherePressure(),
		--LoGetControlPanel_HSI = LoGetControlPanel_HSI(),
		LoGetEngineInfo = LoGetEngineInfo(),
		LoGetSelfData = LoGetSelfData(),
		--LoGetCameraPosition = LoGetCameraPosition(),
		--LoSetCameraPosition = LoSetCameraPosition(),
		--LoSetCommand = LoSetCommand(),
		--LoGetMCPState = LoGetMCPState(),
		--LoGetRoute = LoGetRoute(),
		--LoGetNavigationInfo = LoGetNavigationInfo(),
		LoGetPayloadInfo = LoGetPayloadInfo(),
		--LoGetWingInfo = LoGetWingInfo(),
		LoGetMechInfo = LoGetMechInfo(),
		--LoGetRadioBeaconsStatus = LoGetRadioBeaconsStatus(),
		--LoGetVectorVelocity = LoGetVectorVelocity(),
		--LoGetVectorWindVelocity = LoGetVectorWindVelocity(),
		--LoGetSnares = LoGetSnares(),
		--LoGetAngularVelocity = LoGetAngularVelocity(),
		LoGetHeightWithObjects = LoGetHeightWithObjects(),
		LoGetFMData = LoGetFMData(),

		--Always
		LoGetPilotName = LoGetPilotName(),
		--LoGetAltitude = LoGetAltitude(),
		--LoGetNameByType = LoGetNameByType(),
		--LoGeoCoordinatesToLoCoordinates = LoGeoCoordinatesToLoCoordinates(),
		--LoCoordinatesToGeoCoordinates = LoCoordinatesToGeoCoordinates(),
		LoGetVersionInfo = LoGetVersionInfo(),
		--LoGetWindAtPoint = LoGetWindAtPoint(),
		LoGetModelTime = LoGetModelTime(),
		LoGetMissionStartTime = LoGetMissionStartTime(),
	}
	local dataString = tableToString(DcsAutoMateData)

	sender:sendData(dataString)

    return t + 1 -- call again after 1 second
end
