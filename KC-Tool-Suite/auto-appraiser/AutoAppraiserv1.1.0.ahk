; Auto Appraiser by Riri
;
; This AutoHotkey script automatically clicks the "I'd like to appraise this" button in a loop.
; Intended primarily for appraising items for the shiny attribute.

#Persistent
#NoEnv
#SingleInstance Force
SetBatchLines -1
SetTitleMatchMode, 2
SendMode Input

clickDelay := 100
clicking := false
step := 0

Gui, +AlwaysOnTop
Gui, Margin, 10, 10
Gui, Font, s10, Segoe UI

; Left Side
Gui, Add, Text, vLabelDelay x10 y10, Click Delay (ms):
Gui, Add, Edit, vDelayEdit x10 y+2 w100, %clickDelay%
Gui, Add, Button, gSetDelay x10 y+5 w100, Set Delay
Gui, Add, Button, gOpenWeb x10 y+25 w100, GitHub Page

; Get positions of all three controls
GuiControlGet, posLabel, Pos, LabelDelay
GuiControlGet, posEdit, Pos, DelayEdit
GuiControlGet, posButton, Pos, SetDelay

; Calculate the rightmost edge among these controls
leftEdge := posLabelX + posLabelW
if (posEditX + posEditW > leftEdge)
    leftEdge := posEditX + posEditW
if (posButtonX + posButtonW > leftEdge)
    leftEdge := posButtonX + posButtonW

margin := 10
rightX := leftEdge + margin

; Right Side
Gui, Add, Edit, vDebugLog x%rightX% y10 w200 h130 ReadOnly -WantReturn

; Status Bar
Gui, Add, StatusBar
UpdateStatusBar()

Gui, Show,, Auto Appraiser by Riri
SetTimer, CheckRobloxFocus, 100
Log("Script started.")
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

OpenWeb:
Run, https://github.com/AlinaWan/kc-dig-tool-configs/tree/main/KC-Tool-Suite/auto-appraiser
return

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
    global clicking, clickDelay
    status := clicking ? "Running" : "Suspended"
    SB_SetText("F6: Toggle | Status: " status " | Delay: " clickDelay " ms")
}

CheckRobloxFocus:
global clicking

if (clicking && !WinActive("ahk_exe RobloxPlayerBeta.exe")) {
    clicking := false
    GuiControl,, StatusText, Status: Suspended
    UpdateStatusBar()
    SetTimer, DoClick, Off
    Log("Roblox lost focus. Auto-clicking suspended.")
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
