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
            # Preserve original case
            if c.isupper():
                mapped = mapped.upper()
            new_parts.append(mapped)
        else:
            # Leave multi-char parts as-is (modifiers or words)
            new_parts.append(p)
    return "+".join(new_parts)

def convert_pattern_json(data):
    # Only transform keys inside the "pattern" list
    if "pattern" in data and isinstance(data["pattern"], list):
        for entry in data["pattern"]:
            if "key" in entry:
                entry["key"] = convert_key(entry["key"])
    return data

def convert_simple_json(data):
    # Old format: dict of sequences, convert characters one-way q2a
    return {
        k: [q2a.get(c.lower(), c.lower()) for c in seq]
        for k, seq in data.items()
    }

qwerty_dir = Path("KC-Config-Suite/Pattern_Suite")
azerty_dir = qwerty_dir / "AZERTY"
azerty_dir.mkdir(exist_ok=True)

qwerty_files = {f.name: f for f in qwerty_dir.glob("*.json")}
azerty_files = {f.name: f for f in azerty_dir.glob("*.json")}

for name, q_file in qwerty_files.items():
    az_file = azerty_dir / name
    data = json.loads(q_file.read_text())
    
    if "dtcp" in name:
        # New JSON pattern format with keys in "pattern" array
        converted = convert_pattern_json(data)
    else:
        # Old simple dict-of-sequences format
        converted = convert_simple_json(data)
    
    az_file.write_text(json.dumps(converted, indent=2, ensure_ascii=False))
    print(f"Created/Updated: {az_file}")

# Delete orphan AZERTY files
for name, a_file in azerty_files.items():
    if name not in qwerty_files:
        a_file.unlink()
        print(f"Deleted orphan AZERTY file: {a_file}")
