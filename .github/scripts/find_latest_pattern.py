import re
import sys
from pathlib import Path

def parse_version(filename):
    # Expected filename example:
    # _KC_Pattern_Suite_dtcp2.x_v4_20250630.json
    pattern = re.compile(r'_KC_Pattern_Suite_dt1\.5\.3\+_v(\d+)_\d+\.json')
    m = pattern.match(filename)
    if not m:
        return None
    dt = int(m.group(1))
    v = int(m.group(2))
    return (dt, v)

def find_latest_file(directory):
    files = list(Path(directory).glob('_KC_Pattern_Suite_dtcp*.json'))
    parsed_files = []
    for f in files:
        ver = parse_version(f.name)
        if ver is not None:
            parsed_files.append((ver, f))
    if not parsed_files:
        return None
    # Sort by dt, then v descending (highest last)
    parsed_files.sort(key=lambda x: (x[0][0], x[0][1]))
    return parsed_files[-1][1]

if __name__ == "__main__":
    directory = sys.argv[1]
    latest = find_latest_file(directory)
    if latest:
        print(str(latest))
    else:
        print("")
