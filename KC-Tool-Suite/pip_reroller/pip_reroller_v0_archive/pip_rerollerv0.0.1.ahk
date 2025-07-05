/*
    AutoHotkey Script: Auto Clicker for Rerolling Pips

    📌 Hotkeys:
    - F4: Toggle the click loop ON or OFF.
          When ON, it will click both defined points every cycle.
    - F5: Set the FIRST click point (waits for your next left click). This should be set on the orange pencil icon.
    - F6: Set the SECOND click point (waits for your next left click). This should be set on the buy reroll button.
    - F7: Manually perform one full click cycle immediately (without enabling the loop).
    - Esc: Exit the script immediately.

    🔁 Loop Behavior:
    - The script clicks both target positions once per loop cycle.
    - Each loop has a fixed delay of 1500 milliseconds (1.5 seconds) between cycles.

    ⚠️ Important:
    - This script does NOT detect which pips you get or track results.
    - Be sure to toggle the clicker OFF (press F4 again) if you're happy with your result before the script rerolls again!
*/

#Requires AutoHotkey v1.1

toggle := false
click1 := [1, 1]
click2 := [2, 2]
waitingForClick := ""

F4:: ; Toggle clicker
toggle := !toggle
if (toggle) {
    ToolTip, Script is ON. Clicking will start.
    SetTimer, RemoveToolTip, 500
    SetTimer, ClickLoop, 10
} else {
    ToolTip, Script is OFF. Clicking stopped.
    SetTimer, RemoveToolTip, 500
    SetTimer, ClickLoop, Off
}
return

ClickLoop:
    Click, % click1[1] "," click1[2]
    Click, % click2[1] "," click2[2]
    Sleep, 1500
return

F7:: ; Manual one-time click loop
    Click, % click1[1] "," click1[2]
    Click, % click2[1] "," click2[2]
return

F5:: ; Set first click position
    waitingForClick := "click1"
    ToolTip, Click anywhere to set FIRST click point...
    SetTimer, RemoveToolTip, 1000
return

F6:: ; Set second click position
    waitingForClick := "click2"
    ToolTip, Click anywhere to set SECOND click point...
    SetTimer, RemoveToolTip, 1000
return

~LButton::
    if (waitingForClick != "") {
        MouseGetPos, x, y
        %waitingForClick% := [x, y]
        ToolTip, % (waitingForClick = "click1" ? "First" : "Second") . " click set to: " . x . ", " . y
        SetTimer, RemoveToolTip, 1000
        waitingForClick := ""
    }
return

Esc::ExitApp

RemoveToolTip:
ToolTip
return

GuiClose:
ExitApp
return