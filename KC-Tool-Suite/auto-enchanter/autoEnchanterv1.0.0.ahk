; Auto Enchanter by Riri
;
; MIT License
;
; Copyright (c) 2025 Riri <https://github.com/AlinaWan>
;
; Permission is hereby granted, free of charge, to any person obtaining a copy
; of this software and associated documentation files (the "Software"), to deal
; in the Software without restriction, including without limitation the rights
; to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
; copies of the Software, and to permit persons to whom the Software is
; furnished to do so, subject to the following conditions:
;
; The above copyright notice and this permission notice shall be included in all
; copies or substantial portions of the Software.
;
; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
; OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
; SOFTWARE.

#Persistent
Gui, +AlwaysOnTop
Gui, Font, s10, Segoe UI

; Enchantment data. Each entry is [Color (string), Enabled_Checkbox_State (boolean)]
stopConditions := {}
stopConditions["Chrono"] := ["0xFA9B3C", false]
stopConditions["Wumbo"] := ["0x35E6E9", false]
stopConditions["Strong"] := ["0xFA4E5F", false]
stopConditions["Storming"] := ["0xE9BF5E", false]
stopConditions["Sundering"] := ["0x6868FD", false]
stopConditions["Lucky"] := ["0x72FD5D", false]
stopConditions["Abundant"] := ["0xBE50E9", false]
stopConditions["Altered"] := ["0x71EA7B", false]
stopConditions["Bulky"] := ["0xD7AEFA", false]
stopConditions["Noir"] := ["0x979797", false]
stopConditions["Prodigy"] := ["0x76FA46", false]
stopConditions["Scrapper"] := ["0xFAA753", false]
stopConditions["Sparkled"] := ["0xFAF4B6", false]
stopConditions["Swift"] := ["0x9DD8FD", false]

; --- Paging Setup ---
EnchantsPerPage := 6
currentPage := 1
EnchantPages := []

; Custom order for the beginning of the list
customOrderInitial := ["Chrono", "Wumbo", "Strong", "Storming", "Sundering", "Lucky"]

allEnchants := []

; First add enchantss in the custom predefined order
for _, name in customOrderInitial {
    if stopConditions.HasKey(name) {
        allEnchants.Push(name)
    }
}

; Then add all other enchants that are not in the custom list, sorted alphabetically
restEnchants := []
for name, _ in stopConditions {
    isCustom := false
    for _, customName in customOrderInitial {
        if (customName = name) {
            isCustom := true
            break
        }
    }
    if (!isCustom) {
        restEnchants.Push(name)
    }
}
restEnchants.Sort() ; Sort the remaining Enchants alphabetically

; Append the alphabetically sorted rest to the custom ordered ones
for _, name in restEnchants {
    allEnchants.Push(name)
}

pageCount := Ceil(allEnchants.Length() / EnchantsPerPage)
if (pageCount < 1)
    pageCount := 1

Loop, % pageCount
{
    startIdx := (A_Index - 1) * EnchantsPerPage + 1
    endIdx := Min(A_Index * EnchantsPerPage, allEnchants.Length())
    pageEnchants := []
    Loop, % (endIdx - startIdx + 1)
        pageEnchants.Push(allEnchants[startIdx + A_Index - 1])
    EnchantPages.Push(pageEnchants)
}
; --- END Paging Setup ---

; GUI Setup
#NoEnv
#SingleInstance Force
SetBatchLines -1
SetTitleMatchMode, 2
SendMode Input

clickDelay := 1200
colorTolerance := 4
pollingInterval := 100
clicking := false
step := 0
guiInitialized := false ; Flag to track GUI initialization
mode := "Or" ; Default mode: "Or"

inclusionsFile := A_ScriptDir "\inclusions.ini"
inclusionZones := []

Gui, +AlwaysOnTop
Gui, Margin, 10, 10
Gui, Font, s10, Segoe UI

Gui, Add, Tab2, x20 y15 w330 h250 vMainTab, Main|Target|Inclusions|Debug

Gui, Tab, Main
Gui, Add, Text, x30 y50, Key Hold Time (ms):
Gui, Add, Edit, vDelayEdit x150 y48 w100, %clickDelay%
Gui, Add, Button, gSetDelay x255 y47 w90, Set Delay

Gui, Add, Text, x30 y80, Tolerance (0-255):
Gui, Add, Edit, vToleranceEdit x150 y78 w100, %colorTolerance%
Gui, Add, Button, gSetTolerance x255 y77 w90, Set Tolerance

Gui, Add, Text, x30 y110, Polling Interval (ms):
Gui, Add, Edit, vPollingIntervalEdit x150 y108 w100, %pollingInterval%
Gui, Add, Button, gSetPollingInterval x255 y107 w90, Set Interval

Gui, Add, Text, x30 y140, Stop Condition Mode:
Gui, Add, Radio, x180 y140 vOrMode gSetMode Checked Group, OR

Gui, Add, Button, gGitHubRepository x105 y170 w150, GitHub Repository

Gui, Add, Text, vWarningText x30 y210, Rainbow objects may false-trigger stop
Gui, Add, Text, vStatusText x30 y230, F6: Toggle | Status: Suspended

Gui, Tab, Debug
Gui, Add, Edit, vDebugLog x30 y50 w300 h200 ReadOnly -WantReturn

Gui, Tab, Inclusions
Gui, Add, ListBox, vInclusionList x30 y50 w300 h150
Gui, Add, Button, gAddInclusion x30 y200 w140, Add Inclusion
Gui, Add, Button, gRemoveInclusion x190 y200 w140, Remove Inclusion
Gui, Add, Button, gStartDragSelection x30 y230 w300,  Drag to Select Zone

Gui, Tab, Target
Gui, Font, s10, Segoe UI
Gui, Add, GroupBox, x30 y40 w310 h175 vEnchantGroupBox

yBaseControls := 60
slotControls := []

; Create all possible Checkbox and Edit controls at once, but hide them initially.
totalPossibleSlots := allEnchants.Length()

Loop, % totalPossibleSlots
{
    idx := A_Index
    EnchantName := allEnchants[idx] ; Get the Enchant name for this absolute index
    cbVar := "Stop_Enchant_CB_" . idx
    colorVar := "Color_Enchant_Edit_" . idx

    ; Get the initial state and color from stopConditions
    initialChecked := stopConditions[EnchantName][2]
    initialColor := SubStr(stopConditions[EnchantName][1], 3) ; Remove "0x" for display

    checkboxOptions := "v" . cbVar . " x-100 y-100 w150 gCheckboxClicked Hidden"
    if (initialChecked) {
        checkboxOptions .= " Checked"
    }
    Gui, Add, Checkbox, %checkboxOptions%, %EnchantName%

    Gui, Add, Edit, v%colorVar% x-100 y-100 w80 Hidden, %initialColor%
    slotControls.Push({Checkbox: cbVar, Edit: colorVar})
}

guiWidthTab := 330
buttonWidth := 60
buttonPadding := 10

initialPaginationY := 50 + 175 + 5
initialPageTextY := initialPaginationY + 5

prevButtonX := 20 + buttonPadding
nextButtonX := 20 + guiWidthTab - buttonWidth - buttonPadding

; Calculate X position for centered page text
pageTextWidth := 100
pageTextX := 20 + (guiWidthTab / 2) - (pageTextWidth / 2)

Gui, Add, Button, gPrevPage x%prevButtonX% y%initialPaginationY% w%buttonWidth%, Prev
Gui, Add, Button, gNextPage x%nextButtonX% y%initialPaginationY% w%buttonWidth%, Next
Gui, Add, Text, x%pageTextX% y%initialPageTextY% w%pageTextWidth% Center vPageText, Page 1 of %pageCount%

calculatedInitialHeight := 270

Gui, Show, w370 h%calculatedInitialHeight%, Auto Enchanter by Riri

DrawEnchantPage(currentPage) ; Initial call to draw the first page
guiInitialized := true ; Set flag to true AFTER initial draw

LoadInclusions()
SetTimer, CheckRobloxFocus, %pollingInterval%
Log("Script started.")
UpdateStatusBar() ; Initial status bar update
return

GitHubRepository:
Run, https://github.com/AlinaWan/kc-dig-tool-configs/tree/main/KC-Tool-Suite/auto-enchanter
return

; --- Functions ---

DrawEnchantPage(pageNum)
{
    global EnchantPages, stopConditions, slotControls, EnchantsPerPage, currentPage, pageCount, yBaseControls, guiWidthTab, buttonWidth, buttonPadding, pageTextWidth, allEnchants, guiInitialized

    Gui, Tab, Target
    GuiControl,, PageText, % "Page " . pageNum . " of " . pageCount

    ; Hide ALL controls before drawing the current page's controls
    for _, controls in slotControls {
        GuiControl, Hide, % controls.Checkbox
        GuiControl, Hide, % controls.Edit
    }
    ; Ensure pagination controls are also hidden and then re-shown in the correct place
    GuiControl, Hide, PrevPage
    GuiControl, Hide, NextPage
    GuiControl, Hide, PageText


    Enchants := EnchantPages[pageNum]
    if (!IsObject(Enchants))
        Enchants := []

    ; Start Y position for the first actual Enchant control row
    currentDisplayY := yBaseControls

    Loop, % Enchants.Length()
    {
        idxOnPage := A_Index ; Index within the current page (1 to EnchantsPerPage)
        EnchantName := Enchants[idxOnPage]

        ; Find the absolute index in the entire allEnchants list
        absoluteEnchantIndex := ""
        for i, mName in allEnchants {
            if (mName = EnchantName) {
                absoluteEnchantIndex := i
                break
            }
        }

        if (absoluteEnchantIndex = "") {
            Log("Error: Could not find Enchantment " . EnchantmentName . " in allEnchants list.")
            continue
        }

        ; Retrieve the specific slot control set for this absolute index
        slot := slotControls[absoluteEnchantIndex]

        cbVar := slot.Checkbox
        colorVar := slot.Edit

        ; Calculate the Y position for this control on the current page view
        rowY := yBaseControls + 25 * (idxOnPage - 1)
        colorEditY := rowY - 5 ; Calculate adjusted Y for the color edit box

        ; Move controls to their correct X and Y position (relative to the GUI, so add Tab's X offset)
        GuiControl, Move, %cbVar%, x45 y%rowY%
        GuiControl, Move, %colorVar%, x205 y%colorEditY% ; Use the adjusted Y variable

        ; Set checkbox label and state
        GuiControl, , %cbVar%, %EnchantName%
        GuiControl, % (stopConditions[EnchantName][2] ? "Check" : "UnCheck"), %cbVar%

        ; Set edit control value (remove "0x" prefix for display)
        GuiControl, , %colorVar%, % SubStr(stopConditions[EnchantName][1], 3)

        ; Show the controls for the current Enchant
        GuiControl, Show, %cbVar%
        GuiControl, Show, %colorVar%
    }

    ; Reposition pagination buttons and text below the visible items
    newPaginationY := 225 + 5 ; GroupBox bottom + small margin
    newPageTextY := newPaginationY + 5

    prevButtonX_dynamic := 20 + buttonPadding
    nextButtonX_dynamic := 20 + guiWidthTab - buttonWidth - buttonPadding
    pageTextX_dynamic := 20 + (guiWidthTab / 2) - (pageTextWidth / 2)

    ; Use GuiControl, Move to bring them into view at their new positions
    GuiControl, Move, PrevPage, x%prevButtonX_dynamic% y%newPaginationY%
    GuiControl, Move, NextPage, x%nextButtonX_dynamic% y%newPaginationY%
    GuiControl, Move, PageText, x%pageTextX_dynamic% y%newPageTextY%

    ; Make them visible after moving them
    GuiControl, Show, PrevPage
    GuiControl, Show, NextPage
    GuiControl, Show, PageText

    currentPage := pageNum
}

SaveCurrentPageSettings()
{
    global currentPage, EnchantPages, stopConditions, EnchantsPerPage, slotControls, allEnchants

    ; If the GUI isn't fully initialized yet, we can't save from it, just return.
    ; This handles the very first startup case where controls are empty.
    if (!guiInitialized)
        return

    EnchantsOnCurrentPage := EnchantPages[currentPage]
    if (!IsObject(EnchantsOnCurrentPage))
        return

    Loop, % EnchantsOnCurrentPage.Length()
    {
        idxOnPage := A_Index
        EnchantName := EnchantsOnCurrentPage[idxOnPage]

        ; Calculate the absolute index to find the correct unique variable names
        absoluteEnchantIndex := ""
        for i, mName in allEnchants {
            if (mName = EnchantName) {
                absoluteEnchantIndex := i
                break
            }
        }
        if (absoluteEnchantIndex = "")
            continue

        slot := slotControls[absoluteEnchantIndex]

        cbVar := slot.Checkbox
        colorVar := slot.Edit

        GuiControlGet, checked, , %cbVar%
        GuiControlGet, color, , %colorVar%

        stopConditions[EnchantName][2] := (checked = 1)
        ; Clean and validate color input more robustly
        color := Trim(color) ; Remove leading/trailing whitespace
        color := RegExReplace(color, "[^0-9a-fA-F]") ; Remove any non-hex characters

        ; Validate color input: must be exactly 6 hex characters
        if (StrLen(color) = 6 && RegExMatch(color, "i)^[0-9a-fA-F]{6}$"))
            stopConditions[EnchantName][1] := "0x" . color
        else
            Log("Invalid color for " . EnchantName . ": '" . color . "'. Color not updated.")
    }
}

; --- Button handlers ---
PrevPage:
    ; Save settings of the *current* page before moving to the previous one
    SaveCurrentPageSettings()
    if (currentPage > 1)
    {
        currentPage--
        DrawEnchantPage(currentPage)
    }
return

NextPage:
    ; Save settings of the *current* page before moving to the next one
    SaveCurrentPageSettings()
    if (currentPage < pageCount)
    {
        currentPage++
        DrawEnchantPage(currentPage)
    }
return

CheckboxClicked:
    ; No immediate action needed here.
    ; The state of the checkbox will be correctly read
    ; either when the page changes (via SaveCurrentPageSettings)
    ; or by the CheckRobloxFocus timer.
return

SetMode:
    global mode
    mode := "Or"
    Log("Stop condition mode set to: " mode)
return

LoadInclusions() {
    global inclusionZones, inclusionsFile
    inclusionZones := []
    if !FileExist(inclusionsFile)
        return
    Loop, Read, %inclusionsFile%
    {
        rawLine := A_LoopReadLine
        line := Trim(rawLine)
        line := RegExReplace(line, "\s")

        if (line = "")
            continue

        parts := StrSplit(line, ",")
        valid := (parts.Length() = 4)
        if (valid) {
            for part in parts {
                if !RegExMatch(part, "^\d+$") {
                    valid := false
                    break
                }
            }
        }

        if (valid)
            inclusionZones.Push(line)
        else
            Log("Skipped invalid line: [" . rawLine . "] cleaned to [" . line . "]")
    }
    Log("Loaded inclusions: " . (inclusionZones.MaxIndex() ? StrJoin(", ", inclusionZones) : "(none)"))
    UpdateInclusionListBox()
}

SaveInclusions() {
    global inclusionZones, inclusionsFile
    FileDelete, %inclusionsFile%
    Loop % inclusionZones.MaxIndex() {
        line := inclusionZones[A_Index]
        if (line != "" && RegExMatch(line, "^\d+,\d+,\d+,\d+$"))
            FileAppend, % line . "`n", %inclusionsFile%
    }
}

UpdateInclusionListBox() {
    global inclusionZones
    GuiControl,, InclusionList, |
    for index, zone in inclusionZones
        GuiControl,, InclusionList, %zone%
    GuiControl, +Redraw, InclusionList
    GuiControl, Choose, InclusionList, 1
}

AddInclusion:
    ShowInclusionInput()
return

RemoveInclusion:
    global inclusionZones
    GuiControlGet, selectedItem, , InclusionList
    if (selectedItem = "") {
        MsgBox, 48, No Selection, Please select an inclusion zone to remove.
        return
    }
    indexToRemove := ""
    Loop, % inclusionZones.MaxIndex() {
        if (inclusionZones[A_Index] = selectedItem) {
            indexToRemove := A_Index
            break
        }
    }
    if (indexToRemove != "") {
        inclusionZones.RemoveAt(indexToRemove)
        Log("Removed inclusion zone: " selectedItem)
        SaveInclusions()
        UpdateInclusionListBox()
    }
return

ShowInclusionInput() {
    Gui, InclusionInput:New, +AlwaysOnTop +Owner +Resize, Add Inclusion Zone
    Gui, Font, s10, Segoe UI

    Gui, Add, Text, x10 y15, Top-Left (X1,Y1):
    Gui, Add, Edit, vXY1Edit w125 h22 x140 y15

    Gui, Add, Text, x10 y50, Bottom-Right (X2,Y2):
    Gui, Add, Edit, vXY2Edit w125 h22 x140 y50

    Gui, Add, Button, gConfirmInclusion x60 y90 w70 h25, OK
    Gui, Add, Button, gCancelInclusion x150 y90 w70 h25, Cancel

    Gui, Show,, Add Inclusion Zone
}

ConfirmInclusion:
    global inclusionZones
    Gui, InclusionInput:Submit, NoHide
    Input1 := XY1Edit
    Input2 := XY2Edit

    Input1 := RegExReplace(Input1, "\s+")
    Input2 := RegExReplace(Input2, "\s+")

    if (Input1 = "" || Input2 = "") {
        MsgBox, 48, Invalid Input, Please enter both coordinate pairs.
        return
    }

    if (!RegExMatch(Input1, "^\d+,\d+$") || !RegExMatch(Input2, "^\d+,\d+$")) {
        MsgBox, 48, Invalid Input, Coordinates must be in format: X,Y (numbers only).
        return
    }

    arr1 := StrSplit(Input1, ",")
    arr2 := StrSplit(Input2, ",")

    if (arr1.Length() != 2 || arr2.Length() != 2) {
        MsgBox, 48, Invalid Input, Coordinates missing numbers.
        return
    }

    x1 := arr1[1] + 0
    y1 := arr1[2] + 0
    x2 := arr2[1] + 0
    y2 := arr2[2] + 0

    X := (x1 < x2) ? x1 : x2
    Y := (y1 < y2) ? y1 : y2
    Width := Abs(x2 - x1)
    Height := Abs(y2 - y1)

    if (Width = 0 || Height = 0) {
        MsgBox, 48, Invalid Input, The inclusion zone must have non-zero width and height.
        return
    }

    newZone := X "," Y "," Width "," Height
    inclusionZones.Push(newZone)
    Log("Adding inclusion zone: " newZone)
    SaveInclusions()
    UpdateInclusionListBox()
    Gui, InclusionInput:Destroy
    Reload ; reload to update listbox
return

CancelInclusion:
    Gui, InclusionInput:Destroy
return

SetDelay:
    Gui, Submit, NoHide
    if RegExMatch(DelayEdit, "^\d+$") && DelayEdit > 0 {
        clickDelay := DelayEdit + 0
        Log("Click delay set to: " clickDelay " ms")
    } else {
        clickDelay := 100
        GuiControl,, DelayEdit, %clickDelay%
        Log("Invalid delay entered. Reverting to default: 100 ms")
    }
return

SetTolerance:
    Gui, Submit, NoHide
    if RegExMatch(ToleranceEdit, "^\d+$") && ToleranceEdit >= 0 && ToleranceEdit <= 255 {
        colorTolerance := ToleranceEdit + 0
        Log("Color tolerance set to: " colorTolerance)
    } else {
        colorTolerance := 10
        GuiControl,, ToleranceEdit, %colorTolerance%
        Log("Invalid tolerance entered. Reverting to default: 10")
    }
return

SetPollingInterval:
    global pollingInterval
    Gui, Submit, NoHide
    if RegExMatch(PollingIntervalEdit, "^\d+$") && PollingIntervalEdit > 0 {
        pollingInterval := PollingIntervalEdit + 0
        SetTimer, CheckRobloxFocus, %pollingInterval%
        Log("Polling interval set to: " pollingInterval " ms")
    } else {
        pollingInterval := 100
        GuiControl,, PollingIntervalEdit, %pollingInterval% ; Update GUI to reflect default
        Log("Invalid polling interval entered. Reverting to default: 100 ms")
    }
return

; Toggle clicking loop with F6
F6::ToggleClicking()

ToggleClicking() {
    global clicking
    if (!clicking) {
        if !FocusRoblox() {
            clicking := false
            GuiControl,, StatusText, Status: Suspended
            UpdateStatusBar()
            return
        }
    }
    clicking := !clicking
    UpdateStatusBar() ; Update status bar immediately after toggling

    if (clicking) {
        SetTimer, doEnchant, 1
        Log("Enchanting started.")
    } else {
        SetTimer, doEnchant, Off
        Log("Enchanting stopped.")
    }
}

doEnchant:
    Send {e down}
    Sleep, clickDelay
    Send {e up}
    Sleep, 100 ; Give the screen a moment to update after enchanting
return

FocusRoblox() {
    if WinExist("ahk_exe RobloxPlayerBeta.exe") {
        WinActivate
        WinWaitActive, ahk_exe RobloxPlayerBeta.exe, , 1
        return true
    } else {
        MsgBox, 48, Roblox Not Found, RobloxPlayerBeta.exe is not currently running.
        Log("RobloxPlayerBeta.exe not found.")
        return false
    }
}

UpdateStatusBar() {
    global clicking, clickDelay, colorTolerance, pollingInterval, mode
    status := clicking ? "Running" : "Suspended"
    GuiControl,, StatusText, % "F6: Toggle | Status: " status ""
}

CheckRobloxFocus:
    global clicking, colorTolerance, inclusionZones, stopConditions, allEnchants, slotControls

    ; Pause if Roblox is not focused
    if (clicking && !WinActive("ahk_exe RobloxPlayerBeta.exe")) {
        clicking := false
        GuiControl,, StatusText, Status: Suspended
        UpdateStatusBar()
        SetTimer, doEnchant, Off
        Log("Suspended: Roblox lost focus")
        return
    }

    ; Do nothing if not currently clicking
    if (!clicking)
        return

    ; Refresh stopConditions from GUI state
    for EnchantName, data in stopConditions {
        absoluteEnchantIndex := ""
        for i, mName in allEnchants {
            if (mName = EnchantName) {
                absoluteEnchantIndex := i
                break
            }
        }
        if (absoluteEnchantIndex = "")
            continue

        slot := slotControls[absoluteEnchantIndex]
        cbVar := slot.Checkbox
        colorVar := slot.Edit

        GuiControlGet, checked, , %cbVar%
        GuiControlGet, color, , %colorVar%

        stopConditions[EnchantName][2] := (checked = 1)

        if (color != "") {
            color := Trim(color)
            color := RegExReplace(color, "[^0-9a-fA-F]")

            if (StrLen(color) = 6 && RegExMatch(color, "i)^[0-9a-fA-F]{6}$"))
                stopConditions[EnchantName][1] := "0x" . color
            else
                Log("Invalid color format in GUI for " . EnchantName . ": '" . color . "'. Not updating color.")
        } else if (stopConditions[EnchantName][2]) {
            Log("Color for " . EnchantName . " is empty in GUI. Using default or last valid color.")
        }
    }

    ; Loop through all active stop conditions and inclusion zones
    for title, data in stopConditions {
        if (!data[2]) ; If not enabled, skip
            continue

        color := data[1]

        for index, zone in inclusionZones {
            coords := StrSplit(zone, ",")
            zx := coords[1] + 0
            zy := coords[2] + 0
            zw := coords[3] + 0
            zh := coords[4] + 0

            PixelSearch, px, py, zx, zy, zx + zw, zy + zh, %color%, %colorTolerance%, RGB Fast

            if (!ErrorLevel) {
                Send {e up} ; force the e key up if it's currently holding it
                clicking := false
                GuiControl,, StatusText, Status: Suspended
                UpdateStatusBar()
                SetTimer, doEnchant, Off
                Log("Suspended: Detected " . title . " at " . px . "," . py . " within inclusion zone " . zone)
                return
            }
        }
    }
return

; ====== NEW DRAG-SELECTION FUNCTION ======
StartDragSelection:
    CoordMode, Mouse, Screen
    CoordMode, Gui, Screen

    Gui, Submit, NoHide ; Save current GUI state
    Gui, Hide ; Hide main window during selection

    ; Prompt user
    ToolTip, Click and drag to select an area. Press ESC to cancel.

    ; Wait for left mouse button press
    KeyWait, LButton, D
    MouseGetPos, dragX1, dragY1

    ; Create transparent drag rectangle
    Gui, DragBox:New, +ToolWindow -Caption +AlwaysOnTop +E0x20
    Gui, DragBox:Color, FF0000
    Gui, DragBox:Add, Text, x0 y0 w100 h100
    WinSet, Transparent, 50, DragBox

    ; Update rectangle while dragging
    while (GetKeyState("LButton", "P")) {
        MouseGetPos, dragX2, dragY2
        width := Abs(dragX2 - dragX1)
        height := Abs(dragY2 - dragY1)
        x := (dragX1 < dragX2) ? dragX1 : dragX2
        y := (dragY1 < dragY2) ? dragY1 : dragY2

        Gui, DragBox:Show, x%x% y%y% w%width% h%height% NA
        ; Check for escape key
        if GetKeyState("Escape", "P")
        {
            cancelled := true
            break
        }
        Sleep, 10 ; Reduce CPU usage
    }

    ; Cleanup
    Gui, DragBox:Destroy
    ToolTip

    ; Cancel if ESC was pressed
    if (cancelled) {
        Gui, Show
        Reload
        return
    }

    ; Save the new zone
    newZone := x "," y "," width "," height
    inclusionZones.Push(newZone)
    SaveInclusions()
    UpdateInclusionListBox()
    Gui, Show
    Reload ; reload to update listbox
return
; ====== END DRAG-SELECTION CODE ======

GuiClose:
    SetTimer, CheckRobloxFocus, Off
    ExitApp

Log(msg) {
    GuiControlGet, currentLog, , DebugLog
    FormatTime, timeStr,, HH:mm:ss
    ; Prepend new message to keep latest at top
    newLog := "[" timeStr "] " msg "`n" currentLog
    ; Keep log from growing excessively large, trim from the bottom (oldest entries)
    if (StrLen(newLog) > 3000)
        newLog := SubStr(newLog, 1, 3000)
    GuiControl,, DebugLog, %newLog%
    ; Force scroll to top (to show latest message)
    SendMessage, 0x115, 0, 0, DebugLog ; WM_VSCROLL SB_TOP (0 = SB_TOP)
}

; Helper: Join strings with delimiter
StrJoin(delim, arr) {
    local result := ""
    for index, value in arr
        result .= (index=1 ? "" : delim) . value
    return result
}
