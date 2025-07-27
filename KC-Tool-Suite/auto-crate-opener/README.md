<div align="center">

&nbsp; <h1>Auto Crate Opener</h1>

</div>



> \*“Praemonitus, praemunitus.”\* — Riri, circa 2025



\*\*Auto Crate Opener\*\* is a toggle-driven, network manipulation and click-spamming automation utility crafted with the procedural scripting prowess of AutoHotkey v1.1. Its ostensible function—automatizing the opening of crates within the Roblox game environment by exploiting transient network interface resets—is undergirded by a precise orchestration of system command invocation, asynchronous timer-driven click emission, and GUI-stateful toggling mechanisms.



By leveraging repeated invocation of `ipconfig /release` and `ipconfig /renew`, this tool effectuates momentary network drops (\*intermissio retis\*), which in turn influence the Roblox client’s crate opening mechanics. Concurrently, a rapid-fire click spam (\*cliques rapidus\*) ensures interaction continuity during the toggled operation, all managed via a clean, user-centric GUI interface.



---



\## 📦 Requirements



Before execution, verify the presence of:



\* \*\*AutoHotkey v1.1\*\*  

&nbsp; Obtainable at \[https://www.autohotkey.com](https://www.autohotkey.com)



---



\## 🛠️ Installation \& Setup



1\. \*\*Download the script\*\*  

&nbsp;  \* Fetch the latest Auto Crate Opener release, or  

&nbsp;  \* Export the repository via SVN:  

&nbsp;  ```bash

&nbsp;  svn export https://github.com/AlinaWan/kc-dig-tool-configs/trunk/KC-Tool-Suite/auto-crate-opener

````



2\. \*\*Run the script\*\*



&nbsp;  \* Launch by double-clicking the `.ahk` file to bring forth the GUI.



---



\## 🖥️ Usage



\* Press `F6` to toggle the automated net drop and click spam on or off.

\* The tool executes cycles of network interface reset approximately every 11 seconds, interleaved with ultra-fast click spam.

\* The status bar updates to reflect current operational state.

\* Press `Esc` at any time to exit the application cleanly.



---



\## 🧭 GUI Overview



The GUI comprises two tabs:



\* \*\*Main\*\* – Displays usage instructions, warnings, and a dynamic status bar reflecting toggled state and Roblox window focus.

\* \*\*Debug\*\* – Provides a scrolling log of script activity and runtime messages for diagnostics.



---



\## ⚠️ Important Warning



This utility employs a network disruption technique that may be construed as exploiting unintended game behavior. Use with full awareness of potential risks, including but not limited to:



\* Temporary network instability

\* Dig penalties or bans



\*\*End users accept full responsibility for any consequences arising from usage.\*\*



---



\## 📄 License



Auto Crate Opener is distributed under the \[MIT License](LICENSE).

