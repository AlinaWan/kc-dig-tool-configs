import json
from pathlib import Path

q2a = {"w": "z", "a": "q", "s": "s", "d": "d"}

def convert(data):
    return {
        k: [q2a.get(c.lower(), c.lower()) for c in seq]
        for k, seq in data.items()
    }

qwerty_dir = Path("KC-Config-Suite/Pattern_Suite")
azerty_dir = qwerty_dir / "AZERTY"
azerty_dir.mkdir(exist_ok=True)

qwerty_files = {f.name: f for f in qwerty_dir.glob("*.json")}
azerty_files = {f.name: f for f in azerty_dir.glob("*.json")}

# 1. Generate AZERTY versions from QWERTY
for name, q_file in qwerty_files.items():
    az_file = azerty_dir / name
    if not az_file.exists():
        data = json.loads(q_file.read_text())
        converted = convert(data)
        az_file.write_text(json.dumps(converted, indent=2))
        print(f"Created: {az_file}")

# 2. Delete orphan AZERTY files
for name, a_file in azerty_files.items():
    if name not in qwerty_files:
        a_file.unlink()
        print(f"Deleted orphan AZERTY file: {a_file}")
