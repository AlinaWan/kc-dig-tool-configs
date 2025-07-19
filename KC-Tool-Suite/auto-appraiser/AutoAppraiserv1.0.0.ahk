; Auto Appraiser by Riri
;
; This AutoHotkey script automatically clicks the "I'd like to appraise this" button in a loop.
; Intended primarily for appraising items for the shiny attribute.
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

clickDelay := 100
clicking := false
step := 0

Gui, +Resize +AlwaysOnTop
Gui, Margin, 10, 10
Gui, Font, s10, Segoe UI
Gui, Add, Text,, Click Delay (ms):
Gui, Add, Edit, vDelayEdit w100, %clickDelay%
Gui, Add, Button, gSetDelay w100, Set Delay
Gui, Add, Text, vStatusText Section xs y+10 w200, Status: Inactive
Gui, Add, Text, vHotkeyInfo x+0 ys, [F6 to Toggle]
Gui, Add, StatusBar

UpdateStatusBar()

Gui, Show,, Auto Appraiser by Riri
return

SetDelay:
Gui, Submit, NoHide
if (DelayEdit is "digit" && DelayEdit > 0) {
    clickDelay := DelayEdit
}
return

F6::ToggleClicking()

ToggleClicking() {
    global clicking
    clicking := !clicking
    GuiControl,, StatusText, % "Status: " (clicking ? "Active" : "Inactive")
    UpdateStatusBar()
    if (clicking)
        SetTimer, DoClick, 1
    else
        SetTimer, DoClick, Off
}

DoClick:
Click
MoveMouseInCircle()
Sleep, clickDelay
return

MoveMouseInCircle() {
    global step
    step := Mod(step + 1, 4)
    if (step = 0)
        MouseMove, 0, -1, 0, R  ; Up
    else if (step = 1)
        MouseMove, 1, 0, 0, R  ; Right
    else if (step = 2)
        MouseMove, 0, 1, 0, R  ; Down
    else if (step = 3)
        MouseMove, -1, 0, 0, R ; Left
}

UpdateStatusBar() {
    global clicking, clickDelay
    status := clicking ? "Running" : "Suspended"
    SB_SetText("F6: Toggle | Status: " status " | Delay: " clickDelay " ms")
}

GuiClose:
ExitApp