# Pip Reroller v1

## Overview

Pip Reroller is a Python-based tool designed to automate the rerolling process by detecting objects of a specific color on the screen, clicking specified buttons, and stopping when a user-defined count of detected objects is reached. It uses OpenCV for image processing, tkinter for the GUI, and the `ahk` library to simulate mouse clicks via AutoHotkey.

---

## Usage

1. **Select Area**  
   Click the **Select Area** button, then drag on the screen to select the region containing the pip ranks (eg. SS, S, A).  
   ![Selection Example](/assets/kc-tool-suite/piprr_selection_example.png)
> [!IMPORTANT]
> The area should include only the pip rank area, not the area where stat value is (see the example image above).

2. **Set Chisel Button**  
   Click **Set Chisel Button**, then click on the orange pencil icon for the charm you want to reroll.  
   ![Chisel Button](/assets/kc-tool-suite/chisel_button.png)

3. **Set Buy Button**  
   Click **Set Buy Button**, then click on the confirmation "Yes" button that appears after clicking the chisel button.

4. **(Optional) Adjust Input Fields**

   * **Color Tolerance:** Controls how close a pixel’s color must be to the target color (`#FF82AE`) to be counted. Higher values allow more variance.
   * **Stop at \<int\> SS:** This sets the minimum number of **SS stats** (detected objects) at which the tool will stop rerolling.
        * If you enter **1**, the tool will stop as soon as **1 or more** SS stats are detected.
        * If you enter **3**, the tool will continue rerolling until it finds **3 or more** SS stats, then stop.
   * **Delay Between Clicks (ms):** Milliseconds to wait between clicking the chisel and buy buttons.
   * **Object Tolerance (px):** Pixel distance threshold to merge close detected bounding boxes into a single object.
  
> [!NOTE]
> This tool does not evaluate the stat values themselves. It only detects whether a pip is of SS rank based on its visual appearance (color).

5. **Start Preview**
   Use **Start Preview** to see bounding boxes around detected objects in real time in a separate window. Press **Q** in the preview window to exit.

6. **Start/Stop Automation**
   Press **F5** to toggle the automation running state. The status text on the GUI indicates whether the tool is **Running** or **Suspended**.

---

## Requirements

* Python 3.x
* [AutoHotkey](https://www.autohotkey.com/) (must be installed and on your system PATH)
* Python packages listed in `requirements.txt`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Notes

* The tool detects objects based on the color `#FF82AE` by default. Adjust the tolerance slider for best results depending on your screen colors and lighting.
* You must first select the area and both button positions before starting automation. Otherwise, the GUI will prompt you to complete these steps.
* The automation clicks are sent using AutoHotkey to improve compatibility with games and programs that may block simulated clicks from other methods.

---

## License

This script is licensed under the MIT License.

---

## Credits

Some logic for **selection area handling** and **bounding box preview** was borrowed and adapted from [iamnotbobby](https://github.com/iamnotbobby), also under the MIT License.
