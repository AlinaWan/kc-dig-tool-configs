#NoEnv
#SingleInstance Force
SetBatchLines, -1
SetTitleMatchMode, 2
SendMode Input

clicking := false
pollingInterval := 100

Gui, +AlwaysOnTop
Gui, Margin, 10, 10
Gui, Font, s10, Segoe UI

Gui, Add, Tab2, x20 y15 w330 h240 vMainTab, Main|Debug

Gui, Tab, Main
Gui, Add, Text, x30 y50, F6: Toggle Net Drop + Autoclick
Gui, Add, Text, x30 y70, Esc: Exit
Gui, Add, Text, x30 y95 w300, USAGE: Place your cursor over the Open Crate button, then press F6 to start/stop the autoclick and net drop.

Gui, Font, s8, Segoe UI
Gui, Add, Text, x30 y155 w300 +Wrap +Center vWarningText cRed, WARNING: This tool uses a network manipulation method that may exploit unintended game behavior.`nUse at your own risk. You assume full responsibility for any consequences, including potential bans.
Gui, Font, s10, Segoe UI

; Status bar at the bottom of the main tab (like your example)
Gui, Add, Text, vStatusText x30 y220 w300 cBlue Center, F6: Toggle | Status: Suspended

Gui, Tab, Debug
Gui, Add, Edit, vDebugLog x30 y50 w300 h120 ReadOnly -WantReturn

Gui, Show, w370 h270, Auto Crate Opener by Riri
SetTimer, CheckRobloxFocus, %pollingInterval%
Log("Script started.")
UpdateStatusBar()
return

; F6 Toggle Net Drop + Click Spam
$F6::
clicking := !clicking
if (clicking) {
    Log("F6 pressed: Starting continuous net drop and autoclick.")
    UpdateStatusBar("Running")
    SetTimer, ClickSpam, 10       ; click every 10ms
    SetTimer, NetDropLoop, 0      ; start immediately
} else {
    Log("F6 pressed: Stopping autoclick and net drop.")
    UpdateStatusBar("Stopped")
    SetTimer, ClickSpam, Off
    SetTimer, NetDropLoop, Off
}
return

NetDropLoop:
    Run, %ComSpec% /c ipconfig /release,, Hide
    Sleep, 1
    Run, %ComSpec% /c ipconfig /renew,, Hide
    Sleep, 11000  ; wait 11 seconds before next drop
return

ClickSpam:
    Click
return

Esc::
Log("Exiting script.")
ExitApp
return

CheckRobloxFocus:
if WinActive("Roblox") {
    if clicking
        UpdateStatusBar("Running (Roblox Active)")
    else
        UpdateStatusBar("Suspended (Roblox Active)")
} else {
    if clicking
        UpdateStatusBar("Running (Roblox Inactive)")
    else
        UpdateStatusBar("Suspended (Roblox Inactive)")
}
return

UpdateStatusBar(statusText := "") {
    static lastStatus := ""
    global clicking

    if (statusText = "")
    {
        statusText := clicking ? "Running" : "Suspended"
    }

    if (statusText != lastStatus)
    {
        GuiControl,, StatusText, F6: Toggle | Status: %statusText%
        lastStatus := statusText
    }
}

Log(msg) {
    global DebugLog
    FormatTime, timestamp,, HH:mm:ss
    GuiControlGet, currentLog,, DebugLog
    newLog := "[" . timestamp . "] " . msg . "`n" . currentLog
    GuiControl,, DebugLog, %newLog%
}
