# DXGUI Developer Guide

## WARNING ##

This is an AI-generated document based primarily on the code in the DCS dxgui and Scripts UI folders, and on what is known to work in DCSAutoMate.  It has been reviewed and corrected against the actual DXGUI source code by various AI models, but may still contain inaccuracies.

## Overview

DXGUI is the DCS World UI system used for creating in-game dialogs, overlays, and controls. This guide documents the control types, methods, properties, and patterns discovered through analyzing DCS World UI files and the DCSAutoMate implementation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [File Structure](#file-structure)
3. [Control Types Reference](#control-types-reference)
4. [Common Properties](#common-properties)
5. [Common Methods](#common-methods)
6. [Event Handlers and Callbacks](#event-handlers-and-callbacks)
7. [Skin System](#skin-system)
8. [Creating Widgets Programmatically](#creating-widgets-programmatically)
9. [Practical Examples](#practical-examples)
10. [Best Practices](#best-practices)
11. [Quick Reference](#quick-reference)
12. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Required Modules

Load these modules at the beginning of your Lua script:

```lua
package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"
local DialogLoader = require("DialogLoader")
local Skin = require("Skin")
local dxgui = require("dxgui")
local Input = require("Input")  -- For keyboard input management
local ListBoxItem = require("ListBoxItem")  -- For list/combo items
```

**Optional modules for programmatic widget creation:**
```lua
local RadioButton = require("RadioButton")
local Static = require("Static")
local EditBox = require("EditBox")
-- etc. for other control types
```

### Basic Workflow

1. Create a `.dlg` file defining your dialog structure
2. Create a `.lua` file to load and manipulate the dialog
3. Load the dialog using `DialogLoader.spawnDialogFromFile()`
4. Access widgets directly via `window.widgetName` (preferred) or using `DialogLoader.findWidgetByName()`
5. Set up event handlers and callbacks
6. Show the dialog with `:setVisible(true)`

### Minimal Example

**MyOverlay.dlg:**
```lua
dialog = {
	["type"] = "Window",
	["params"] = {
		["bounds"] = { ["x"] = 100, ["y"] = 100, ["w"] = 400, ["h"] = 300 },
		["enabled"] = true,
	},
	["children"] = {
		["myText"] = {
			["type"] = "Static",
			["params"] = {
				["bounds"] = { ["x"] = 10, ["y"] = 10, ["w"] = 380, ["h"] = 30 },
				["text"] = "Hello, DCS World!",
				["visible"] = true,
				["enabled"] = true,
				["zindex"] = 0,
			},
		},
	},
}
```

**MyOverlay.lua:**
```lua
local DialogLoader = require("DialogLoader")

local window = DialogLoader.spawnDialogFromFile("MyOverlay.dlg")
-- Access directly (preferred, as used by DCSAutoMate):
local textWidget = window.myText
-- Or access via findWidgetByName (wrapper around widget:findByName):
-- local textWidget = DialogLoader.findWidgetByName(window, "myText")

textWidget:setText("Updated text!")
window:setVisible(true)
```

---

## File Structure

### Dialog Files (.dlg)

Dialog files use Lua table format to define UI structure:

```lua
dialog = {
	["type"] = "Window",          -- Control type
	["params"] = { ... },          -- Properties and settings
	["skin"] = { ... },            -- Visual appearance (optional)
	["children"] = { ... },        -- Child controls (optional)
}
```

**Key sections:**
- `type` - The control type (Window, Panel, Static, Button, etc.)
- `params` - Control properties (bounds, text, name, etc.)
- `skin` - Appearance definitions with states
- `children` - Child controls (nested recursively). In DCS `.dlg` files this is commonly a table keyed by widget name.

Common `children` pattern:
```lua
["children"] = {
	["someWidgetName"] = {
		["type"] = "Static",
		["params"] = {
			["bounds"] = { ["x"] = 0, ["y"] = 0, ["w"] = 100, ["h"] = 20 },
			["text"] = "Label",
		},
	},
}
```

Note: Widget names are typically the key under `children` (e.g. `children["someWidgetName"]`), not `params.name`.

Also note: Most widgets use `params.bounds = { x, y, w, h }`, but some Window dialogs (including DCSAutoMate) use a wrapped form:
```lua
["bounds"] = {
	[1] = { ["x"] = 0, ["y"] = 0, ["w"] = 460, ["h"] = 380 },
}
```

### Lua Script Files

Script files load and manipulate dialogs:
- Use `DialogLoader.spawnDialogFromFile(path)` to load `.dlg` files
- Use `DialogLoader.findWidgetByName(window, "name")` to access widgets
- Set up event handlers with callback methods
- Manage window lifecycle and state

---

## Control Types Reference

### Window

Top-level container for dialogs and overlays.

**Properties:**
- `bounds` - Position and size (usually `{x, y, w, h}`; some Window dialogs use a wrapped `[1] = {x, y, w, h}` form)
- `draggable` - Allow window dragging (boolean)
- `resizable` - Allow window resizing (boolean)
- `modal` - Modal dialog behavior (boolean)
- `hasCursor` - Show mouse cursor (boolean)
- `offscreen` - Allow offscreen positioning (boolean)
- `zOrder` - Global z-order for overlays (number)

**Example:**
```lua
{
	["type"] = "Window",
	["params"] = {
		["bounds"] = { ["x"] = 0, ["y"] = 0, ["w"] = 600, ["h"] = 400 },
		["draggable"] = true,
		["hasCursor"] = true,
		["zOrder"] = 10,
	},
}
```

### Panel

Container for grouping controls. Use for layout organization.

**Properties:**
- `bounds` - Position and size
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `zindex` - Z-order within parent (number)

**Example:**
```lua

["leftPanel"] = {
	["type"] = "Panel",
	["params"] = {
		["bounds"] = { ["x"] = 0, ["y"] = 0, ["w"] = 200, ["h"] = 400 },
		["enabled"] = true,
		["visible"] = true,
		["zindex"] = 0,
	},
	["children"] = { ... },
}
```

### Static

Text labels and static content. Most common control for displaying text.

**Properties:**
- `bounds` - Position and size
- `text` - Display text (string)
- `tooltip` - Hover tooltip (string)
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `angle` - Rotation angle in degrees (number)
- `pivotPoint` - Center of rotation (table: `{x, y}`)

**Example:**
```lua

["titleLabel"] = {
	["type"] = "Static",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 10, ["w"] = 300, ["h"] = 30 },
		["text"] = "Configuration Settings",
		["visible"] = true,
		["enabled"] = true,
		["zindex"] = 0,
	},
}
```

### Button

Clickable button control.

**Properties:**
- `bounds` - Position and size
- `text` - Button label (string)
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `tooltip` - Hover tooltip (string)

**Example:**
```lua

["confirmButton"] = {
	["type"] = "Button",
	["params"] = {
		["bounds"] = { ["x"] = 250, ["y"] = 350, ["w"] = 100, ["h"] = 30 },
		["text"] = "Confirm",
		["enabled"] = true,
		["visible"] = true,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local button = DialogLoader.findWidgetByName(window, "confirmButton")
button:addMouseDownCallback(function()
	-- Handle button click
end)
```

### ComboList (ComboBox)

Dropdown selection list.

**Properties:**
- `bounds` - Position and size
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `tabOrder` - Tab navigation order (number)

**Example:**
```lua

["aircraftSelector"] = {
	["type"] = "ComboList",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 50, ["w"] = 200, ["h"] = 30 },
		["enabled"] = true,
		["visible"] = true,
		["tabOrder"] = 1,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local combo = DialogLoader.findWidgetByName(window, "aircraftSelector")
local item1 = ListBoxItem.new("F-16C")
combo:insertItem(item1)
local item2 = ListBoxItem.new("F/A-18C")
combo:insertItem(item2)
combo:selectItem(item1)

combo.onChange = function(self)
	local selected = self:getSelectedItem()
	print("Selected: " .. selected:getText())
end
```

### EditBox

Text input field.

**Properties:**
- `bounds` - Position and size
- `text` - Initial text (string)
- `multiline` - Allow multiple lines (boolean)
- `numeric` - Numeric input only (boolean)
- `password` - Password masking (boolean)
- `readOnly` - Read-only mode (boolean)
- `acceptDecimalPoint` - Allow decimal input (boolean)
- `maxLength` - Maximum character count (number)

**Example:**
```lua

["nameInput"] = {
	["type"] = "EditBox",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 90, ["w"] = 200, ["h"] = 30 },
		["text"] = "",
		["maxLength"] = 50,
		["enabled"] = true,
		["visible"] = true,
		["tabOrder"] = 1,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local editBox = DialogLoader.findWidgetByName(window, "nameInput")
editBox:setText("Default value")
local value = editBox:getText()
```

### Grid

Table/grid layout with rows and columns.

**Properties:**
- `bounds` - Position and size
- `rows` - Number of rows (number)
- `fixedColumns` - Number of fixed columns (number)
- `columnMouseResizing` - Allow column resizing (boolean)
- `vertScrollBarStep` - Vertical scroll increment (number)
- `vertScrollBarPageStep` - Vertical scroll page increment (number)
- `horzScrollBarStep` - Horizontal scroll increment (number)
- `horzScrollBarPageStep` - Horizontal scroll page increment (number)

**Example:**
```lua

["dataGrid"] = {
	["type"] = "Grid",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 130, ["w"] = 580, ["h"] = 200 },
		["rows"] = 10,
		["fixedColumns"] = 1,
		["columnMouseResizing"] = true,
		["enabled"] = true,
		["visible"] = true,
		["zindex"] = 0,
	},
	["children"] = { ... },  -- GridHeaderCell controls (commonly keyed by name)
}
```

**Usage:**
```lua
local grid = DialogLoader.findWidgetByName(window, "dataGrid")
grid:insertRow(20)
local rowIndex = grid:getRowCount() - 1
local cell = Static.new()
cell:setText("Row data")
grid:setCell(0, rowIndex, cell)
```

### GridHeaderCell

Column header for Grid controls.

**Properties:**
- `bounds` - Header position/size (use `bounds.w` f
- `layout` - Layout configuration (table)or width)
- `text` - Header text (string)
- `draggable` - Allow dragging/reordering (boolean)

**Example:**
```lua
{
	["type"] = "GridHeaderCell",
	["params"] = {
		["bounds"] = { ["x"] = 0, ["y"] = 0, ["w"] = 200, ["h"] = 20 },
		["draggable"] = false,
		["text"] = "Name",
	},
}
```

### ListBox

Scrollable list of items.

**Properties:**
- `bounds` - Position and size
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `multipleSelection` - Allow multiple selection (boolean)

**Example:**
```lua

["fileList"] = {
	["type"] = "ListBox",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 130, ["w"] = 200, ["h"] = 200 },
		["enabled"] = true,
		["visible"] = true,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local listBox = DialogLoader.findWidgetByName(window, "fileList")
local item = ListBoxItem.new("File1.txt")
listBox:insertItem(item)
listBox:selectItem(item)
```

### RadioButton

Radio button control for mutually exclusive options.

**Properties:**
- `bounds` - Position and size
- `text` - Label text (string)
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `tabOrder` - Tab navigation order (number)

**Example:**
```lua

["optionA"] = {
	["type"] = "RadioButton",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 170, ["w"] = 150, ["h"] = 25 },
		["text"] = "Option A",
		["enabled"] = true,
		["visible"] = true,
		["tabOrder"] = 1,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local radio = DialogLoader.findWidgetByName(window, "optionA")
radio:setState(true)  -- Select this option
radio.onChange = function(self)
	if self:getState() then
		-- This option was selected
	end
end
```

### CheckBox

Checkbox control for independent toggle options (unlike RadioButton which is mutually exclusive).

**Properties:**
- `bounds` - Position and size
- `text` - Label text (string)
- `state` - Initial checked/unchecked state (boolean)
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `tabOrder` - Tab navigation order (number)

**Example:**
```lua

["enableFeature"] = {
	["type"] = "CheckBox",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 200, ["w"] = 150, ["h"] = 25 },
		["text"] = "Enable Feature",
		["state"] = false,
		["enabled"] = true,
		["visible"] = true,
		["tabOrder"] = 1,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local checkbox = DialogLoader.findWidgetByName(window, "enableFeature")
checkbox:setState(true)  -- Check the box
local isChecked = checkbox:getState()
checkbox.onChange = function(self)
	if self:getState() then
		-- Checkbox is now checked
	else
		-- Checkbox is now unchecked
	end
end
```

### AutoScrollText

Auto-scrolling text display for messages or logs.

**Properties:**
- `bounds` - Position and size
- `text` - Initial text (string)
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `tooltip` - Hover tooltip (string)
- `zindex` - Z-order (number)

**Example:**
```lua

["messageLog"] = {
	["type"] = "AutoScrollText",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 210, ["w"] = 380, ["h"] = 150 },
		["enabled"] = true,
		["visible"] = true,
		["zindex"] = 0,
	},
}
```

**Usage:**
```lua
local log = window.messageLog
log:addText("New message appeared!", 5.0)  -- display for 5 seconds
log:clear()  -- clear all messages
```

### HorzProgressBar

Horizontal progress indicator control.

**Properties:**
- `bounds` - Position and size
- `value` - Current value (number)
- `range` - Min and max values (table: `{min, max}`)
- `step` - Step increment (number)
- `text` - Text overlay (string)
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)

**Example:**
```lua

["loadingBar"] = {
	["type"] = "HorzProgressBar",
	["params"] = {
		["bounds"] = { ["x"] = 10, ["y"] = 370, ["w"] = 380, ["h"] = 20 },
		["value"] = 0,
		["enabled"] = true,
		["visible"] = true,
		["zindex"] = 0,
	},
}
```

### HorzScrollBar

Horizontal scrollbar control.

**Properties:**
- `bounds` - Position and size
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `value` - Current scroll position (number)
- `step` - Scroll increment (number)
- `pageStep` - Page scroll increment (number)
- `range` - Min and max values (table: `{min, max}`)

### VertScrollBar

Vertical scrollbar control.

**Properties:**
- `bounds` - Position and size
- `enabled` - Interactive state (boolean)
- `visible` - Visibility (boolean)
- `value` - Current scroll position (number)
- `step` - Scroll increment (number)
- `pageStep` - Page scroll increment (number)
- `range` - Min and max values (table: `{min, max}`)

### ComboBox

Editable dropdown control — combines a text input field with a dropdown list. Different from ComboList which is select-only.

**Properties:**
- `bounds` - Position and size
- `readOnly` - Disable text editing (boolean)
- `enableSearchLine` - Enable search/filter in dropdown (boolean)
- `hintText` - Placeholder text for edit field (string)
- `tabOrder` - Tab navigation order (number)

**Usage:**
```lua
local combo = window.myComboBox

-- Add items
combo:newItem("Option A")
combo:newItem("Option B")

-- Separate callbacks for list selection vs text editing
combo:addChangeListBoxCallback(function(self)
	local selected = self:getSelectedItem()
	if selected then
		print("Selected from list: " .. selected:getText())
	end
end)

combo:addChangeEditBoxCallback(function(self)
	print("User typed: " .. self:getText())
end)

-- Text selection in the edit field
combo:setSelection(0, 5)  -- select first 5 characters
```

### HorzSlider / VertSlider

Horizontal and vertical slider controls for selecting a value within a range.

**Properties:**
- `bounds` - Position and size
- `value` - Current value (number)
- `range` - Min and max values (table: `{min, max}`)
- `step` - Step increment (number)
- `pageStep` - Page step increment (number)
- `tabOrder` - Tab navigation order (number)

**Usage:**
```lua
local slider = window.mySlider
slider:setRange(0, 100)
slider:setValue(50)
slider:setStep(1)

slider:addChangeCallback(function(self)
	local value = self:getValue()
	print("Slider value: " .. value)
end)

-- Thumb press/release callbacks
slider:addThumbPressedCallback(function(self)
	-- User grabbed the slider thumb
end)

slider:addThumbReleasedCallback(function(self)
	-- User released the slider thumb
end)
```

### SpinBox

Numeric spinner control with up/down buttons and text input.

**Properties:**
- `bounds` - Position and size
- `value` - Current value (number)
- `range` - Min and max values (table: `{min, max}`)
- `checkRange` - Whether to enforce range limits (boolean)
- `step` - Step increment (number)
- `pageStep` - Page step increment (number)
- `acceptDecimalPoint` - Allow decimal input (boolean)
- `tabOrder` - Tab navigation order (number)

**Usage:**
```lua
local spinBox = window.mySpinBox
spinBox:setRange(0, 100)
spinBox:setValue(50)
spinBox:setStep(1)
spinBox:setAcceptDecimalPoint(false)

-- Format display string (C-style format)
spinBox:setFormatString("%05g")

-- Show/hide up/down buttons
spinBox:setButtonsVisible(true)

-- Select all text in the input field
spinBox:selectAll()

spinBox:addChangeCallback(function(self)
	local value = self:getValue()
end)
```

### ToggleButton

Toggle button that stays pressed/released. Inherits from Widget.

**Properties:**
- `bounds` - Position and size
- `text` - Button label (string)
- `state` - Toggled/untoggled state (boolean)
- `sound` - Sound file to play on change (string)
- `tabOrder` - Tab navigation order (number)

**Usage:**
```lua
local toggle = window.myToggle
toggle:setState(true)
local isOn = toggle:getState()

toggle:addChangeCallback(function(self)
	if self:getState() then
		-- Toggled on
	else
		-- Toggled off
	end
end)
```

### SwitchButton

Switch-style toggle control (sliding toggle visual). Functionally identical to ToggleButton but with a different visual style.

**Properties:** Same as ToggleButton (`state`, `sound`, `tabOrder`).

### ScrollPane

Scrollable container widget. Child widgets placed inside can scroll when they exceed the visible area.

**Properties:**
- `bounds` - Position and size
- `vertScrollBarStep` - Vertical scroll increment (number)
- `vertScrollBarPageStep` - Vertical scroll page increment (number)
- `horzScrollBarStep` - Horizontal scroll increment (number)
- `horzScrollBarPageStep` - Horizontal scroll page increment (number)
- `vertMouseWheel` - Enable vertical mouse wheel scrolling (boolean)
- `horzMouseWheel` - Enable horizontal mouse wheel scrolling (boolean)
- `layout` - Layout configuration (table)

**Usage:**
```lua
local scrollPane = window.myScrollPane

-- Insert child widgets
scrollPane:insertWidget(childWidget)
scrollPane:insertWidget(childWidget, index)  -- at specific position

-- Get scroll range and position
local min, max = scrollPane:getVertScrollRange()
local vertPos = scrollPane:getVertScrollValue()
scrollPane:setVertScrollValue(0)  -- scroll to top

-- Get visible area size
local viewW, viewH = scrollPane:getViewSize()

-- After resizing children, call this to update layout
scrollPane:updateWidgetsBounds()

-- Scroll change callback
scrollPane.onScrollChange = function(self)
	-- Handle scroll position change
end
```

### Window Subtypes

Windows have several specialized subtypes, selected automatically based on params in the `.dlg` file:

**OverlayWindow** (when `params.overlay = true`):
- Renders above all normal windows
- Has its own `setZOrder()` / `getZOrder()` for overlay stacking

**ModalWindow** (when `params.modal = true`):
- Use `setLockFlow(true)` to make `setVisible(true)` block execution until the window is closed (synchronous dialog behavior)
- Always renders on top (z-order methods are disabled)

**OffscreenWindow** (when `params.offscreen = true`):
- Renders to a texture/surface rather than the screen
- Supports programmatic mouse event injection: `mouseMove(x, y)`, `mouseDown(x, y, button)`, `mouseUp(x, y, button)`
- Z-order methods are disabled

**BuddyWindow** (when `params.buddy = true`):
- Positions itself relative to another widget
- Use `setBuddyWidget(widget)` to attach it to a widget (like a tooltip or popup)
- Z-order methods are disabled

### Additional Widget Types

These widget types exist in the DXGUI system but are less commonly used:

- **Menu / MenuBar / MenuItem / MenuSubItem** - Full menu system with menu bar and dropdown menus
- **MenuCheckItem / MenuRadioItem / MenuSeparatorItem** - Menu item variants
- **PieMenu / PieMenuItem / PieMenuSubItem** - Radial/pie menu system
- **TreeView / TreeViewItem** - Hierarchical tree control
- **CheckListBox / CheckListBoxItem** - List box with checkable items
- **TabGroupItem** - Tab control items with `state` property
- **Dial** - Rotary dial control with `range`, `value`, `step`, `cyclic` properties
- **TextureView** - Texture rendering widget
- **VideoPlayerWidget** - Video playback widget
- **WebViewWidget** - Web content rendering widget
- **DemoSceneWidget** - 3D scene rendering widget
- **ColorTextStatic** - Static text with color formatting
- **AnimatedColorStatic** - Animated color text control
- **Chart** - Chart/graph widget
- **HorzRangeIndicator / VertRangeIndicator** - Range indicator with `range` and `valueRange` properties
- **VertProgressBar** - Vertical progress bar (same API as HorzProgressBar)

---

## Common Properties

These properties are available on most control types:

| Property | Type | Description |
|----------|------|-------------|
| `bounds` | table | Position and size (commonly `{x, y, w, h}`; some Window dialogs use `{ [1] = {x, y, w, h} }`) |
| `enabled` | boolean | Enable/disable interactivity |
| `visible` | boolean | Show/hide control |
| `text` | string | Display text (label, button text, etc.) |
| `tooltip` | string | Hover tooltip text |
| `zindex` | number | Z-order within parent container |
| `tabOrder` | number | Tab navigation order |
| `state` | boolean | Checked/unchecked state (CheckBox, RadioButton) |
| `lockFlow` | boolean | Lock window layout flow (Window) |
| `textWrapping` | boolean | Enable text wrapping (EditBox multiline) |
| `hintText` | string | Placeholder/hint text (EditBox, ComboBox) |
| `sound` | string | Sound file to play on change (Button, ToggleButton, etc.) |

You can access widgets directly as properties of the window object (e.g. `window.confirmButton`, which is the preferred pattern), or using `DialogLoader.findWidgetByName(window, "name")` which is a thin wrapper around `widget:findByName(name)`.

### Widget Names (`findWidgetByName`)

In DCS `.dlg` files, widgets are commonly identified by their key under the parent `children` table (this is what `DialogLoader.findWidgetByName(...)` is typically used with), for example:

```lua
["children"] = {
	["confirmButton"] = {
		["type"] = "Button",
		["params"] = {
			["bounds"] = { ["x"] = 0, ["y"] = 0, ["w"] = 100, ["h"] = 20 },
			["text"] = "OK",
		},
	},
}
```

### Bounds Table

The `bounds` table defines position and size:

```lua
["bounds"] = {
	["x"] = 100,  -- Left position in pixels
	["y"] = 50,   -- Top position in pixels
	["w"] = 300,  -- Width in pixels
	["h"] = 200,  -- Height in pixels
}
```

Some Window dialogs use a wrapped form (example from DCSAutoMate):
```lua
["bounds"] = {
	[1] = { ["x"] = 0, ["y"] = 0, ["w"] = 460, ["h"] = 380 },
}
```

---

## Common Methods

### Positioning and Sizing

```lua
-- Set position and size
widget:setBounds(x, y, width, height)

-- Get current bounds
local x, y, w, h = widget:getBounds()

-- Set position only
widget:setPosition(x, y)

-- Get position
local x, y = widget:getPosition()

-- Get size
local w, h = widget:getSize()
```

### Visibility and State

```lua
-- Show/hide control
widget:setVisible(true)
widget:setVisible(false)

-- Check visibility
if widget:isVisible() then
	-- Widget is visible
end

-- Enable/disable control
widget:setEnabled(true)
widget:setEnabled(false)

-- Check focus state
if widget:getFocused() then
	-- Widget has focus
end
```

### Content

```lua
-- Set text content
widget:setText("New text")

-- Get text content
local text = widget:getText()

-- Clear content
widget:clear()
```

### Appearance

```lua
-- Apply skin/theme
widget:setSkin(skinTable)

-- Get current skin
local skin = widget:getSkin()

-- Set transparency (0 = invisible, 1 = opaque)
widget:setOpacity(0.8)
local opacity = widget:getOpacity()

-- Set zoom level
widget:setZoom(1.5)
local zoom = widget:getZoom()

-- Set tooltip text and skin
widget:setTooltipText("Hover help text")
local tip = widget:getTooltipText()
widget:setTooltipSkin(tooltipSkin)

-- Apply shader effect
widget:setShaderEffect("effectName", params)

-- Force redraw
widget:redraw()
```

### Coordinate Conversion

```lua
-- Convert screen coordinates to widget-local coordinates
local localX, localY = widget:windowToWidget(screenX, screenY)

-- Convert widget-local coordinates to screen coordinates
local screenX, screenY = widget:widgetToWindow(localX, localY)

-- Convert coordinates to a parent widget's coordinate space
local parentX, parentY = widget:widgetToParentWidget(x, y, parentWidget)
```

### Per-Frame Updates

```lua
-- Set a function to be called every frame
widget:setUpdateFunction(function(self, elapsedTime)
	-- Update animation, position, etc.
	-- elapsedTime is seconds since last frame
end)

-- Remove the update function
widget:setUpdateFunction(nil)
```

### Mouse Capture

```lua
-- Capture all mouse input to this widget (even outside its bounds)
widget:captureMouse()

-- Release mouse capture
widget:releaseMouse()
```

### Widget Management

```lua
-- Clone a widget template
local newWidget = templateWidget:clone()

-- Remove widget from parent (Panel or Window)
parentPanel:removeWidget(widget)
parentWindow:removeWidget(widget)

-- Remove all widgets from parent
parentPanel:removeAllWidgets()
parentWindow:removeAllWidgets()

-- Destroy window
window:kill()

-- Get widget type name
local typeName = widget:getTypeName()

-- Get root widget
local root = widget:getRoot()

-- Find child widget by name
local child = widget:findByName("childName")
```

### Window Specific

```lua
-- Show/hide mouse cursor for window
window:setHasCursor(true)
window:setHasCursor(false)

-- Center window on screen
window:centerWindow()

-- Set z-order (higher = on top)
window:setZOrder(100)
local zOrder = window:getZOrder()

-- Make window transparent to user input (click-through)
window:setTransparentForUserInput(true)

-- Set window as active
window:setActive(true)

-- Get current skin (useful for storing original before modifying)
local originalSkin = window:getSkin()
-- Later restore
window:setSkin(originalSkin)

-- Get window bounds
local x, y, w, h = window:getBounds()

-- Insert a widget into the window at optional index
window:insertWidget(widget)
window:insertWidget(widget, index)  -- index controls draw order

-- Overlay widgets (drawn on top, ignore user input)
window:insertOverlayWidget(overlayWidget)
window:removeOverlayWidget(overlayWidget)
```

### ComboList and ListBox Specific

```lua
-- Create and add item directly (most common pattern)
local item = comboList:newItem("Item text")

-- Alternative: Create item separately, then insert
local item = ListBoxItem.new("Item text")
comboList:insertItem(item)

-- Select an item
comboList:selectItem(item)

-- Get selected item
local selected = comboList:getSelectedItem()
if selected then
	local text = selected:getText()
end

-- Get item by index (0-based indexing)
local firstItem = comboList:getItem(0)
local secondItem = comboList:getItem(1)

-- Get number of items
local count = comboList:getItemCount()

-- Clear all items
comboList:clear()
-- Alternative:
comboList:removeAllItems()

-- Get the index of an item
local idx = comboList:getItemIndex(item)

-- Remove a specific item
comboList:removeItem(item)

-- Show/hide the dropdown popup programmatically
comboList:setWindowVisible(true)
local isDropdownVisible = comboList:getWindowVisible()
```

**Important:** ComboList and ListBox use **0-based indexing** for items.

### ListBox Specific

ListBox has some differences from ComboList in its callback model:

```lua
-- ListBox onChange receives the item and whether it was a double-click
listBox.onChange = function(self, item, dblClick)
	if item then
		if dblClick then
			-- Item was double-clicked
		else
			-- Item was single-clicked
		end
	end
end

-- Scroll to make an item visible
listBox:setItemVisible(item)

-- Get/set scroll position
local pos = listBox:getScrollPosition()
listBox:setScrollPosition(0)  -- scroll to top

-- Selection change callback
listBox:addSelectionChangeCallback(function(self)
	local selected = self:getSelectedItem()
end)

-- Item mouse event callbacks
listBox:addItemMouseDownCallback(function(self) end)
listBox:addItemMouseDoubleDownCallback(function(self) end)
listBox:addItemMouseUpCallback(function(self) end)
```

### EditBox Specific

```lua
-- Get number of lines (multiline EditBox)
local lineCount = editBox:getLineCount()

-- Get text length of a specific line (0-based line index)
local len = editBox:getLineTextLength(lineIndex)

-- Set text selection/cursor position
-- Parameters: startLine, startCol, endLine, endCol (0-based line numbers)
editBox:setSelectionNew(0, 0, 0, 0)  -- Start of first line
local lastLine = lineCount - 1
editBox:setSelectionNew(lastLine, 0, lastLine, 0)  -- Start of last line

-- Legacy selection method (single-line oriented: index, count)
editBox:setSelection(index, count)
local index, count = editBox:getSelection()

-- Set placeholder/hint text
editBox:setHintText("Enter value here...")
local hint = editBox:getHintText()
```

### Grid Specific

```lua
-- Add a new row (commonly used with an explicit height)
-- insertRow does NOT return an index; compute it separately
grid:insertRow(20)
local rowIndex = grid:getRowCount() - 1

-- Insert row at a specific position (0-based index)
grid:insertRow(20, index)

-- If height is nil, the row height is taken from the grid's skin
grid:insertRow()

-- Remove all rows
grid:removeAllRows()

-- Remove a specific row
grid:removeRow(rowIndex)

-- Clear row contents (keep the row, remove widgets)
grid:clearRow(rowIndex)

-- Set/get row height
grid:setRowHeight(rowIndex, height)
local h = grid:getRowHeight(rowIndex)

-- Get number of rows
local rowCount = grid:getRowCount()

-- Place widget in cell (0-based column and row indices)
grid:setCell(columnIndex, rowIndex, widget)

-- Get widget from cell
local cellWidget = grid:getCell(columnIndex, rowIndex)

-- Remove widget from cell (returns the removed widget)
local removed = grid:removeCell(columnIndex, rowIndex)

-- Column management
grid:insertColumn(width, headerWidget, index)
grid:removeColumn(index)
local colCount = grid:getColumnCount()
grid:setColumnWidth(index, width)
local w = grid:getColumnWidth(index)

-- Auto-fill remaining width across specified columns
grid:stretchColumns({0, 1, 2})  -- column indices to stretch

-- Column headers
grid:setColumnHeader(index, headerWidget)
local header = grid:getColumnHeader(index)

-- Row selection
grid:selectRow(rowIndex)   -- select a row (-1 or nil to deselect)
local selectedRow = grid:getSelectedRow()  -- returns -1 if none selected

-- Make a row visible (scroll to it)
grid:setRowVisible(rowIndex)

-- Get column/row from mouse position (window coordinates)
local column, row = grid:getMouseCursorColumnRow(mouseX, mouseY)

-- Scroll position
grid:setVertScrollPosition(pos)
local vertPos = grid:getVertScrollPosition()
grid:setHorzScrollPosition(pos)
local horzPos = grid:getHorzScrollPosition()

-- Row selection/hover callbacks
grid:addSelectRowCallback(function(self, currentRow, previousRow)
	-- Fires when row selection changes
end)

grid:addHoverRowCallback(function(self, currentRow, previousRow)
	-- Fires when hovered row changes
end)

-- Remove all content
grid:removeAll()  -- remove all rows and columns
grid:clear()      -- clear all content
```

**Important:** Grid columns and rows use **0-based indexing**.

### dxgui Module Methods

```lua
-- Get screen/window dimensions (four variants exist in DCS scripts)
local screenWidth, screenHeight = dxgui.GetScreenSize()   -- monitor resolution
local windowWidth, windowHeight = dxgui.GetWindowSize()   -- DCS render window size

-- Some DCS scripts alias dxgui to Gui:
-- local Gui = require('dxgui')
-- local w, h = Gui.GetScreenSize()
-- local w, h = Gui.GetWindowSize()
-- Use GetWindowSize for positioning within the DCS window (handles windowed vs fullscreen).
-- Use GetScreenSize for the actual monitor resolution.

-- Copy text to system clipboard
dxgui.CopyTextToClipboard("Text to copy")
```

---

## Event Handlers and Callbacks

### Callback Methods

Most controls support these callback registration methods:

```lua
-- Value or state changed
widget:addChangeCallback(function(self)
	local newValue = self:getText()
	-- Handle change
end)

-- Focus gained or lost
widget:addFocusCallback(function(self)
	if self:getFocused() then
		-- Focus gained
	else
		-- Focus lost
	end
end)

-- Mouse button down
widget:addMouseDownCallback(function(self, x, y, button)
	-- button: 1=left, 2=right, 3=middle
end)

-- Mouse button up
widget:addMouseUpCallback(function(self, x, y, button)
	-- Handle mouse release
end)

-- Mouse enters control area
widget:addMouseEnterCallback(function(self)
	-- Handle hover start
end)

-- Mouse leaves control area
widget:addMouseLeaveCallback(function(self)
	-- Handle hover end
end)

-- Keyboard shortcut (Window-only, NOT available on regular widgets)
window:addHotKeyCallback('escape', function()
	window:setVisible(false)
end)

window:addHotKeyCallback('Ctrl+Shift+Z', function()
	-- Toggle something
end)

-- Remove a hotkey callback
window:removeHotKeyCallback('escape', callbackFunction)

-- Hotkey format: [modifier+]buttonName
-- Modifiers (case-insensitive, any order): Ctrl, Alt, Shift
-- Button names from dxgui/bind/KeyNames.txt
-- Examples: "escape", "return", "Ctrl+S", "Ctrl+Alt+N"
-- For numpad + key: "alt+[\\+]" (escape the + with \\)

-- Key press (available on all widgets)
widget:addKeyDownCallback(function(self, keyName, unicode)
	-- keyName is from KeyNames.txt, unicode is the character code
	-- Return true to indicate the event was handled
end)

-- Key release
widget:addKeyUpCallback(function(self, keyName, unicode)
	-- Handle key release
end)

-- Mouse double-click
widget:addMouseDoubleDownCallback(function(self, x, y, button)
	-- Handle double-click
end)

-- Mouse wheel
widget:addMouseWheelCallback(function(self, x, y, clicks)
	-- clicks > 0 = scroll up, clicks < 0 = scroll down
	-- Return true to indicate the event was handled
end)

-- Mouse move
widget:addMouseMoveCallback(function(self, x, y)
	-- Handle mouse movement
end)

-- Position or size changed
widget:addPositionCallback(function(self)
	-- Widget was repositioned
end)

widget:addSizeCallback(function(self)
	-- Widget was resized
end)
```

### Removing Callbacks

All `add*Callback` methods have corresponding `remove*Callback` methods. You must pass the same function reference you used when adding:

```lua
local myCallback = function(self)
	-- Handle change
end

widget:addChangeCallback(myCallback)
-- Later:
widget:removeChangeCallback(myCallback)

-- Same pattern for all callback types:
-- removeChangeCallback, removeFocusCallback,
-- removePositionCallback, removeSizeCallback,
-- removeMouseCallback(type, cb), removeKeyboardCallback(type, cb),
-- removeMouseWheelCallback(cb), removeHotKeyCallback(hotkeyString, cb)
```

### Direct Assignment

Alternative to `addChangeCallback`:

```lua
-- Direct onChange assignment
widget.onChange = function(self)
	-- Handle change
end

-- Window close event
window.onClose = function(self)
	-- Handle window closing
end
```

### Callback Best Practices

1. **Use `self` parameter** - Callbacks receive the widget as first parameter
2. **Store state to prevent recursion** - Set flags before triggering changes:
   ```lua
   local updating = false
   widget.onChange = function(self)
   	if updating then return end
   	updating = true
   	-- Make changes
   	updating = false
   end
   ```
3. **Clean up references** - Remove callbacks when destroying widgets to prevent memory leaks

---

## Skin System

Skins define the visual appearance of controls with support for multiple states.

### Skin Structure

```lua
["skin"] = {
	["params"] = {
		["name"] = "customSkin",
	},
	["states"] = {
		["released"] = { ... },  -- Normal state
		["hover"] = { ... },     -- Mouse over
		["pressed"] = { ... },   -- Being clicked
		["disabled"] = { ... },  -- Inactive state
	},
}
```

### State Properties

Each state can define:

```lua
["released"] = {
	[1] = {  -- Layer 1 (background)
		["bkg"] = {
			-- 9-slice image
			["picture"] = "path/to/image.png",
			["insets"] = {10, 10, 10, 10},  -- top, bottom, left, right
		},
	},
	[2] = {  -- Layer 2 (text)
		["text"] = {
			["fontSize"] = 14,
			["color"] = "0xffffffff",  -- RGBA hex
			["horzAlign"] = "left",    -- left, center, right
			["vertAlign"] = "center",  -- top, center, bottom
		},
	},
	[3] = {  -- Layer 3 (picture/icon)
		["picture"] = {
			["file"] = "path/to/icon.png",
			["minSize"] = {16, 16},
		},
	},
},
```

### Color Format

Colors use RGBA hex format: `"0xRRGGBBAA"`

Examples:
- `"0xffffffff"` - White, fully opaque
- `"0x000000ff"` - Black, fully opaque
- `"0xff0000ff"` - Red, fully opaque
- `"0x00ff00ff"` - Green, fully opaque
- `"0x0000ffff"` - Blue, fully opaque
- `"0xffffff80"` - White, 50% transparent
- `"0x00000000"` - Transparent

### 9-Slice Backgrounds

The `insets` property defines 9-slice scaling:

```lua
["bkg"] = {
	["picture"] = "background.png",
	["insets"] = {10, 10, 10, 10},  -- top, bottom, left, right
}
```

This divides the image into 9 sections:
- Corners remain fixed size
- Edges stretch in one direction
- Center stretches in both directions

### Text Alignment

Horizontal alignment (`horzAlign`):
- `"left"` - Align to left edge
- `"center"` - Center horizontally
- `"right"` - Align to right edge

Vertical alignment (`vertAlign`):
- `"top"` - Align to top edge
- `"center"` - Center vertically
- `"bottom"` - Align to bottom edge

### Additional Text Properties

```lua
["text"] = {
	["color"] = "0xffffffff",
	["font"] = "CONSOLA.TTF",  -- Font file name
	["fontSize"] = 14,
	["lineHeight"] = 14,  -- Line spacing
	["horzAlign"] = "left",
	["vertAlign"] = "center",
}
```

### Window Skin Header

Windows can have custom header skins:

```lua
["skin"] = {
	["skins"] = {
		["header"] = {
			["skinData"] = {
				["params"] = {
					["hasCloseButton"] = false,
					["insets"] = {
						["top"] = 2,
						["bottom"] = 2,
						["left"] = 2,
						["right"] = 2,
					},
				},
				["states"] = {
					["released"] = {
						[1] = {
							["bkg"] = {
								["center_center"] = "0x1a232dff",
							},
							["text"] = {
								["color"] = "0xffffffff",
							},
						},
					},
				},
			},
		},
	},
}
```

### Clearing Skin Properties with $nil$

Use `"$nil$"` to explicitly remove/clear skin properties:

```lua
["states"] = {
	["released"] = {
		[1] = {
			["bkg"] = {
				["center_center"] = "$nil$",  -- Remove background
				["insets"] = "$nil$",  -- Remove insets
				["file"] = "$nil$",  -- Remove image
			},
		},
	},
}
```

This is useful for creating transparent or minimal skins based on existing ones.

### Applying Skins Programmatically

```lua
-- Get current skin
local originalSkin = widget:getSkin()

-- Modify skin
local newSkin = {
	["params"] = originalSkin.params,
	["states"] = {
		["released"] = {
			{
				["text"] = {
					["color"] = "0xff0000ff",  -- Red text
				},
			},
		},
	},
}

-- Apply modified skin
widget:setSkin(newSkin)

-- Restore original skin later
widget:setSkin(originalSkin)
```

---

## Creating Widgets Programmatically

Beyond cloning templates, you can create widgets directly from modules:

```lua
-- Require the control type module
local RadioButton = require("RadioButton")
local Static = require("Static")
local EditBox = require("EditBox")

-- Create new widgets
local radio = RadioButton.new("Option text")
local label = Static.new()
local input = EditBox.new()

-- Configure the widget
radio:setBounds(10, 10, 200, 25)
radio:setText("My Option")
radio:setState(false)

-- Add to parent container
parentPanel:insertWidget(radio)
-- or for grids:
grid:setCell(columnIndex, rowIndex, radio)
```

### Custom Widget Properties

You can attach custom properties to widgets for state tracking:

```lua
-- Add custom data to widgets
radioButton.dcsAutoMateValue = "someValue"
combo.dcsAutoMateLabelToValue = {}
combo.dcsAutoMateValueToItem = {}
editBox.dcsAutoMateVarName = "varName"

-- Access later in callbacks
widget.onChange = function(self)
	local customValue = self.dcsAutoMateValue
	-- Use custom data
end
```

This pattern is useful for:
- Storing original values
- Mapping display text to internal values
- Tracking widget state across callbacks
- Associating widgets with data models

---

## Practical Examples

### Example 1: Loading and Displaying a Dialog

```lua
package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"
local DialogLoader = require("DialogLoader")

-- Load dialog from file
local window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")

-- Position at screen center
local screenWidth, screenHeight = dxgui.GetScreenSize()
local dialogWidth = 600
local dialogHeight = 400
local x = (screenWidth - dialogWidth) / 2
local y = (screenHeight - dialogHeight) / 2
window:setBounds(x, y, dialogWidth, dialogHeight)

-- Show window
window:setVisible(true)

-- Add close on Escape key
window:addHotKeyCallback('escape', function()
	window:setVisible(false)
end)
```

### Example 2: Creating an Overlay

```lua
local DialogLoader = require("DialogLoader")
local dxgui = require("dxgui")

-- Load overlay dialog
local overlay = DialogLoader.spawnDialogFromFile("Overlay.dlg")

-- Position at top-right corner
local screenWidth, screenHeight = dxgui.GetScreenSize()
overlay:setBounds(screenWidth - 320, 10, 300, 200)

-- Set as overlay (always on top)
overlay:setZOrder(100)

-- Make it visible
overlay:setVisible(true)

-- Toggle with hotkey
local overlayVisible = true
overlay:addHotKeyCallback('Ctrl+Shift+O', function()
	overlayVisible = not overlayVisible
	overlay:setVisible(overlayVisible)
end)
```

### Example 3: Dynamic Widget Creation with Templates

```lua
local DialogLoader = require("DialogLoader")

local window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")
local grid = DialogLoader.findWidgetByName(window, "dataGrid")
local template = DialogLoader.findWidgetByName(window, "rowTemplate")

-- Hide template
template:setVisible(false)

-- Create rows dynamically
local data = {"Item 1", "Item 2", "Item 3"}
for i, text in ipairs(data) do
	grid:insertRow(20)  -- insertRow does NOT return an index
	local rowIndex = grid:getRowCount() - 1

	-- Clone template
	local widget = template:clone()
	widget:setText(text)
	widget:setVisible(true)

	-- Add to grid
	grid:setCell(0, rowIndex, widget)

	-- Add event handler
	widget.onChange = function(self)
		print("Selected: " .. self:getText())
	end
end
```

### Example 4: Populating a ComboList

```lua
local DialogLoader = require("DialogLoader")

local window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")
local combo = DialogLoader.findWidgetByName(window, "aircraftCombo")

-- Clear existing items
combo:clear()

-- Method 1: Using newItem (simpler, more common)
local aircraft = {"F-16C", "F/A-18C", "F-15E", "A-10C II"}
for i, name in ipairs(aircraft) do
	combo:newItem(name)
end

-- Select first item by index (0-based)
local firstItem = combo:getItem(0)
if firstItem then
	combo:selectItem(firstItem)
end

-- Method 2: Using ListBoxItem (more control)
local item = ListBoxItem.new("Custom item")
combo:insertItem(item)
combo:selectItem(item)

-- Handle selection change
combo.onChange = function(self)
	local selected = self:getSelectedItem()
	if selected then
		print("Selected aircraft: " .. selected:getText())
	end
end

-- Get item count
local count = combo:getItemCount()
print("Total items: " .. count)
```

### Example 5: Keyboard Input Management

When using EditBox controls, lock/unlock keyboard input to prevent game controls from interfering:

```lua
local DialogLoader = require("DialogLoader")
local Input = require("Input")

local window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")
local editBox = DialogLoader.findWidgetByName(window, "nameInput")

local keyboardLocked = false

local function lockKeyboard()
	if not keyboardLocked then
		local keyboardEvents = Input.getDeviceKeys(Input.getKeyboardDeviceName())
		DCS.lockKeyboardInput(keyboardEvents)
		keyboardLocked = true
	end
end

local function unlockKeyboard(releaseKeys)
	if keyboardLocked then
		DCS.unlockKeyboardInput(releaseKeys)
		keyboardLocked = false
	end
end

-- Lock keyboard when EditBox gains focus
editBox:addFocusCallback(function(self)
	if self:getFocused() then
		lockKeyboard()
	else
		unlockKeyboard(true)
	end
end)
```

### Example 6: Safe UI Operations with pcall

Wrap UI operations in `pcall()` to prevent crashes:

```lua
local function safeUpdateUI()
	local success, err = pcall(function()
		local window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")
		local widget = DialogLoader.findWidgetByName(window, "myWidget")
		widget:setText("Updated")
		window:setVisible(true)
	end)

	if not success then
		print("UI Error: " .. tostring(err))
	end
end

safeUpdateUI()
```

### Example 7: Grid with Dynamic Content

```lua
local DialogLoader = require("DialogLoader")

local window = DialogLoader.spawnDialogFromFile("DataGrid.dlg")
local grid = DialogLoader.findWidgetByName(window, "mainGrid")

-- Clear existing rows
grid:removeAllRows()

-- Data to display
local data = {
	{name = "Waypoint 1", lat = "N 42° 30.5'", lon = "E 041° 15.2'"},
	{name = "Waypoint 2", lat = "N 42° 31.8'", lon = "E 041° 16.7'"},
	{name = "Waypoint 3", lat = "N 42° 33.1'", lon = "E 041° 18.3'"},
}

-- Populate grid
for i, row in ipairs(data) do
	grid:insertRow(20)  -- insertRow does NOT return an index
	local rowIdx = grid:getRowCount() - 1

	-- Name column
	local nameCell = Static.new()
	nameCell:setText(row.name)
	grid:setCell(0, rowIdx, nameCell)

	-- Latitude column
	local latCell = Static.new()
	latCell:setText(row.lat)
	grid:setCell(1, rowIdx, latCell)

	-- Longitude column
	local lonCell = Static.new()
	lonCell:setText(row.lon)
	grid:setCell(2, rowIdx, lonCell)
end
```

### Example 8: Dynamic Grid Resizing

Adjust grid height based on number of rows and reposition controls below:

```lua
local DialogLoader = require("DialogLoader")

local window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")
local grid = DialogLoader.findWidgetByName(window, "dataGrid")
local button = DialogLoader.findWidgetByName(window, "actionButton")
local textBox = DialogLoader.findWidgetByName(window, "outputText")

-- Populate grid with variable number of items
local data = {"Item 1", "Item 2", "Item 3", "Item 4", "Item 5"}

for i, text in ipairs(data) do
	grid:insertRow(20)  -- 20px row height; insertRow does NOT return an index
	local rowIdx = grid:getRowCount() - 1
	local cell = Static.new()
	cell:setText(text)
	grid:setCell(0, rowIdx, cell)
end

-- Resize grid to fit content
local rowCount = #data
local headerHeight = 20
local rowHeight = 20
local gridHeight = headerHeight + (rowCount * rowHeight)
local gridX, gridY = 0, 48
local gridWidth = 460

grid:setBounds(gridX, gridY, gridWidth, gridHeight)

-- Reposition controls below the grid
local buttonY = gridY + gridHeight + 12
button:setBounds(0, buttonY, 140, 20)

local textY = buttonY + 20 + 12
local textHeight = 160
textBox:setBounds(0, textY, gridWidth, textHeight)
```

### Example 9: Window Lifecycle Management

```lua
local DialogLoader = require("DialogLoader")

local MyDialog = {}
MyDialog.window = nil

function MyDialog.show()
	if MyDialog.window then
		MyDialog.window:setVisible(true)
		return
	end

	-- Create window
	MyDialog.window = DialogLoader.spawnDialogFromFile("MyDialog.dlg")

	-- Set up close handler
	local closeButton = DialogLoader.findWidgetByName(MyDialog.window, "closeButton")
	closeButton:addMouseDownCallback(function()
		MyDialog.hide()
	end)

	-- Escape key to close
	MyDialog.window:addHotKeyCallback('escape', function()
		MyDialog.hide()
	end)

	MyDialog.window:setVisible(true)
end

function MyDialog.hide()
	if MyDialog.window then
		MyDialog.window:setVisible(false)
	end
end

function MyDialog.destroy()
	if MyDialog.window then
		MyDialog.window:kill()
		MyDialog.window = nil
	end
end

-- Usage
MyDialog.show()
```

---

## Best Practices

### 1. Use pcall() for Safety

Always wrap UI operations in `pcall()` to prevent crashes:

```lua
local success, err = pcall(function()
	-- UI operations here
end)
if not success then
	print("Error: " .. tostring(err))
end
```

### 2. Template Controls for Dynamic Content

Create invisible template widgets and clone them for dynamic content:

```lua
-- In .dlg file

["itemTemplate"] = {
	["type"] = "Static",
	["params"] = {
		["bounds"] = { ["x"] = 0, ["y"] = 0, ["w"] = 200, ["h"] = 25 },
		["visible"] = false,  -- Hidden template
	},
}

-- In .lua file
local template = DialogLoader.findWidgetByName(window, "itemTemplate")
local newItem = template:clone()
newItem:setText("New item")
newItem:setVisible(true)
```

### 3. Keyboard Input Locking

Lock keyboard input when text fields have focus to prevent game controls from interfering:

```lua
local Input = require("Input")
local keyboardLocked = false

local function lockKeyboard()
	if not keyboardLocked then
		local keyboardEvents = Input.getDeviceKeys(Input.getKeyboardDeviceName())
		DCS.lockKeyboardInput(keyboardEvents)
		keyboardLocked = true
	end
end

local function unlockKeyboard()
	if keyboardLocked then
		DCS.unlockKeyboardInput(true)
		keyboardLocked = false
	end
end

editBox:addFocusCallback(function(self)
	if self:getFocused() then
		lockKeyboard()
	else
		unlockKeyboard()
	end
end)
```

### 4. State Tracking to Prevent Recursion

Use flags to prevent recursive event handlers:

```lua
local updating = false
widget.onChange = function(self)
	if updating then return end
	updating = true
	-- Make changes that trigger onChange
	updating = false
end
```

### 5. Store Original Skins

Save original skins before modifying to allow restoration:

```lua
local originalSkin = widget:getSkin()
-- Modify appearance
widget:setSkin(modifiedSkin)
-- Later restore
widget:setSkin(originalSkin)
```

### 6. Z-Order for Overlays

Use `setZOrder()` to control overlay stacking at runtime:

```lua
window:setZOrder(100)  -- Higher = on top
```

### 7. Screen Size Detection

Get screen dimensions for proper positioning:

```lua
local screenWidth, screenHeight = dxgui.GetScreenSize()  -- monitor resolution
-- Or for the DCS window size (handles windowed vs fullscreen):
local windowWidth, windowHeight = dxgui.GetWindowSize()
```

### 8. Clean Widget References

Remove callbacks and destroy widgets when no longer needed:

```lua
-- Remove widget from parent (Panel or Window)
parentPanel:removeWidget(widget)

-- Destroy window
window:kill()

-- Clear reference
widget = nil
```

### 9. Name All Important Widgets

Give important widgets stable keys under their parent `children` table:

```lua
["children"] = {
	["myWidget"] = {
		["type"] = "Static",
		["params"] = {
			-- other params
		},
	},
}
```

### 10. Use Bounds for Precise Layout

Set exact positions and sizes with `bounds` instead of relying on automatic layout:

```lua
["bounds"] = { ["x"] = 10, ["y"] = 10, ["w"] = 300, ["h"] = 30 }
```

### 11. Remember 0-Based Indexing

ComboList/ListBox items and Grid columns use 0-based indexing:

```lua
local firstItem = combo:getItem(0)  -- First item is index 0
grid:setCell(0, rowIndex, widget)  -- First column is index 0
```

### 12. Use :newItem() for ComboList

Prefer the simpler `:newItem()` method over creating ListBoxItem separately:

```lua
-- Preferred:
combo:newItem("Item text")

-- Also works but more verbose:
local item = ListBoxItem.new("Item text")
combo:insertItem(item)
```

### 13. Attach Custom Properties to Widgets

Store custom data directly on widgets for state tracking:

```lua
widget.myCustomValue = "something"
widget.myLookupTable = {}
-- Access in callbacks:
widget.onChange = function(self)
	local value = self.myCustomValue
end
```

### 14. Use Skin Toggling for Show/Hide

For overlays, consider using skin switching instead of just visibility:

```lua
local Skin = require("Skin")
local defaultSkin = window:getSkin()
local hiddenSkin = Skin.windowSkinChatMin()  -- Minimal skin

-- Hide by changing skin
window:setSkin(hiddenSkin)
window:setHasCursor(false)

-- Show by restoring skin
window:setSkin(defaultSkin)
window:setHasCursor(true)
```

---

## Quick Reference

### Essential Code Snippets

**Load Dialog:**
```lua
local window = DialogLoader.spawnDialogFromFile("path/to/dialog.dlg")
```

**Find Widget:**
```lua
local widget = DialogLoader.findWidgetByName(window, "widgetName")
```

**Show/Hide:**
```lua
window:setVisible(true)
window:setVisible(false)
```

**Set Text:**
```lua
widget:setText("New text")
```

**Add Click Handler:**
```lua
button:addMouseDownCallback(function(self)
	-- Handle click
end)
```

**Add Change Handler:**
```lua
widget.onChange = function(self)
	-- Handle change
end
```

**Screen Size:**
```lua
local w, h = dxgui.GetScreenSize()
```

**Clone Widget:**
```lua
local newWidget = template:clone()
```

**Create Item:**
```lua
local item = combo:newItem("Text")
```

**Get Item:**
```lua
local item = combo:getItem(0)  -- 0-based
```

**Clear List:**
```lua
combo:clear()
```

**Copy to Clipboard:**
```lua
dxgui.CopyTextToClipboard("text")
```

**Lock Keyboard:**
```lua
local Input = require("Input")
local events = Input.getDeviceKeys(Input.getKeyboardDeviceName())
DCS.lockKeyboardInput(events)
```

### Common Patterns

**Center Window on Screen:**
```lua
local sw, sh = dxgui.GetScreenSize()
local w, h = window:getSize()
window:setPosition((sw - w) / 2, (sh - h) / 2)
```

**Toggle Visibility with Hotkey:**
```lua
local visible = true
window:addHotKeyCallback('Ctrl+Shift+H', function()
	visible = not visible
	window:setVisible(visible)
end)
```

**Populate ComboList (Simpler Method):**
```lua
combo:clear()
for i, text in ipairs(options) do
	combo:newItem(text)
end
-- Select first item (0-based index)
local firstItem = combo:getItem(0)
if firstItem then
	combo:selectItem(firstItem)
end
```

**Copy to Clipboard:**
```lua
dxgui.CopyTextToClipboard("Text to copy")
```

**Lock Keyboard Input:**
```lua
local Input = require("Input")
local events = Input.getDeviceKeys(Input.getKeyboardDeviceName())
DCS.lockKeyboardInput(events)
-- Later unlock:
DCS.unlockKeyboardInput(true)
```

**Safe Operation:**
```lua
pcall(function()
	-- UI code here
end)
```

### Reference Files

**DCS World UI Examples:**
- `Scripts/UI/GameMenu.dlg` / `GameMenu.lua` - Complete dialog example
- `Scripts/UI/gameMessages.lua` - Message overlay system
- `Scripts/UI/DebugSight.lua` - Simple overlay positioning
- `Scripts/UI/BannersIngameOverlay.dlg` - In-game overlay example
- `Scripts/UI/ConsoleDialog.dlg` - Complex dialog with multiple controls

**DCSAutoMate Implementation:**
- `Scripts/DCSAutoMate/DCSAutoMateMonitorWindow.dlg` - Custom in-game UI
- `Scripts/Hooks/DCSAutoMateHook.lua` - Complete implementation with dynamic content, keyboard management, and network communication

### Color Reference

| Color | Hex Value |
|-------|-----------|
| White | `0xffffffff` |
| Black | `0x000000ff` |
| Red | `0xff0000ff` |
| Green | `0x00ff00ff` |
| Blue | `0x0000ffff` |
| Yellow | `0xffff00ff` |
| Cyan | `0x00ffffff` |
| Magenta | `0xff00ffff` |
| Gray 50% | `0x808080ff` |
| Transparent | `0x00000000` |
| Semi-transparent White | `0xffffff80` |

---

## Troubleshooting

### Widget Not Found

**Problem:** `DialogLoader.findWidgetByName()` returns `nil`

**Solutions:**
- Verify the widget is keyed under the parent `children` table with the name you’re searching for
- Check spelling and case sensitivity
- Ensure widget is child of window (check `children` hierarchy)

### Text Not Displaying

**Problem:** Text appears blank or wrong color

**Solutions:**
- Check skin `text.color` is not transparent (`0x00000000`)
- Verify font size is appropriate for widget bounds
- Ensure widget bounds are large enough for text
- Check `text` parameter is set

### Events Not Firing

**Problem:** Callbacks not being called

**Solutions:**
- Verify widget is `enabled = true`
- Check widget is `visible = true`
- Ensure callback is added after widget is found
- Use correct callback method for control type

### Window Not Appearing

**Problem:** Window doesn't show after `setVisible(true)`

**Solutions:**
- Check bounds are within screen coordinates
- Verify `zOrder` is appropriate (higher = on top)
- Ensure no parent container is hidden
- Check window was successfully loaded (not `nil`)

---

## Additional Resources

### Official DCS World UI Files

Study these files in `DCS World/Scripts/UI/` for examples:
- Dialog definitions (`.dlg` files)
- Script implementations (`.lua` files)
- Skin definitions (`Skin/` directory)

### DCSAutoMate Implementation

See working examples in DCSAutoMate:
- `Scripts/DCSAutoMate/DCSAutoMateMonitorWindow.dlg` - Dialog definition
- `Scripts/Hooks/DCSAutoMateHook.lua` - Complete implementation

### Development Workflow

1. Create `.dlg` file with basic structure
2. Load in game and verify appearance
3. Add Lua script to manipulate controls
4. Test event handlers and callbacks
5. Refine layout and styling
6. Add error handling with `pcall()`

---

*Last Updated: February 10, 2026*
