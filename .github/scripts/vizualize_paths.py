import json
import re
from pathlib import Path
from PIL import Image, ImageDraw

default_step_size = 20
image_size = (600, 600)
frame_duration = 100

# Directories
pattern_dir = Path("KC-Config-Suite/Pattern_Suite")
output_dir = Path("assets/pattern_suite/path_visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

move_map = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
wasd_set = {"w", "a", "s", "d"}

# Find the latest pattern JSON with "dtcp" in the name
def find_latest_pattern_file():
    pattern = re.compile(r'_KC_Pattern_Suite_dtcp(\d+)\.x_v(\d+)_\d+\.json')
    best_file = None
    best_dt = -1
    best_v = -1

    for file in pattern_dir.glob("_KC_Pattern_Suite_dtcp*.json"):
        match = pattern.match(file.name)
        if not match:
            continue
        dt, v = int(match[1]), int(match[2])
        if dt > best_dt or (dt == best_dt and v > best_v):
            best_dt, best_v = dt, v
            best_file = file
    return best_file

def parse_directions_from_pattern(pattern_list):
    directions = []
    for entry in pattern_list:
        key = entry.get("key", "")
        duration = entry.get("duration", None)

        # Parse direction key
        parts = key.split("+")
        wasd_parts = [p.lower() for p in parts if p.lower() in wasd_set]

        # Determine movement
        if len(wasd_parts) == 1:
            directions.append((wasd_parts[0], duration))
        elif len(wasd_parts) == 2:
            # Only allow diagonals like A+W or W+A
            pair = set(wasd_parts)
            if pair in [{"w", "a"}, {"w", "d"}, {"s", "a"}, {"s", "d"}]:
                directions.append(("+".join(sorted(wasd_parts)), duration))
        # Ignore anything else (multiple non-WASD keys or junk)
    return directions

def get_vector(direction):
    if "+" in direction:
        d1, d2 = direction.split("+")
        dx1, dy1 = move_map.get(d1, (0, 0))
        dx2, dy2 = move_map.get(d2, (0, 0))
        return dx1 + dx2, dy1 + dy2
    else:
        return move_map.get(direction, (0, 0))

def generate_gif(name, directions):
    x, y = image_size[0] // 2, image_size[1] // 2
    positions = [(x, y)]

    for direction, duration in directions:
        dx, dy = get_vector(direction)

        # Normalize duration to step size
        try:
            dur = int(duration)
            step = max(5, min(100, dur // 10))  # Clamp between 5 and 100
        except (TypeError, ValueError):
            step = default_step_size

        x += dx * step
        y += dy * step
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
        print("No valid dtcp pattern file found.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_paths = []
    for pattern in data.get("pattern", []):
        # use exported_from or versioned name fallback
        name = data.get("name", "pattern")
        directions = parse_directions_from_pattern(data["pattern"])
        if not directions:
            continue

        cleaned_name = name.strip("_")
        out_gif = generate_gif(cleaned_name, directions)
        output_paths.append((cleaned_name, out_gif))
        break  # Only render one pattern per file (since name isn't nested)

    # Generate README
    readme_path = pattern_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as readme:
        readme.write("# Pattern Visualizations\n\n")
        for name, path in output_paths:
            rel_path = "/" + str(path).replace("\\", "/")
            readme.write(f"### `{name}`\n\n")
            readme.write(f"![{name}]({rel_path})\n\n")

    print("GIFs and README generated successfully.")

if __name__ == "__main__":
    main()
