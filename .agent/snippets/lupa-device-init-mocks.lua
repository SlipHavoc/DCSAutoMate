-- Lupa mock setup for executing DCS device_init.lua
-- These mocks (plus the clickabledata mocks) allow device_init.lua to execute
-- far enough to populate the indicators[] table.

-- C++ engine functions that device_init.lua calls directly:
function mount_vfs_model_path() end
function mount_vfs_texture_path() end
function mount_vfs_liveries_path() end

function get_param_handle(name)
    return { set = function(self, val) end, get = function(self) return 0 end }
end

function get_aircraft_property_or_nil(name)
    return nil  -- Uses module defaults (e.g. FA-18C: helmet_option=nil → 1 → HMS)
end

-- Rendering constants:
render_purpose = { GENERAL = 0, BAKE = 1, HUD_ONLY_VIEW = 2, SCREENSPACE = 3 }
indicator_types = { COMMON = 0 }

-- No-op stubs:
function update_screenspace_displacement() end
function try_find_assigned_viewport() return nil end
function Copy(t) return t end

-- CRITICAL: dofile must use pcall to tolerate runtime errors in font/material
-- files that reference globals from missing DCS engine scripts.
local originalDofile = dofile
function dofile(path)
    local f, err = loadfile(path)
    if f then
        local ok, result = pcall(f)
        if ok then return result
        else io.stderr:write("Warning: Error executing " .. path .. ": " .. result .. "\n")
        end
    else
        io.stderr:write("Warning: Could not load " .. path .. ": " .. err .. "\n")
    end
end
