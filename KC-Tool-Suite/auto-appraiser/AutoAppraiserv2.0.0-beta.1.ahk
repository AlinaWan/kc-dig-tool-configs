; Auto Appraiser by Riri
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

; Mutation data. Each entry is [Color (string), Enabled_Checkbox_State (boolean)]
stopConditions := {}
stopConditions["Shiny"] := ["0xFFF587", true]
stopConditions["Gargantuan"] := ["0x93FF40", false]
stopConditions["Titanic"] := ["0x93FF40", false]
stopConditions["Gigantic"] := ["0xB5FF78", false]
stopConditions["Big"] := ["0xC6FFA2", false]
stopConditions["Small"] := ["0xFFBBBB", false]
stopConditions["Tiny"] := ["0xFF8989", false]
stopConditions["Microscopic"] := ["0xFF5050", false]
stopConditions["Awkward"] := ["0x92D847", false]
stopConditions["Chromatic"] := ["0xFF007B", false]
stopConditions["Dark"] := ["0x4F4F4F", false]
stopConditions["Electric"] := ["0xF9D95B", false]
stopConditions["Fossilized"] := ["0xFFFFFF", false] ; needs color
stopConditions["Galactic"] := ["0xFFFFFF", false] ; needs color
stopConditions["Glossy"] := ["0x67DCF5", false]
stopConditions["Golden"] := ["0xFFFFFF", false] ; needs color
stopConditions["Iridescent"] := ["0xFFB7D3", false]
stopConditions["Marbled"] := ["0xCCC3A1", false]
stopConditions["Neon"] := ["0xFFFFFF", false] ; needs color
stopConditions["Noir"] := ["0xFFFFFF", false] ; needs color
stopConditions["Petrified"] := ["0xFFCD8F", false]
stopConditions["Rusty"] := ["0x83594E", false]
stopConditions["Silver"] := ["0xC1D7FF", false]
stopConditions["Transparent"] := ["0xAAFFED", false]
stopConditions["Venomous"] := ["0xFFFFFF", false] ; needs color

; --- Paging Setup ---
mutationsPerPage := 6
currentPage := 1
mutationPages := []

; Custom order for the beginning of the list
customOrderInitial := ["Shiny", "Gargantuan", "Titanic", "Gigantic", "Big", "Small", "Tiny", "Microscopic"]

allMutations := []

; First add mutations in the custom predefined order
for _, name in customOrderInitial {
    if stopConditions.HasKey(name) {
        allMutations.Push(name)
    }
}

; Then add all other mutations that are not in the custom list, sorted alphabetically
restMutations := []
for name, _ in stopConditions {
    isCustom := false
    for _, customName in customOrderInitial {
        if (customName = name) {
            isCustom := true
            break
        }
    }
    if (!isCustom) {
        restMutations.Push(name)
    }
}
restMutations.Sort() ; Sort the remaining mutations alphabetically

; Append the alphabetically sorted rest to the custom ordered ones
for _, name in restMutations {
    allMutations.Push(name)
}

pageCount := Ceil(allMutations.Length() / mutationsPerPage)
if (pageCount < 1)
    pageCount := 1

Loop, % pageCount
{
    startIdx := (A_Index - 1) * mutationsPerPage + 1
    endIdx := Min(A_Index * mutationsPerPage, allMutations.Length())
    pageMutations := []
    Loop, % (endIdx - startIdx + 1)
        pageMutations.Push(allMutations[startIdx + A_Index - 1])
    mutationPages.Push(pageMutations)
}
; --- END Paging Setup ---

; GUI Setup
#NoEnv
#SingleInstance Force
SetBatchLines -1
SetTitleMatchMode, 2
SendMode Input

clickDelay := 100
colorTolerance := 10
clicking := false
step := 0
guiInitialized := false ; Flag to track GUI initialization

exclusionsFile := A_ScriptDir "\exclusions.ini"
exclusionZones := []

Gui, +AlwaysOnTop
Gui, Margin, 10, 10
Gui, Font, s10, Segoe UI

Gui, Add, Tab2, x20 y15 w330 h250 vMainTab, Main|Target|Exclusions|Debug

Gui, Tab, Main
Gui, Add, Text, x30 y50, Click Delay (ms):
Gui, Add, Edit, vDelayEdit x150 y48 w100, %clickDelay%
Gui, Add, Button, gSetDelay x255 y47 w90, Set Delay

Gui, Add, Text, x30 y80, Tolerance (0-255):
Gui, Add, Edit, vToleranceEdit x150 y78 w100, %colorTolerance%
Gui, Add, Button, gSetTolerance x255 y77 w90, Set Tolerance

Gui, Add, Text, vWarningText x30 y210, Rainbow objects may false-trigger stop
Gui, Add, Text, vStatusText x30 y230, F6: Toggle | Status: Suspended

Gui, Tab, Debug
Gui, Add, Edit, vDebugLog x30 y50 w300 h200 ReadOnly -WantReturn

Gui, Tab, Exclusions
Gui, Add, ListBox, vExclusionList x30 y50 w300 h150
Gui, Add, Button, gAddExclusion x30 y200 w140, Add Exclusion
Gui, Add, Button, gRemoveExclusion x190 y200 w140, Remove Exclusion

Gui, Tab, Target
Gui, Font, s10, Segoe UI
Gui, Add, GroupBox, x30 y40 w310 h175 vMutationGroupBox

yBaseControls := 60
slotControls := []

; Create all possible Checkbox and Edit controls at once, but hide them initially.
totalPossibleSlots := allMutations.Length()

Loop, % totalPossibleSlots
{
    idx := A_Index
    mutationName := allMutations[idx] ; Get the mutation name for this absolute index
    cbVar := "Stop_Mutation_CB_" . idx
    colorVar := "Color_Mutation_Edit_" . idx

    ; Get the initial state and color from stopConditions
    initialChecked := stopConditions[mutationName][2]
    initialColor := SubStr(stopConditions[mutationName][1], 3) ; Remove "0x" for display

    checkboxOptions := "v" . cbVar . " x-100 y-100 w150 gCheckboxClicked Hidden"
    if (initialChecked) {
        checkboxOptions .= " Checked"
    }
    Gui, Add, Checkbox, %checkboxOptions%, %mutationName%

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

Gui, Show, w370 h%calculatedInitialHeight%, Auto Appraiser by Riri

DrawMutationPage(currentPage) ; Initial call to draw the first page
guiInitialized := true ; Set flag to true AFTER initial draw

LoadExclusions()
SetTimer, CheckRobloxFocus, 100
Log("Script started.")
return


; --- Functions ---

DrawMutationPage(pageNum)
{
    global mutationPages, stopConditions, slotControls, mutationsPerPage, currentPage, pageCount, yBaseControls, guiWidthTab, buttonWidth, buttonPadding, pageTextWidth, allMutations, guiInitialized

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


    mutations := mutationPages[pageNum]
    if (!IsObject(mutations))
        mutations := []

    ; Start Y position for the first actual mutation control row
    currentDisplayY := yBaseControls

    Loop, % mutations.Length()
    {
        idxOnPage := A_Index ; Index within the current page (1 to mutationsPerPage)
        mutationName := mutations[idxOnPage]

        ; Find the absolute index in the entire allMutations list
        absoluteMutationIndex := ""
        for i, mName in allMutations {
            if (mName = mutationName) {
                absoluteMutationIndex := i
                break
            }
        }

        if (absoluteMutationIndex = "") {
            Log("Error: Could not find mutation " . mutationName . " in allMutations list.")
            continue
        }

        ; Retrieve the specific slot control set for this absolute index
        slot := slotControls[absoluteMutationIndex]

        cbVar := slot.Checkbox
        colorVar := slot.Edit

        ; Calculate the Y position for this control on the current page view
        rowY := yBaseControls + 25 * (idxOnPage - 1)
        colorEditY := rowY - 5 ; Calculate adjusted Y for the color edit box

        ; Move controls to their correct X and Y position (relative to the GUI, so add Tab's X offset)
        GuiControl, Move, %cbVar%, x45 y%rowY%
        GuiControl, Move, %colorVar%, x205 y%colorEditY% ; Use the adjusted Y variable

        ; Set checkbox label and state
        GuiControl, , %cbVar%, %mutationName%
        GuiControl, % (stopConditions[mutationName][2] ? "Check" : "UnCheck"), %cbVar%

        ; Set edit control value (remove "0x" prefix for display)
        GuiControl, , %colorVar%, % SubStr(stopConditions[mutationName][1], 3)

        ; Show the controls for the current mutation
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
    global currentPage, mutationPages, stopConditions, mutationsPerPage, slotControls, allMutations

    ; If the GUI isn't fully initialized yet, we can't save from it, just return.
    ; This handles the very first startup case where controls are empty.
    if (!guiInitialized)
        return

    mutationsOnCurrentPage := mutationPages[currentPage]
    if (!IsObject(mutationsOnCurrentPage))
        return

    Loop, % mutationsOnCurrentPage.Length()
    {
        idxOnPage := A_Index
        mutationName := mutationsOnCurrentPage[idxOnPage]

        ; Calculate the absolute index to find the correct unique variable names
        absoluteMutationIndex := ""
        for i, mName in allMutations {
            if (mName = mutationName) {
                absoluteMutationIndex := i
                break
            }
        }
        if (absoluteMutationIndex = "")
            continue

        slot := slotControls[absoluteMutationIndex]

        cbVar := slot.Checkbox
        colorVar := slot.Edit

        GuiControlGet, checked, , %cbVar%
        GuiControlGet, color, , %colorVar%

        stopConditions[mutationName][2] := (checked = 1)
        ; Clean and validate color input more robustly
        color := Trim(color) ; Remove leading/trailing whitespace
        color := RegExReplace(color, "[^0-9a-fA-F]") ; Remove any non-hex characters

        ; Validate color input: must be exactly 6 hex characters
        if (StrLen(color) = 6 && RegExMatch(color, "i)^[0-9a-fA-F]{6}$"))
            stopConditions[mutationName][1] := "0x" . color
        else
            Log("Invalid color for " . mutationName . ": '" . color . "'. Color not updated.")
    }
}

; --- Button handlers ---
PrevPage:
    ; Save settings of the *current* page before moving to the previous one
    SaveCurrentPageSettings()
    if (currentPage > 1)
    {
        currentPage--
        DrawMutationPage(currentPage)
    }
return

NextPage:
    ; Save settings of the *current* page before moving to the next one
    SaveCurrentPageSettings()
    if (currentPage < pageCount)
    {
        currentPage++
        DrawMutationPage(currentPage)
    }
return

CheckboxClicked:
    ; No immediate action needed here.
    ; The state of the checkbox will be correctly read
    ; either when the page changes (via SaveCurrentPageSettings)
    ; or by the CheckRobloxFocus timer.
return

LoadExclusions() {
    global exclusionZones, exclusionsFile
    exclusionZones := []
    if !FileExist(exclusionsFile)
        return
    Loop, Read, %exclusionsFile%
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
            exclusionZones.Push(line)
        else
            Log("Skipped invalid line: [" . rawLine . "] cleaned to [" . line . "]")
    }
    Log("Loaded exclusions: " . (exclusionZones.MaxIndex() ? StrJoin(", ", exclusionZones) : "(none)"))
    UpdateExclusionListBox()
}

SaveExclusions() {
    global exclusionZones, exclusionsFile
    FileDelete, %exclusionsFile%
    Loop % exclusionZones.MaxIndex() {
        line := exclusionZones[A_Index]
        if (line != "" && RegExMatch(line, "^\d+,\d+,\d+,\d+$"))
            FileAppend, % line . "`n", %exclusionsFile%
    }
}

UpdateExclusionListBox() {
    global exclusionZones
    GuiControl,, ExclusionList, |
    for index, zone in exclusionZones
        GuiControl,, ExclusionList, %zone%
    GuiControl, +Redraw, ExclusionList
    GuiControl, Choose, ExclusionList, 1
}

AddExclusion:
    ShowExclusionInput()
return

RemoveExclusion:
    global exclusionZones
    GuiControlGet, selectedItem, , ExclusionList
    if (selectedItem = "") {
        MsgBox, 48, No Selection, Please select an exclusion zone to remove.
        return
    }
    indexToRemove := ""
    Loop, % exclusionZones.MaxIndex() {
        if (exclusionZones[A_Index] = selectedItem) {
            indexToRemove := A_Index
            break
        }
    }
    if (indexToRemove != "") {
        exclusionZones.RemoveAt(indexToRemove)
        Log("Removed exclusion zone: " selectedItem)
        SaveExclusions()
        UpdateExclusionListBox()
    }
return

ShowExclusionInput() {
    Gui, ExclusionInput:New, +AlwaysOnTop +Owner +Resize, Add Exclusion Zone
    Gui, Font, s10, Segoe UI

    Gui, Add, Text, x10 y15, Top-Left (X1,Y1):
    Gui, Add, Edit, vXY1Edit w125 h22 x140 y15

    Gui, Add, Text, x10 y50, Bottom-Right (X2,Y2):
    Gui, Add, Edit, vXY2Edit w125 h22 x140 y50

    Gui, Add, Button, gConfirmExclusion x60 y90 w70 h25, OK
    Gui, Add, Button, gCancelExclusion x150 y90 w70 h25, Cancel

    Gui, Show,, Add Exclusion Zone
}

ConfirmExclusion:
    global exclusionZones
    Gui, ExclusionInput:Submit, NoHide
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
        MsgBox, 48, Invalid Input, The exclusion zone must have non-zero width and height.
        return
    }

    newZone := X "," Y "," Width "," Height
    exclusionZones.Push(newZone)
    Log("Adding exclusion zone: " newZone)
    SaveExclusions()
    UpdateExclusionListBox()
    Gui, ExclusionInput:Destroy
    Reload ; reload to update listbox
return

CancelExclusion:
    Gui, ExclusionInput:Destroy
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
    UpdateStatusBar()
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
    GuiControl,, StatusText, % "Status: " (clicking ? "Running" : "Suspended")
    UpdateStatusBar()

    if (clicking) {
        SetTimer, DoClick, 1
        Log("Clicking started.")
    } else {
        SetTimer, DoClick, Off
        Log("Clicking stopped.")
    }
}

DoClick:
    Click
    MoveMouseInCircle()
    Sleep, clickDelay
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

MoveMouseInCircle() {
    global step
    step := Mod(step + 1, 4)
    if (step = 0)
        MouseMove, 0, -1, 0, R
    else if (step = 1)
        MouseMove, 1, 0, 0, R
    else if (step = 2)
        MouseMove, 0, 1, 0, R
    else if (step = 3)
        MouseMove, -1, 0, 0, R
}

UpdateStatusBar() {
    global clicking, clickDelay, colorTolerance
    status := clicking ? "Running" : "Suspended"
    GuiControl,, StatusText, % "F6: Toggle | Status: " status
}

CheckRobloxFocus:
    global clicking, colorTolerance, exclusionZones, stopConditions, allMutations, slotControls

    if (clicking && !WinActive("ahk_exe RobloxPlayerBeta.exe")) {
        clicking := false
        GuiControl,, StatusText, Status: Suspended
        UpdateStatusBar()
        SetTimer, DoClick, Off
        Log("Suspended: Roblox lost focus")
        return
    }

    if (!clicking)
        return

    ; Re-evaluate stop conditions from GUI to ensure current state is used
    for mutationName, data in stopConditions {
        ; Find the absolute index of this mutation to retrieve its GUI control names
        absoluteMutationIndex := ""
        for i, mName in allMutations {
            if (mName = mutationName) {
                absoluteMutationIndex := i
                break
            }
        }
        if (absoluteMutationIndex = "")
            continue

        slot := slotControls[absoluteMutationIndex]

        cbVar := slot.Checkbox
        colorVar := slot.Edit

        GuiControlGet, checked, , %cbVar%
        GuiControlGet, color, , %colorVar%

        stopConditions[mutationName][2] := (checked = 1) ; Update the state (index 1 in 0-based array)
        
        ; Only attempt to process if 'color' is not empty (e.g., if the control was initialized with a value)
        if (color != "") {
            color := Trim(color) ; Remove leading/trailing whitespace
            color := RegExReplace(color, "[^0-9a-fA-F]") ; Remove any non-hex characters

            ; Validate color input: must be exactly 6 hex characters
            if (StrLen(color) = 6 && RegExMatch(color, "i)^[0-9a-fA-F]{6}$"))
                stopConditions[mutationName][1] := "0x" . color
            else
                ; Log this, but don't halt the script or change the color if it's invalid
                ; The color will remain whatever it was previously, or the default.
                Log("Invalid color format in GUI for " . mutationName . ": '" . color . "'. Not updating color.")
        } else {
            ; If color is empty from the GUI control, log it if the checkbox is checked,
            ; but don't try to use an empty color for PixelSearch.
            ; The default color in stopConditions for this mutation will be used.
            if (stopConditions[mutationName][2]) { ; Only log if it's an enabled mutation
                 Log("Color for " . mutationName . " is empty in GUI. Using default or last valid color.")
            }
        }
    }

    for title, data in stopConditions {
        if (!data[2]) ; If false, skip this mutation's color detection
            continue

        color := data[1] ; The color hex code for this mutation

        ; Reset scan area for each new color search
        xStart := 0
        yStart := 0
        xEnd := A_ScreenWidth
        yEnd := A_ScreenHeight
        currentScanX := xStart
        currentScanY := yStart

        Loop {
            PixelSearch, px, py, currentScanX, currentScanY, xEnd, yEnd, %color%, %colorTolerance%, RGB Fast
            if (ErrorLevel) ; Pixel not found in remaining scan area
                break

            insideExclusion := false
            for index, zone in exclusionZones {
                coords := StrSplit(zone, ",")
                zx := coords[1] + 0
                zy := coords[2] + 0
                zw := coords[3] + 0
                zh := coords[4] + 0

                if (px >= zx && px <= zx + zw && py >= zy && py <= zy + zh) {
                    insideExclusion := true
                    break
                }
            }

            if (!insideExclusion) {
                clicking := false
                GuiControl,, StatusText, Status: Suspended
                UpdateStatusBar()
                SetTimer, DoClick, Off
                Log("Suspended: Detected " . title . " at " . px . "," . py)
                return
            }

            ; Update scan area to continue search from after the found pixel
            currentScanX := px + 1
            if (currentScanX > xEnd) {
                currentScanX := 0
                currentScanY := py + 1
                if (currentScanY > yEnd)
                    break
            }
        }
    }
return

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