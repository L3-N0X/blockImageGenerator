import os
from PIL import Image
import collections
import re  # Import regular expressions for more robust parsing

# --- Configuration ---
INPUT_DIR = "./input"
OUTPUT_DIR = "./output"
# DEFAULT_PALETTE_JAVA remains the same as in the uploaded script
DEFAULT_PALETTE_JAVA = {
    "R": (255, 0, 0),
    "r": (192, 0, 0),
    "G": (0, 255, 0),
    "g": (0, 192, 0),
    "B": (0, 0, 255),
    "b": (0, 0, 192),
    "Y": (255, 255, 0),
    "y": (192, 192, 0),
    "P": (255, 175, 175),
    "p": (192, 131, 131),
    "C": (0, 255, 255),
    "c": (0, 192, 192),
    "M": (255, 0, 255),
    "m": (192, 0, 192),
    "O": (255, 200, 0),
    "o": (192, 150, 0),
    "W": (255, 255, 255),
    "L": (0, 0, 0),
}
# AVAILABLE_CHARS remains the same
AVAILABLE_CHARS = (
    [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in DEFAULT_PALETTE_JAVA]
    + [c for c in "abcdefghijklmnopqrstuvwxyz" if c not in DEFAULT_PALETTE_JAVA]
    + [str(i) for i in range(10)]
)
# Category for images without a clear category_ prefix
DEFAULT_CATEGORY = "General"

# --- Helper Functions (ensure_dir, get_image_files, analyze_colors, create_color_map, generate_palette_file - mostly unchanged from uploaded script) ---


def ensure_dir(directory):
    """Creates the directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def natural_sort_key(s):
    """Sort helper that handles embedded numbers in strings naturally."""
    return [
        int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)
    ]


def get_image_files(directory):
    """Gets a list of image filenames from the input directory."""
    files = []
    if not os.path.isdir(directory):
        print(f"Error: Input directory '{directory}' not found.")
        return files
    for filename in os.listdir(directory):
        if filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
        ):
            files.append(os.path.join(directory, filename))
    # Natural sort files for consistent, human-friendly order in generated Java file
    files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    return files


def analyze_colors(image_files):
    """Analyzes images to find unique opaque colors."""
    unique_colors = set()
    for filepath in image_files:
        try:
            with Image.open(filepath) as img:
                img = img.convert("RGBA")
                width, height = img.size
                pixels = img.load()
                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[x, y]
                        if a > 0:
                            unique_colors.add((r, g, b))
        except Exception as e:
            print(f"Error processing colors in {filepath}: {e}")
    return unique_colors


def create_color_map(unique_colors):
    """Creates a mapping from RGB color tuples to characters."""
    color_to_char = {}
    char_to_color = {}
    char_pool = collections.deque(AVAILABLE_CHARS)
    used_default_chars = set()
    colors_to_process = list(unique_colors)

    # Try mapping default colors first
    for rgb in list(colors_to_process):  # Iterate over a copy
        found_default = False
        for char, default_rgb in DEFAULT_PALETTE_JAVA.items():
            if rgb == default_rgb:
                if char not in used_default_chars:
                    color_to_char[rgb] = char
                    char_to_color[char] = rgb
                    used_default_chars.add(char)
                    unique_colors.remove(rgb)
                    colors_to_process.remove(rgb)  # Remove from processing list too
                    found_default = True
                    break
        if found_default:
            continue

    # Assign remaining unique colors
    for color in sorted(list(unique_colors)):
        if not char_pool:
            print("Warning: Ran out of characters to assign!")
            next_char = "?"
            if color not in color_to_char:
                color_to_char[color] = next_char
                if next_char not in char_to_color:
                    char_to_color[next_char] = color
            continue

        next_char = char_pool.popleft()
        color_to_char[color] = next_char
        char_to_color[next_char] = color

    if " " in char_to_color:
        print("Warning: Space character (' ') assigned to a color.")
    print(f"Mapped {len(color_to_char)} unique opaque colors.")
    return color_to_char, char_to_color


def generate_palette_file(char_to_color_map, output_path):
    """Generates the ColorPalettes.txt file (respects user request for no weird comments)."""
    try:
        with open(output_path, "w") as f:
            # Keep comments minimal as requested
            f.write("// Java code for GameView color palette updates:\n")
            for char, color in sorted(char_to_color_map.items()):
                is_default = char in DEFAULT_PALETTE_JAVA
                if not is_default:
                    r, g, b = color
                    java_char = f"'{char}'" if char != "'" else "'\\''"
                    java_char = java_char if char != "\\" else "'\\\\'"
                    f.write(
                        f"gameView.updateColorForBlockImage({java_char}, new Color({r}, {g}, {b}));\n"
                    )
        print(f"Generated color palette definition: {output_path}")
    except Exception as e:
        print(f"Error writing palette file {output_path}: {e}")


def image_to_block_string(image_path, color_map):
    """Converts an image file to a Java BlockImage string (unchanged except for trailing space removal)."""
    block_lines = []
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGBA")
            width, height = img.size
            pixels = img.load()
            for y in range(height):
                line = ""
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    if a == 0:
                        line += " "
                    else:
                        char = color_map.get((r, g, b))
                        if char:
                            line += char
                        else:
                            print(
                                f"Warning: Color ({r},{g},{b}) alpha {a} not in map for {image_path}. Using '?'."
                            )
                            line += "?"
                block_lines.append(line)
        # Remove trailing spaces from each line
        trimmed_lines = [line.rstrip() for line in block_lines]
        java_string = '"""\n' + "\n".join(trimmed_lines) + '\n"""'
        return java_string
    except Exception as e:
        print(f"Error converting {image_path}: {e}")
        return '"""\nError\n"""'


def generate_java_file(
    image_files, color_map, output_path, grouping_mode, group_output_type
):
    """
    Generates the GameBlockImages.java file according to user options.
    grouping_mode: 'grouped' or 'flat'
    group_output_type: 'class' or 'enum' (only relevant if grouping_mode == 'grouped')
    """
    import collections
    import re

    categorized_images = collections.defaultdict(list)
    for image_path in image_files:
        filename = os.path.basename(image_path)
        name_without_ext = os.path.splitext(filename)[0]
        parts = name_without_ext.split("_", 1)
        if grouping_mode == "grouped" and len(parts) == 2:
            category_name = parts[0].capitalize()
            image_name = parts[1]
        else:
            category_name = "General"
            image_name = name_without_ext
        variable_name = re.sub(r"\W|^(?=\d)", "_", image_name).upper()
        if not variable_name or not (
            variable_name[0].isalpha() or variable_name[0] == "_"
        ):
            variable_name = "_" + variable_name
        categorized_images[category_name].append(
            {"path": image_path, "filename": filename, "variable_name": variable_name}
        )
    try:
        with open(output_path, "w") as f:
            f.write("package thd.gameobjects.movable;\n\n")
            f.write("public class GameBlockImages {\n\n")
            f.write("    private GameBlockImages() {}\n\n")
            f.write("    static final double BLOCK_SIZE = 4;\n\n")
            if grouping_mode == "flat":
                for group in categorized_images.values():
                    # Natural sort within group
                    for img_info in sorted(
                        group, key=lambda x: natural_sort_key(x["filename"])
                    ):
                        block_string = image_to_block_string(
                            img_info["path"], color_map
                        )
                        f.write(
                            f"    static final String {img_info['variable_name']} = {block_string};\n\n"
                        )
            else:
                for category in sorted(categorized_images.keys()):
                    group = categorized_images[category]
                    if group_output_type == "class":
                        f.write(f"    static class {category} {{\n\n")
                        f.write(f"        private {category}() {{}}\n\n")
                        for img_info in sorted(
                            group, key=lambda x: natural_sort_key(x["filename"])
                        ):
                            block_string = image_to_block_string(
                                img_info["path"], color_map
                            )
                            f.write(
                                f"        static final String {img_info['variable_name']} = {block_string};\n\n"
                            )
                        f.write("    }\n\n")
                    elif group_output_type == "enum":
                        f.write(f"    enum {category}Tiles {{\n")
                        sorted_group = sorted(
                            group, key=lambda x: natural_sort_key(x["filename"])
                        )
                        for i, img_info in enumerate(sorted_group):
                            block_string = image_to_block_string(
                                img_info["path"], color_map
                            )
                            comma = "," if i < len(sorted_group) - 1 else ";"
                            f.write(
                                f"        {img_info['variable_name']}({block_string}){comma}\n"
                            )
                        f.write("        private final String tile;\n")
                        f.write(
                            f"        {category}Tiles(String tile) {{ this.tile = tile; }}\n"
                        )
                        f.write(
                            "        @Override public String toString() { return tile; }\n"
                        )
                        f.write("    }\n\n")
            f.write("}\n")
        print(f"Generated Java block images file: {output_path}")
    except Exception as e:
        print(f"Error writing Java file {output_path}: {e}")


# --- Main Execution (updated) ---
if __name__ == "__main__":
    print("Starting Image to BlockImage Conversion...")
    ensure_dir(OUTPUT_DIR)
    image_files = get_image_files(INPUT_DIR)

    if not image_files:
        print(f"No image files found in {INPUT_DIR}. Exiting.")
    else:
        print(f"Found {len(image_files)} image files.")

        print("Analyzing colors across all images...")
        all_unique_colors = analyze_colors(image_files)
        print(f"Found {len(all_unique_colors)} unique opaque colors.")

        color_to_char_map, char_to_color_map = create_color_map(
            all_unique_colors.copy()
        )

        palette_path = os.path.join(OUTPUT_DIR, "ColorPalettes.txt")
        generate_palette_file(char_to_color_map, palette_path)

        print("\nHow do you want to organize the output Java class?")
        print("1. Group images by prefix (sub-classes/enums, e.g. CarTiles.ROT_0)")
        print("2. All images as static final Strings in one class")
        while True:
            choice1 = input("Enter 1 or 2: ").strip()
            if choice1 in ("1", "2"):
                break
        if choice1 == "1":
            print("\nHow should each group be represented?")
            print("1. As static inner classes (each image as static final String)")
            print("2. As enums (each image as an enum constant with the image string)")
            while True:
                choice2 = input("Enter 1 or 2: ").strip()
                if choice2 in ("1", "2"):
                    break
            group_output_type = "class" if choice2 == "1" else "enum"
            grouping_mode = "grouped"
        else:
            grouping_mode = "flat"
            group_output_type = None

        java_path = os.path.join(OUTPUT_DIR, "GameBlockImages.java")
        generate_java_file(
            image_files, color_to_char_map, java_path, grouping_mode, group_output_type
        )

        print("\nConversion complete.")
        print(f"Output files generated in: {OUTPUT_DIR}")
        print(f"  - {os.path.basename(java_path)}")
        print(f"  - {os.path.basename(palette_path)}")
        print("\n-------------------- Usage Instructions --------------------")
        print("1. Place `GameBlockImages.java` into the correct package folder.")
        print("2. Add code from `ColorPalettes.txt` to your GameView setup.")
        print("3. Access images as appropriate for your chosen format.")
        print("4. Ensure Pillow is installed (`pip install Pillow`).")
        print("----------------------------------------------------------")
