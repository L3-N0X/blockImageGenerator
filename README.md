# Block Image Generator

A Python tool that converts pixel art images into text-based block representations for use in Java games. It generates a Java class with block image constants and color palette configurations.

## Prerequisites

- Python 3.12 or higher
- PIL (Pillow) library

## Project Structure

```
blockImageGenerator/
├── input/           # Place your pixel art images here
├── output/         # Generated files will appear here
├── main.py         # Main script
└── pyproject.toml  # Project dependencies
```

## Installation and Setup

### Option 1: Using uv (Recommended)

1. Install uv if you haven't already:
```bash
pip install uv
```

### Option 2: Using Standard Python venv

1. Create a new virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install pillow
```

## Usage

1. Create the required directories if they don't exist:
   - `input/` - For your source images
   - `output/` - For generated files

2. Place your pixel art images (PNG, JPG, etc.) in the `input/` directory

3. Run the script:
```bash
uv run main.py
# OR
python main.py
```

4. Check the `output/` directory for two generated files:
   - `GameBlockImages.java` - Contains the block image string constants
   - `ColorPalettes.txt` - Contains color configuration code

## Integration with Java Project

1. Copy `GameBlockImages.java` to your Java project's source directory:
   - Example path: `src/thd/gameobjects/movable/GameBlockImages.java`

2. Copy the color configuration code from `ColorPalettes.txt` into your Java project where you initialize your `GameView` instance

3. Use the generated block images in your code:
```java
gameView.addBlockImageToCanvas(GameBlockImages.TREE, x, y, size, rotation);
```

## Color Palette

The tool uses a predefined set of color mappings based on standard AWT Colors:
- `R/r` - Red (normal/darker)
- `G/g` - Green (normal/darker)
- `B/b` - Blue (normal/darker)
- `Y/y` - Yellow (normal/darker)
- And more...

Additional colors are automatically mapped to available characters (A-Z, a-z, 0-9).

## Notes

- Transparent pixels in source images are converted to spaces in the block representation
- The tool automatically handles color mapping and generates appropriate Java code
- Make sure your pixel art images use a reasonable number of unique colors to avoid running out of available characters