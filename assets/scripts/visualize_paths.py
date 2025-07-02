import json
import re
from pathlib import Path
from PIL import Image, ImageDraw

step_size = 20
image_size = (600, 600)
frame_duration = 100

# Directories
pattern_dir = Path("KC-Config-Suite/Pattern_Suite")
output_dir = Path("assets/pattern_suite/path_visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

move_map = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}

def find_latest_pattern_file():
    pattern = re.compile(r'_KC_Pattern_Suite_dt(\d+)\.x_v(\d+)_\d+\.json')
    best_file = None
    best_dt = -1
    best_v = -1

    for file in pattern_dir.glob("_KC_Pattern_Suite_dt*.json"):
        match = pattern.match(file.name)
        if not match:
            continue
        dt, v = int(match[1]), int(match[2])
        if dt > best_dt or (dt == best_dt and v > best_v):
            best_dt, best_v = dt, v
            best_file = file
    return best_file

def generate_gif(name, directions):
    x, y = image_size[0] // 2, image_size[1] // 2
    positions = [(x, y)]
    for move in directions:
        dx, dy = move_map.get(move, (0, 0))
        x += dx * step_size
        y += dy * step_size
        positions.append((x, y))

    frames = []
    for i in range(1, len(positions)):
        img = Image.new("RGB", image_size, "white")
        draw = ImageDraw.Draw(img)
        draw.line(positions[:i+1], fill="blue", width=3)
        cx, cy = positions[i]
        draw.ellipse((cx-4, cy-4, cx+4, cy+4), fill="red")
        frames.append(img)

    out_path = output_dir / f"{name}.gif"
    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=frame_duration, loop=0)
    return out_path

def main():
    json_file = find_latest_pattern_file()
    if not json_file:
        print("No valid pattern suite file found.")
        return

    with open(json_file, "r") as f:
        data = json.load(f)

    output_paths = []
    for name, directions in data.items():
        cleaned_name = name.strip("_")
        out_gif = generate_gif(cleaned_name, directions)
        output_paths.append((cleaned_name, out_gif))

    # Generate README
    readme_path = pattern_dir / "README.md"
    with open(readme_path, "w") as readme:
        readme.write("# Pattern Visualizations\n\n")
        for name, path in output_paths:
            rel_path = "/" + str(path).replace("\\", "/")
            readme.write(f"### `{name}`\n\n")
            readme.write(f"![{name}]({rel_path})\n\n")

    print("GIFs and README generated successfully.")

if __name__ == "__main__":
    main()