# Pip Reroller v1

## Overview

Pip Reroller is a Python-based tool designed to automate the rerolling process by detecting object ranks (SS, S, A, etc) on the screen, clicking specified buttons, and stopping when your chosen quality conditions are met. It uses OpenCV for image processing, tkinter for the GUI, and the `ahk` library to simulate mouse clicks via AutoHotkey.

---

## Usage

1. **Select Area**  
   Click the **Select Area** button, then drag on the screen to select the region containing the pip ranks (e.g. SS, S, A).  
   ![Selection Example](/assets/kc-tool-suite/piprr_selection_example.png)
> [!IMPORTANT]
> The area should include only the pip rank area, not the area where stat value is (see the example image above).

2. **Set Chisel Button**  
   Click **Set Chisel Button**, then click on the orange pencil icon for the charm you want to reroll.  
   ![Chisel Button](/assets/kc-tool-suite/chisel_button.png)

3. **Set Buy Button**  
   Click **Set Buy Button**, then click on the confirmation "Yes" button that appears after clicking the chisel button.

4. **Adjust Input Fields**

   * **Color Tolerance:** How close a pixel’s color must be to the target rank color for it to be detected (higher = more lenient).
   * **Minimum SS:** The minimum number of **SS** ranks required to stop rerolling. For example, if set to **1**, the tool stops when at least one SS is found.
   * **Minimum Quality:** Select the lowest rank (F, D, C, B, A, S, SS) you accept for stopping. Only pips **at least this rank** or higher are counted toward the minimum objects condition.
   * **Minimum Objects:** The minimum number of detected objects of at least the chosen minimum quality required to stop.
   * **Delay Between Clicks (ms):** Milliseconds to wait between clicking the chisel and buy buttons.
   * **Object Tolerance (px):** Pixel distance threshold for merging close detected bounding boxes into a single object.
  
> [!NOTE]
> This tool does not evaluate stat values themselves. It only detects each pip's visual rank based on color.

5. **Start Preview**  
   Use **Start Preview** to see bounding boxes around detected objects in real time in a separate window. Press **Q** in the preview window to exit.

6. **Start/Stop Automation**  
   Press **F5** to toggle the automation running state. The status text on the GUI indicates whether the tool is **Running** or **Suspended**.

---

## Stopping Logic: Condition Hierarchy

Pip Reroller will only stop rerolling when **both** of the following conditions are met:

1. **Minimum Objects:** At least the specified number of pips (`Minimum Objects`) are detected that are >= your chosen `Minimum Quality`.
2. **Minimum SS:** At least the specified number of pips are detected that are of the **SS** rank.

> **Both conditions must be true at the same time before the tool will stop.**

### Example Stopping Cases

Suppose:
- Minimum Objects = 3
- Minimum SS = 1
- Minimum Quality = C

| Detected Ranks     | Stops? | Reason                           |
|--------------------|--------|----------------------------------|
| SS, F, F           | No     | Only 1 ≥C, needs 3               |
| SS, C, F           | Yes    | 3 objects ≥C, at least 1 SS      |
| SS, SS             | No     | Only 2 objects                   |
| A, B, B            | No     | 3 objects ≥C, but no SS          |
| SS, C, B           | Yes    | 3 objects ≥C, at least 1 SS      |
| SS, SS, SS         | Yes    | 3 objects ≥C, all SS             |
| D, D, D, SS        | No     | Only 1 ≥C, needs 3               |

### Example Goal-Based Configurations

> Want to build your configuration based on a *target outcome*? Here are some examples:

#### Example Goal 1: You want to stop only if you get **A, A, SS**

* Set **Minimum Objects** = 3
  (because you want 3 A+ pips total)
* Set **Minimum Quality** = A
  (because you want all pips to be at least A)
* Set **Minimum SS** = 1
  (because you require at least one SS pip)

> This ensures all pips are A or higher, and one must be SS before it stops.

#### Example Goal 2: You want **at least 2 SS**, regardless of other pips

* **Minimum Objects** = 2
* **Minimum Quality** = F (or the lowest allowed)
* **Minimum SS** = 2

> Tool stops when there are at least 2 pips total, both of which are SS.

#### Example Goal 3: You want **S+, but don’t care if SS appears**

* **Minimum Objects** = 3
* **Minimum Quality** = S
* **Minimum SS** = 0

> Will stop when at least 3 ranks are S or higher, even if SS is not present.

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

* The tool detects pip ranks based on their colors (SS, S, A, etc) using default reference colors. Adjust the color tolerance for best results depending on your screen and lighting.
* You must select the area and both button positions before starting automation.
* Automation clicks use AutoHotkey for compatibility with games and programs that block simulated clicks from other libraries.

---

## License

This script is licensed under the [MIT License](LICENSE.txt).

---

## Credits

Some logic for **selection area handling** and **bounding box preview** was borrowed and adapted from [iamnotbobby](https://github.com/iamnotbobby), also under the MIT License.
