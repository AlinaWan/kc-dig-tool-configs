# Auto Appraiser by Riri

This AutoHotkey (AHK) script is designed for auto appraising in Roblox by automating clicking and stopping automatically when your chosen modifier (such as Shiny, Gargantuan, or other visual traits) appears on screen. It uses an inclusion-based system, meaning it only searches for those specific modifier colors within the areas you define.

---

## How to Use

### Prerequisites

- **AutoHotkey v1.1+**: You need to have AutoHotkey installed on your Windows machine.  
  [Download it from AutoHotkey.com](https://www.autohotkey.com)

### Running the Script

1. **Save the script**: Save the provided AHK code as a `.ahk` file (e.g., `AutoAppraiser.ahk`).
2. **Place `inclusions.ini`**: Ensure the `inclusions.ini` file is in the same directory as your `.ahk` script (If it doesn't exist yet, one will be created when adding an inclusion).
3. **Run**: Double-click the `.ahk` file to run the script. A small GUI window will appear.

---

## GUI Overview

The main window has several tabs:

- **Main**: Adjust core settings like Click Delay, Tolerance (for color matching), and Polling Interval.
- **Target**: Configure which "mutations" (colors) the script should look for.
- **Inclusions**: Define the specific screen regions where the script should search for colors.
- **Debug**: View a log of script actions and messages.

---

## Starting/Stopping the Clicking

- Press `F6` to toggle the clicking on or off.
- The script will automatically suspend if the Roblox window loses focus.

---

## Inclusions (`inclusions.ini`)

The `inclusions.ini` file defines the rectangular areas on your screen where the script will perform its color detection. The script will only look for colors within these specified zones.

### Default Configuration

The included `inclusions.ini` is pre-configured for:

- A 1920x1080 monitor
- Roblox running in windowed mode
- Windows 11
- Targeting the 6th hotbar slot

If your setup differs, you will need to adjust these zones.

### Adding/Removing Inclusion Zones

1. Go to the **Inclusions** tab.
2. Click **Add Inclusion**.
3. A window will prompt you for two coordinate pairs:
   - **Top-Left (X1,Y1)**: The coordinates of the top-left corner.
   - **Bottom-Right (X2,Y2)**: The coordinates of the bottom-right corner.
4. Use tools like AutoHotkey's built-in **Window Spy** to get exact pixel coordinates.
5. Click **OK** to save or **Cancel** to discard.
6. To remove a zone, select it from the list and click **Remove Inclusion**.

---

## Stop Conditions (Target Tab)

In the **Target** tab, you'll see a list of mutations (e.g., Shiny, Gargantuan, Chromatic).

- **Checkbox**: Enable color detection for that mutation. If its color appears in any defined inclusion zone, clicking stops.
- **Color Edit Box**: Specify the hexadecimal color code (e.g., `FFF587` for Shiny).

---

## Important Notes

- ⚠️ **"Dark" Modifier Warning**:  
  The color `0x4F4F4F` is close to the hotbar background. This may cause false positives. Adjust **Tolerance** with care.

- ⚠️ **"Gargantuan" and "Titanic" Color Overlap**:  
  Both **Gargantuan** and **Titanic** share the exact same detection color. Please be aware when interpreting results. This is just how the game works, and there’s nothing I can do to fix it.

- 🎨 **Color Tolerance**:  
  - Lower tolerance = stricter matching (less false positives, might miss slight color variations)  
  - Higher tolerance = more lenient (may detect wrong colors)

- 🖥️ **Screen Resolution**:  
  Zones are based on **absolute coordinates**. If you change your resolution or move the Roblox window, reconfigure the zones.

---

## License

Auto Appraiser is licensed under the [MIT License](LICENSE).
