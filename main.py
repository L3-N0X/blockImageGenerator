# Example Usage:
# 1. Create directories `./input` and `./output`.
# 2. Place your small pixel art images (e.g., `tree.png`, `player.png`) in `./input`.
# 3. Run this Python script (`python your_script_name.py`).
# 4. Check the `./output` directory for `GameBlockImages.java` and `ColorPalettes.txt`.
# 5. Integrate the generated files/code into your Java project following the instructions above.

import os
from PIL import Image
import collections

# --- Configuration ---
INPUT_DIR = './input'
OUTPUT_DIR = './output'
DEFAULT_PALETTE_JAVA = { # Based on the JavaDoc [cite: 91, 92, 482, 483, 484] - Standard AWT Colors
    'R': (255, 0, 0),     # Color.RED
    'r': (192, 0, 0),     # Color.RED.darker() - Approximation
    'G': (0, 255, 0),     # Color.GREEN
    'g': (0, 192, 0),     # Color.GREEN.darker() - Approximation
    'B': (0, 0, 255),     # Color.BLUE
    'b': (0, 0, 192),     # Color.BLUE.darker() - Approximation
    'Y': (255, 255, 0),   # Color.YELLOW
    'y': (192, 192, 0),   # Color.YELLOW.darker() - Approximation
    'P': (255, 175, 175), # Color.PINK
    'p': (192, 131, 131), # Color.PINK.darker() - Approximation
    'C': (0, 255, 255),   # Color.CYAN
    'c': (0, 192, 192),   # Color.CYAN.darker() - Approximation
    'M': (255, 0, 255),   # Color.MAGENTA
    'm': (192, 0, 192),   # Color.MAGENTA.darker() - Approximation
    'O': (255, 200, 0),   # Color.ORANGE
    'o': (192, 150, 0),   # Color.ORANGE.darker() - Approximation
    'W': (255, 255, 255), # Color.WHITE
    'L': (0, 0, 0),       # Color.BLACK (L for 'bLack' to avoid conflict with Blue)
}
# Characters to use for new colors if default ones don't match or run out
# Prioritize uppercase, then lowercase, then numbers
AVAILABLE_CHARS = (
    [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in DEFAULT_PALETTE_JAVA] +
    [c for c in "abcdefghijklmnopqrstuvwxyz" if c not in DEFAULT_PALETTE_JAVA] +
    [str(i) for i in range(10)]
)

# --- Helper Functions ---

def ensure_dir(directory):
  """Creates the directory if it doesn't exist."""
  if not os.path.exists(directory):
    os.makedirs(directory)

def get_image_files(directory):
  """Gets a list of image filenames from the input directory."""
  files = []
  if not os.path.isdir(directory):
      print(f"Error: Input directory '{directory}' not found.")
      return files
  for filename in os.listdir(directory):
    # Basic check for common image extensions
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
      files.append(os.path.join(directory, filename))
  return files

def analyze_colors(image_files):
    """Analyzes images to find unique opaque colors."""
    unique_colors = set()
    for filepath in image_files:
        try:
            with Image.open(filepath) as img:
                # Convert to RGBA to handle transparency consistently
                img = img.convert("RGBA")
                width, height = img.size
                pixels = img.load()
                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[x, y]
                        # Consider fully transparent as space (handled later)
                        # Collect only opaque or semi-transparent colors
                        if a > 0: # Treat anything not fully transparent as a color
                             # Store only RGB, assuming alpha handling is just for space vs char
                            unique_colors.add((r, g, b))
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    return unique_colors

def create_color_map(unique_colors):
    """Creates a mapping from RGB color tuples to characters."""
    color_to_char = {}
    char_to_color = {}
    char_pool = collections.deque(AVAILABLE_CHARS)

    # 1. Try to map to default palette based on RGB values
    used_default_chars = set()
    # Use a temporary list to avoid modifying the set during iteration
    colors_to_process = list(unique_colors)
    for rgb in colors_to_process:
        found_default = False
        for char, default_rgb in DEFAULT_PALETTE_JAVA.items():
             if rgb == default_rgb:
                 if char not in used_default_chars: # Assign default char only once
                     color_to_char[rgb] = char
                     char_to_color[char] = rgb
                     used_default_chars.add(char)
                     unique_colors.remove(rgb) # Color is mapped
                     found_default = True
                     break # Stop checking defaults for this color
        # If a color matched a default, move to the next color
        if found_default:
            continue

    # 2. Assign remaining unique colors to available characters
    for color in sorted(list(unique_colors)): # Sort for deterministic assignment
        if not char_pool:
            print("Warning: Ran out of characters to assign to unique colors!")
            # Fallback: Use a placeholder or raise an error
            # For now, let's use '?' but this might cause issues in Java
            next_char = '?'
            if color not in color_to_char: # Avoid overwriting if '?' was already assigned
                 color_to_char[color] = next_char
                 if next_char not in char_to_color:
                     char_to_color[next_char] = color # Map '?' only once if possible
            continue # Skip to next color if out of chars

        # Find the next available character (skip defaults already used implicitly by char_pool def)
        next_char = char_pool.popleft()
        # The available pool already excludes default chars, so no need to check used_default_chars here

        color_to_char[color] = next_char
        char_to_color[next_char] = color

    # Ensure space (' ') is reserved for transparency and not assigned
    if ' ' in char_to_color:
        print("Warning: Space character (' ') was assigned to a color. This might conflict with transparency.")

    print(f"Mapped {len(color_to_char)} unique opaque colors to characters.")
    return color_to_char, char_to_color


def generate_palette_file(char_to_color_map, output_path):
    """Generates the ColorPalettes.txt file."""
    try:
        with open(output_path, 'w') as f:
            f.write("// Add these lines to your Java project where you initialize GameView\n")
            f.write("// or in a method that configures the color palette.\n")
            f.write("// Make sure you have a GameView instance (e.g., 'gameView').\n\n")
            # Only write updates for characters *not* in the default Java map
            # or if the color differs from the default (though our logic assigns new chars then)
            for char, color in sorted(char_to_color_map.items()):
                 # Check if this char is a default one
                is_default = char in DEFAULT_PALETTE_JAVA

                # Only write if it's NOT a default char. If it IS a default char,
                # we assume the Java code already defines it correctly.
                # (Our create_color_map logic ensures we only map default chars
                # if the color *exactly* matches the expected default RGB).
                if not is_default:
                     r, g, b = color
                     # Ensure character is properly escaped for Java char literal
                     java_char = f"'{char}'" if char != '\'' else "'\\''" # Handle single quote itself
                     java_char = java_char if char != '\\' else "'\\\\'" # Handle backslash itself

                     f.write(f"gameView.updateColorForBlockImage({java_char}, new Color({r}, {g}, {b}));\n")
        print(f"Generated color palette definition: {output_path}")
    except Exception as e:
        print(f"Error writing palette file {output_path}: {e}")


def image_to_block_string(image_path, color_map):
    """Converts an image file to a Java BlockImage string."""
    block_lines = []
    max_width = 0
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGBA") # Ensure consistent format
            width, height = img.size
            max_width = width
            pixels = img.load()
            for y in range(height):
                line = ""
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    if a == 0: # Fully transparent is space
                        line += " "
                    else:
                        # Find the character for the RGB color
                        char = color_map.get((r, g, b))
                        if char:
                            line += char
                        else:
                            # Should not happen if all colors were mapped and handled correctly
                            print(f"Warning: Color ({r},{g},{b}) with alpha {a} not found in map for {image_path}. Using '?'.")
                            line += "?"
                block_lines.append(line)

        # Pad lines with spaces to make the block rectangular if needed (usually not for pixel art)
        padded_lines = [line.ljust(max_width) for line in block_lines]
        # Format as Java text block
        java_string = '"""\n' + '\n'.join(padded_lines) + '\n"""'
        return java_string

    except Exception as e:
        print(f"Error converting image {image_path} to block string: {e}")
        return '"""\nError\n"""' # Return an error string

def generate_java_file(image_files, color_map, output_path):
    """Generates the GameBlockImages.java file."""
    try:
        with open(output_path, 'w') as f:
            f.write("package thd.gameobjects.movable;\n\n")
            # No longer adding import java.awt.Color; as it's not needed for the strings.
            f.write("/**\n")
            f.write(" * Contains static final String constants for block images.\n")
            f.write(" */\n")
            f.write("public class GameBlockImages {\n\n")
            # Private constructor to prevent instantiation
            f.write("    private GameBlockImages() {\n")
            f.write("    }\n\n")


            for image_path in image_files:
                filename = os.path.basename(image_path)
                name_without_ext = os.path.splitext(filename)[0]
                # Create a valid Java variable name (uppercase, replace invalid chars)
                variable_name = "".join(c if c.isalnum() else '_' for c in name_without_ext).upper()
                # Ensure it starts with a letter or underscore, and handle empty names
                if not variable_name or not (variable_name[0].isalpha() or variable_name[0] == '_'):
                     variable_name = "_" + variable_name # Prepend underscore if needed

                print(f"Processing {filename} -> {variable_name}...")
                block_string = image_to_block_string(image_path, color_map)

                f.write(f"    /**\n")
                f.write(f"     * BlockImage for {filename}\n")
                f.write(f"     */\n")
                f.write(f"    public static final String {variable_name} = {block_string};\n\n") # Made public static final

            f.write("}\n") # Close class
        print(f"Generated Java block images file: {output_path}")
    except Exception as e:
        print(f"Error writing Java file {output_path}: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Image to BlockImage Conversion...")
    ensure_dir(OUTPUT_DIR)

    image_files = get_image_files(INPUT_DIR)

    if not image_files:
        print(f"No image files found in {INPUT_DIR}. Exiting.")
    else:
        print(f"Found {len(image_files)} image files.")

        # 1. Analyze all colors first
        print("Analyzing colors across all images...")
        all_unique_colors = analyze_colors(image_files)
        print(f"Found {len(all_unique_colors)} unique opaque colors.")

        # 2. Create the master color map
        color_to_char_map, char_to_color_map = create_color_map(all_unique_colors.copy()) # Pass copy

        # 3. Generate Palette Definition File
        palette_path = os.path.join(OUTPUT_DIR, 'ColorPalettes.txt')
        generate_palette_file(char_to_color_map, palette_path)

        # 4. Generate Java Block Images File
        java_path = os.path.join(OUTPUT_DIR, 'GameBlockImages.java')
        generate_java_file(image_files, color_to_char_map, java_path)

        print("\nConversion complete.")
        print(f"Output files generated in: {OUTPUT_DIR}")
        print(f"  - {os.path.basename(java_path)}")
        print(f"  - {os.path.basename(palette_path)}")
        print("\n-------------------- Usage Instructions --------------------")
        print("1. Place the generated Java file (`GameBlockImages.java`) into")
        print("   the correct package folder within your Java project's source directory")
        print("   (e.g., src/thd/gameobjects/movable/GameBlockImages.java).")
        print("2. Copy the Java code lines from `ColorPalettes.txt`.")
        print("3. Paste these lines into your Java project where you initialize")
        print("   or configure your `GameView` instance. This ensures the characters")
        print("   in the block strings map to the correct colors.")
        print("   Example location: Inside the constructor or an initialization method")
        print("   where you have access to your `GameView gameView` object.")
        print("4. In your Java code, access the block images using the static constants,")
        print("   for example: `gameView.addBlockImageToCanvas(GameBlockImages.TREE, x, y, size, rotation);`")
        print("----------------------------------------------------------")


