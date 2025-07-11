import json
from pathlib import Path

# Bidirectional mapping for conversions
q2a = {"w": "z", "a": "q", "s": "s", "d": "d"}
a2q = {v: k for k, v in q2a.items()}
full_map = {**q2a, **a2q}

def convert_key(key: str) -> str:
    parts = key.split("+")
    new_parts = []
    for p in parts:
        if len(p) == 1:
            c = p
            c_lower = c.lower()
            mapped = full_map.get(c_lower, c_lower)
            if c.isupper():
                mapped = mapped.upper()
            new_parts.append(mapped)
        else:
            new_parts.append(p)
    return "+".join(new_parts)

def convert_pattern_json(data: dict) -> dict:
    if "pattern" in data and isinstance(data["pattern"], list):
        for entry in data["pattern"]:
            if "key" in entry:
                entry["key"] = convert_key(entry["key"])
    return data

def convert_simple_json(data: dict) -> dict:
    return {
        k: [q2a.get(c.lower(), c.lower()) for c in seq]
        for k, seq in data.items()
    }

# Set up paths
qwerty_dir = Path("KC-Config-Suite/Pattern_Suite")
azerty_dir = qwerty_dir / "AZERTY"
azerty_dir.mkdir(exist_ok=True)

qwerty_files = {f.name: f for f in qwerty_dir.glob("*.json")}
azerty_files = {f.name: f for f in azerty_dir.glob("*.json")}

# Convert each QWERTY file to AZERTY
for name, q_file in qwerty_files.items():
    az_file = azerty_dir / name
    try:
        text = q_file.read_text(encoding='utf-8-sig')
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"✖ Failed to decode JSON in: {q_file}")
        print(f"Reason: {e}")
        print("Offending content (first 20 lines):")
        print("\n".join(text.splitlines()[:20]))
        raise

    # Auto-detect format
    if isinstance(data, dict) and "pattern" in data and isinstance(data["pattern"], list):
        converted = convert_pattern_json(data)
    else:
        converted = convert_simple_json(data)

    az_file.write_text(json.dumps(converted, indent=2, ensure_ascii=False))
    print(f"Created/Updated: {az_file}")

# Delete orphan AZERTY files
for name, a_file in azerty_files.items():
    if name not in qwerty_files:
        a_file.unlink()
        print(f"Deleted orphan AZERTY file: {a_file}")
