
# Boris's Scalemail Planner

A simple python script for a Scalemail Editor with customizable size and colors.

Includes the following features: 
* Custom Scale Pattern Size
* Fully Custom Scale Colors 
* Dynamically Change Scales' Colors
* Dual-Axis Symmetry
* Undo / Ctrl-Z
* Hotswap between your last two selected colors with 'Space'
* Hotswap between your first 9 colors with number keys and Invisible with 0 or `
* Exporting and Sharing your patterns
* Scale counters


### Example Import/Export Code

```
Old Format:
[20,45][0036e5,959595,1a1a1a][3-1,3,2-2,2-1,3,2-2,3,2-1,2-2,3,6-1,2-3,2,2-1,3,2,3,2-1,2,2-3,3-1,0,2,3-1,3,2-2,2-1,2-3,2-1,2-2,3,3-1,2-2,3-1,2-3,2,2-1,3,2-1,2,2-3,3-1,2,0,3,4-1,3,2-2,4-1,2-2,3,4-1,3,2,4-1,2-3,2,3-1,2,2-3,4-1,2,0,3,5-1,3,2-2,2-1,2-2,3,5-1,3,2,3-1,3,1,2-3,2,1,2,2-3,1,3,3-1,2,0,3,2,2-1,2,2-1,3,4-2,3,2-1,2,2-1,2,2-3,2-1,2-3,2-1,2-3,2,2-3,2-1,2-3,2-1,3,0,3,2,1,2,3,3-1,3,2-2,3,3-1,3,2,1,2,2-3,1,2-3,4-1,3-3,4-1,2-3,1,3,0,3,2,1,3,5-1,2-3,5-1,3,1,2,2-3,1,3,6-1,3,6-1,3,1,3,0,3,2,5-1,3,4-1,3,5-1,2,2-3,2,4-1,2,5-1,2,4-1,2,3,0,2-3,4-1,2-3,4-1,2-3,4-1,3-3,2,3-1,2,3,2-1,3,2-1,3,2,3-1,2,3,0,2-3,3-1,2-3,6-1,2-3,3-1,3-3,2,2-1,2,3,7-1,3,2,2-1,2,3,0,2-3,3-1,3,8-1,3,3-1,3-3,2,2-1,2,3,3-1,3,3-1,3,2,2-1,2,3,0,2-3,2-1,2-3,8-1,2-3,2-1,3-3,2,1,2,3,9-1,3,2,1,2,3,0,2-3,1,2-3,10-1,2-3,1,3-3,2,1,3,3-1,3,1,3,1,3,3-1,3,1,2,3,0,2-3,1,3,3-1,2,4-1,2,3-1,3,1,3-3,2,4-1,2-3,3-1,2-3,4-1,2,3,0,2-3,4-1,2,3,4-1,3,2,4-1,3-3,2,3-1,2-3,2-1,3,2-1,2-3,3-1,2,3,0,3,2,3-1,2,3,6-1,3,2,3-1,2,2-3,4-1,3,7-1,3,4-1,3,0,3,2,3-1,2,3,6-1,3,2,3-1,2,2-3,3-1,2-3,3-1,3,3-1,2-3,3-1,3,0,3,2,2-1,2,3,8-1,3,2,2-1,2,2-3,2-1,2-3,9-1,2-3,2-1,3,0,3,2,1,2,3,10-1,3,2,1,2,3,2,1,2-3,5-1,3,5-1,2-3,1,2,0,3,2-1,3,5-1,2-2,5-1,3,2-1,3,2,1,3,4-1,5-3,4-1,3,1,2,0,3,6-1,2-2,2-3,2-2,6-1,3,2,5-1,3-3,0,3-3,5-1,2,0,2,5-1,2,2-3,2-0,2-3,2,5-1,2,5-1,2-3,5-0,2-3,5-1,0,5-1,2-3,6-0,2-3,5-1]

New Format:
(8dO6AhQtBgA25ZWVlRoaGlRsVJsTUsTWuSUmRqScqgJUbFS5UsTVMVTklJqScqiA1ZsVbE1ZkrckqJyrIDWGxUsTWGSoxckJORNUQGSklJszUkpJypcqXJOVLlSYGQkao2JqjISci5VulbkTAyE1jlYYk5E1prTEwMlhqzWE5JWSwlZGDlW5VuVbolRGpNSZKiMHKpytcqnRKSNcZKSMHKo15qnRKSNUaoyUkYOVLle5UuiEjkgyEjByLmSXIuiE1RiYmqMSMHImqJWSoxdErcqnKsjByrI1ZkrdEqcqTUuVRGBkqI1pkqJyrNcaswMlRGtMlROVTlUapyqMDJSRrzJSTlS5khypMDISOSTISMhcrDWORIDUmsYrDUmQmreKzEgNaxcsVpksdA6WEBLCcoXJLCWOUjlYCxylcrA=)
```


## Screenshot of GUI with Example Code Loaded

![App Screenshot](https://i.imgur.com/0Em1yCs.png)

## Installation
The GUI is a single-file python script. You can clone the repo or download the zip file in the [Releases](https://github.com/borisshoes/ScalemailPlanner/releases) page to a directory of your choice.

**Alternatively, you can download the pre-compiled EXE file and run that.**

Installation Steps:
1) Download and install Python from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2) Download the ZIP file from the [Releases](https://github.com/borisshoes/ScalemailPlanner/releases) page and unzip the folder.
3) Either run installer.bat if you are on windows, or use the following two commands on mac with a terminal in the folder

```python -m pip install --upgrade --user pip```

```python -m pip install -r requirements.txt --user```

4) The installer will open the window on success, or you can then just use run.bat. For mac use the command

```python ./scales.py```

## Usage
### Option A
Run the EXE file available in [Releases](https://github.com/borisshoes/ScalemailPlanner/releases)

### Option B
1) Run the python script with scale.png in the same directory (you can use a custom scale image or the included one)
2) Enter the size of your pattern in the width and height boxes (measured in scales)
3) Click Make Scale Grid
4) Change Color 1 by clicking the color preview next to 'Color 1'
5) Add a new color by clicking New Color
6) Switch between colors using the number keys or between your previous color with 'Space'
7) Change scale colors by selecting a color and clicking, or click-dragging to paint scales
8) The Invisible color is uneditable and will make the selected scales invisible, allowing for non-rectangular patterns.
9) Scale count for each color is in the parentheses next to each color in the list
10) Don't forget to save or share your pattern by Exporting it and saving the code somewhere (see below)

### Importing/Exporting
Clicking Export will generate a code of your current pattern and save it to your clipboard.

Pasting a code into the text box and clicking Import will load the pattern.