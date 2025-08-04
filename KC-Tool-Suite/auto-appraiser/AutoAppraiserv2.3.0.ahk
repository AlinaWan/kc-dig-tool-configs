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

; Thanks to users lecsr, kou15, and Democracy for lending some items to capture their colors
; Mutation data. Each entry is [Color (string), Enabled_Checkbox_State (boolean)]
stopConditions := {}
stopConditions["Shiny"] := ["0xFFF587", true]
stopConditions["Ancient"] := ["0xFFD376", false]
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
stopConditions["Fossilized"] := ["0xFAB07E", false]
stopConditions["Galactic"] := ["0x934EFA", false]
stopConditions["Glossy"] := ["0x67DCF5", false]
stopConditions["Golden"] := ["0xFAE43C", false]
stopConditions["Iridescent"] := ["0xFFB7D3", false]
stopConditions["Marbled"] := ["0xCCC3A1", false]
stopConditions["Neon"] := ["0xB6FF40", false]
stopConditions["Noir"] := ["0xBAE0FA", false]
stopConditions["Petrified"] := ["0xFFCD8F", false]
stopConditions["Rusty"] := ["0x83594E", false]
stopConditions["Silver"] := ["0xC1D7FF", false]
stopConditions["Transparent"] := ["0xAAFFED", false]
stopConditions["Venomous"] := ["0x8F2FFE", false]
; --- 4.0 Mutation Additions ---
stopConditions["Blazing"] := ["0xFA771A", false]
stopConditions["Bronze"] := ["0xFA8B60", false]
stopConditions["Crystallized"] := ["0xACFAE0", false]
stopConditions["Frozen"] := ["0x9BC5F3", false]
stopConditions["Funky"] := ["0x2BFDA6", false]
stopConditions["Honey"] := ["0xFFFFFF", false] ; needs color
stopConditions["Moonlit"] := ["0xAD74FE", false]
stopConditions["Mossy"] := ["0x317E1B", false]
stopConditions["Sandy"] := ["0xFABA95", false]
stopConditions["Smoky"] := ["0xD2D3DA", false]
stopConditions["Soaked"] := ["0x5C7FDD", false]
stopConditions["Warped"] := ["0x7755FA", false]
stopConditions["Wormhole"] := ["0x802DD2", false]

; --- Paging Setup ---
mutationsPerPage := 6
currentPage := 1
mutationPages := []

; Custom order for the beginning of the list
customOrderInitial := ["Shiny", "Ancient", "Gargantuan", "Titanic", "Gigantic", "Big", "Small", "Tiny", "Microscopic"]

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
colorTolerance := 5
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
Gui, Add, Text, x30 y50, Click Delay (ms):
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
Gui, Add, Radio, x240 y140 vAndMode gSetMode, AND

Gui, Add, Button, gGitHubRepository x105 y170 w150, GitHub Repository

Gui, Add, Text, vWarningText x30 y220,
Gui, Add, Text, vStatusText x30 y240, F6: Toggle | Status: Suspended

Gui, Tab, Debug
Gui, Add, Edit, vDebugLog x30 y50 w300 h200 ReadOnly -WantReturn

Gui, Tab, Inclusions
Gui, Add, ListBox, vInclusionList x30 y50 w300 h150
Gui, Add, Button, gAddInclusion x30 y200 w140, Add Inclusion
Gui, Add, Button, gRemoveInclusion x190 y200 w140, Remove Inclusion
Gui, Add, Button, gStartDragSelection x30 y230 w300,  Drag to Select Zone

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

LoadInclusions()
SetTimer, CheckRobloxFocus, %pollingInterval%
Log("Script started.")
UpdateStatusBar() ; Initial status bar update
return

GitHubRepository:
Run, https://github.com/AlinaWan/kc-dig-tool-configs/tree/main/KC-Tool-Suite/auto-appraiser
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

SetMode:
    global mode, OrMode, AndMode ; Declare both radio button variables as global
    Gui, Submit, NoHide ; Submit to get the current state of GUI controls

    ; Get the checked state of each individual radio button
    GuiControlGet, isOrChecked, , OrMode
    GuiControlGet, isAndChecked, , AndMode

    if (isOrChecked) {
        mode := "Or"
    } else if (isAndChecked) {
        mode := "And"
    } else {
        ; Fallback, though one should always be checked in a radio group
        mode := "Or"
        Log("Warning: Neither OR nor AND radio button is checked. Defaulting to OR mode.")
    }
    
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
    Sleep, 50 ; Give the screen a moment to update after the click
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
    global clicking, clickDelay, colorTolerance, pollingInterval, mode
    status := clicking ? "Running" : "Suspended"
    GuiControl,, StatusText, % "F6: Toggle | Status: " status ""
}

CheckRobloxFocus:
    global clicking, colorTolerance, inclusionZones, stopConditions, allMutations, slotControls, mode

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
        if (color != "") {
            color := Trim(color)
            color := RegExReplace(color, "[^0-9a-fA-F]")
            if (StrLen(color) = 6 && RegExMatch(color, "i)^[0-9a-fA-F]{6}$"))
                stopConditions[mutationName][1] := "0x" . color
            ; Log("Updated stopConditions for " . mutationName . ": Checked=" . stopConditions[mutationName][2] . ", Color=" . stopConditions[mutationName][1])
        } else {
            ; Log("Color for " . mutationName . " is empty in GUI. Using default or last valid color.")
        }
    }

    if (mode = "Or") {
        ; OR mode: Stop if *any* enabled mutation's color is found in *any* inclusion zone
        for title, data in stopConditions {
            if (!data[2]) ; If not enabled, skip this mutation's color detection
                continue

            color := data[1] ; The color hex code for this mutation

            ; Loop through each inclusion zone
            for index, zone in inclusionZones {
                coords := StrSplit(zone, ",")
                zx := coords[1] + 0
                zy := coords[2] + 0
                zw := coords[3] + 0
                zh := coords[4] + 0

                ; Perform PixelSearch *only within* the current inclusion zone
                PixelSearch, px, py, zx, zy, zx + zw, zy + zh, %color%, %colorTolerance%, RGB Fast
                
                if (!ErrorLevel) { ; If pixel is found within this inclusion zone
                    clicking := false
                    GuiControl,, StatusText, Status: Suspended
                    UpdateStatusBar()
                    SetTimer, DoClick, Off
                    Log("Suspended: Detected " . title . " at " . px . "," . py . " within inclusion zone " . zone . " (OR mode)")
                    return ; Stop clicking and exit this function
                }
            }
        }
    } else if (mode = "And") {
        Log("AND mode active. Checking for all enabled mutations.")
        foundAllEnabled := true
        enabledMutationsCount := 0
        foundMutationsInAndMode := {} ; Map to track if each *enabled* mutation was found

        ; First, count enabled mutations and initialize their found status
        for title, data in stopConditions {
            if (data[2]) { ; Only consider enabled mutations
                enabledMutationsCount++
                foundMutationsInAndMode[title] := false ; Assume not found initially
            }
        }
        Log("Total enabled mutations for AND mode: " . enabledMutationsCount)

        ; If no mutations are enabled, the "AND" condition is not applicable for stopping.
        ; Continue clicking in this case.
        if (enabledMutationsCount = 0) {
            Log("No mutations enabled for AND mode. Continuing.")
            return
        }

        ; Now, try to find each enabled mutation
        for title, data in stopConditions {
            if (!data[2]) ; Skip disabled mutations
                continue

            color := data[1]
            foundThisMutation := false
            Log("Searching for '" . title . "' (Color: " . color . ")")

            ; Check if this specific color is found in *any* of the inclusion zones
            for index, zone in inclusionZones {
                coords := StrSplit(zone, ",")
                zx := coords[1] + 0
                zy := coords[2] + 0
                zw := coords[3] + 0
                zh := coords[4] + 0

                PixelSearch, px, py, zx, zy, zx + zw, zy + zh, %color%, %colorTolerance%, RGB Fast
                
                if (!ErrorLevel) {
                    foundThisMutation := true
                    Log("Found '" . title . "' at " . px . "," . py . " in zone " . zone)
                    break ; Found this color in one zone, no need to check other zones for *this* color
                }
            }

            if (foundThisMutation) {
                foundMutationsInAndMode[title] := true
            } else {
                ; If even one enabled mutation is not found, the "AND" condition fails
                foundAllEnabled := false
                Log("'" . title . "' NOT found. AND condition failed for this cycle.")
                break ; No need to check further mutations, as the AND condition is already false
            }
        }

        if (foundAllEnabled) {
            clicking := false
            GuiControl,, StatusText, Status: Suspended
            UpdateStatusBar()
            SetTimer, DoClick, Off
            Log("Suspended: All enabled mutations found simultaneously within inclusion zones (AND mode)")
            return
        } else {
            Log("AND condition not met for all enabled mutations. Continuing clicking.")
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
