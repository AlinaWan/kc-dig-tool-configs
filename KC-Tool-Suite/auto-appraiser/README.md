# Auto Appraiser by Riri

**Auto Appraiser** is an AutoHotkey (AHK) script designed to automate appraising items in the Roblox game [*Dig!*](https://www.roblox.com/games/126244816328678). The script stops intelligently and automatically when your selected target modifier (such as **Shiny**, **Gargantuan**, or **Titanic**) appears.

---

## 📦 Requirements

Before using the script, ensure you have the following:

* **AutoHotkey v1.1**  
  Download it from: [https://www.autohotkey.com](https://www.autohotkey.com)

---

### 🛠️ Installation & Setup

Follow these steps to get started:

1. **Download the script**

   * Download the latest version of Auto Appraiser, OR:
   * Export the Auto Appraiser directory using SVN:

     ```bash
     svn export https://github.com/AlinaWan/kc-dig-tool-configs/trunk/KC-Tool-Suite/auto-appraiser
     ```

2. **Run the script**

   * Double-click the script to launch the GUI.

3. **Add at least one inclusion zone**

   * Before using the auto-clicker, you **must define at least one inclusion zone** through the **Inclusions** tab in the GUI.
   * These zones tell the script where on screen to look for modifier colors.
   * If no zones are added, the script has nothing to scan and will not function correctly.

---

## 🖥️ Using the Script

### Launching and Toggling

* Press `F6` to start or stop auto-clicking.
* The script will pause automatically if the Roblox window loses focus or your target modifier is found.

---

## 🧭 GUI Overview

The GUI includes four tabs:

* **Main** – General settings (Click Delay, Color Tolerance, Polling Interval)
* **Target** – Choose which modifier colors stop clicking
* **Inclusions** – Define exact screen regions to scan
* **Debug** – View real-time script messages and actions

---

## 🎯 Inclusion Zones (`inclusions.ini`)

Inclusion zones tell the script *where* to look for modifier colors.

### What Should a Zone Be?

Each zone should **closely match the pixel bounds of the hotbar item** you're appraising (e.g., the 6th hotbar slot).
**Avoid including any pixels outside the item square**, such as beyond the background UI, as they can interfere with detection.  

![Example Inclusion](example_inclusion.png)

### Default Configuration

The included `inclusions.ini` is pre-set for:

* 1920×1080 resolution
* Roblox in **windowed mode**
* **Windows 11**
* Targeting the **6th hotbar slot**

You will need to adjust the zones if you are using:

* A different resolution
* A different windowed/fullscreen mode
* A different hotbar slot

### How to Add/Remove Zones

1. Open the GUI and go to the **Inclusions** tab.
2. Click **Add Inclusion**.
3. Enter two coordinate pairs:

   * **Top-Left (X1, Y1)** – Upper-left corner of the zone
   * **Bottom-Right (X2, Y2)** – Lower-right corner of the zone

4. Use AutoHotkey's **Window Spy** tool to get exact pixel coordinates.
5. Click **OK** to save the zone.
6. To remove a zone, select it from the list and click **Remove Inclusion**.

---

## 🎨 Stop Conditions (Target Tab)

The **Target** tab defines which visual modifiers should stop the auto-clicking when detected.

Each row includes:

* **Checkbox** – Enable or disable detection for that modifier.
* **Hex Color Box** – The exact RGB hex code to detect (e.g., `FFF587` for Shiny).

Detection behavior depends on the **Match Mode** selected in the **Main** tab:

* ✅ **OR Mode** (default):
  Clicking will stop as soon as **any** enabled color is found in any inclusion zone.

* ✅ **AND Mode**:
  Clicking will stop **only if all** enabled colors are found in the inclusion zones at the same time.

You can switch between OR and AND using the radio group in the Main tab.

---

## ⚠️ Notes & Warnings

* 🕶️ **Dark Modifier Warning**  
  The color `0x4F4F4F` (the color of the Dark modifier) is nearly identical to the hotbar background. This may cause false detections unless tolerance is tuned carefully.

* 🧍‍♂️ **Gargantuan/Titanic Conflict**  
  These modifiers use the **exact same color**, so the script cannot differentiate between them. This is a game limitation, not a script bug.

* 🎚️ **Color Tolerance**  

  * Lower tolerance = stricter match (less false positives, but may miss minor shifts)
  * Higher tolerance = more forgiving (but may trigger incorrectly)

* 🖥️ **Resolution & Position Sensitivity**  
  Inclusion zones use **absolute screen coordinates**.
  If you change resolution, move the Roblox window, or switch displays, you must reconfigure your zones.

* 🎨 **Target Color Codes**  
  Changes made to the target colors in the GUI do not persist after closing the script. This is intentional as the defaults are already optimized for typical systems.
  You usually don’t need to change them unless using custom screen filters or displays.

---

## 📄 License

Auto Appraiser is licensed under the [MIT License](LICENSE).
