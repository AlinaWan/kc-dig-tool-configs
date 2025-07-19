; Auto Appraiser by Riri
;
; This AutoHotkey script automatically clicks the "I'd like to appraise this" button in a loop.
; Intended primarily for appraising items for the shiny attribute.
;
; Supports exclusion zones defined by two points (X1,Y1) and (X2,Y2).
; Saves exclusions to exclusions.ini in format X,Y,Width,Height.
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
#NoEnv
#SingleInstance Force
SetBatchLines -1
SetTitleMatchMode, 2
SendMode Input

; --- Global Variables ---
clickDelay := 100
colorTolerance := 10
clicking := false
step := 0

exclusionsFile := A_ScriptDir "\exclusions.ini"
exclusionZones := []  ; Holds strings like "X,Y,Width,Height"

; --- GUI Setup ---
Gui, +AlwaysOnTop
Gui, Margin, 10, 10
Gui, Font, s10, Segoe UI

Gui, Add, Tab2, x20 y15 w330 h230 vMainTab, Main|Debug|Exclusions

Gui, Tab, Main
Gui, Add, Text, x30 y50, Click Delay (ms):
Gui, Add, Edit, vDelayEdit x150 y48 w100, %clickDelay%
Gui, Add, Button, gSetDelay x255 y47 w90, Set Delay

Gui, Add, Text, x30 y80, Tolerance (0-255):
Gui, Add, Edit, vToleranceEdit x150 y78 w100, %colorTolerance%
Gui, Add, Button, gSetTolerance x255 y77 w90, Set Tolerance

Gui, Add, Text, vWarningText x30 y200, Rainbow objects may false-trigger stop
Gui, Add, Text, vStatusText x30 y220, F6: Toggle | Status: Suspended

Gui, Tab, Debug
Gui, Add, Edit, vDebugLog x30 y50 w300 h150 ReadOnly -WantReturn

Gui, Tab, Exclusions
Gui, Add, ListBox, vExclusionList x30 y50 w300 h120
Gui, Add, Button, gAddExclusion x30 y180 w140, Add Exclusion
Gui, Add, Button, gRemoveExclusion x190 y180 w140, Remove Exclusion

Gui, Show,, Auto Appraiser by Riri

LoadExclusions()
SetTimer, CheckRobloxFocus, 100
Log("Script started.")
return

; -----------------------------------------
; Functions
; -----------------------------------------

LoadExclusions() {
    global exclusionZones, exclusionsFile
    exclusionZones := []
    if !FileExist(exclusionsFile)
        return
    Loop, Read, %exclusionsFile%
    {
        rawLine := A_LoopReadLine
        line := Trim(rawLine)
        line := RegExReplace(line, "\s")  ; remove all spaces/tabs/newlines

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
    GuiControlGet, selectedItem,, ExclusionList
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
    global clicking, colorTolerance, exclusionZones

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

    ; Search entire screen for target color, skipping pixels inside exclusion zones
    xStart := 0
    yStart := 0
    xEnd := A_ScreenWidth
    yEnd := A_ScreenHeight
    color := 0xFFF587

    Loop {
        PixelSearch, px, py, xStart, yStart, xEnd, yEnd, color, %colorTolerance%, RGB Fast
        if (ErrorLevel)  ; No more found pixels
            break

        ; Check if found pixel is inside any exclusion zone
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
            ; Pixel found outside exclusions - suspend clicking
            clicking := false
            GuiControl,, StatusText, Status: Suspended
            UpdateStatusBar()
            SetTimer, DoClick, Off
            Log("Suspended: Detected target color (#FFF587) at " px "," py)
            return
        }

        ; Else, pixel inside exclusion - continue searching, skip this pixel by advancing x by 1
        xStart := px + 1
        yStart := py
        if (xStart >= xEnd) {
            xStart := 0
            yStart := py + 1
            if (yStart >= yEnd)
                break
        }
    }
return

GuiClose:
    SetTimer, CheckRobloxFocus, Off
    ExitApp

Log(msg) {
    GuiControlGet, currentLog,, DebugLog
    FormatTime, timeStr,, HH:mm:ss
    newLog := "[" timeStr "] " msg "`n" currentLog
    if (StrLen(newLog) > 3000)
        newLog := SubStr(newLog, 1, 3000)
    GuiControl,, DebugLog, %newLog%
}

; Helper: Join strings with delimiter
StrJoin(delim, arr) {
    local result := ""
    for index, value in arr
        result .= (index=1 ? "" : delim) . value
    return result
}
