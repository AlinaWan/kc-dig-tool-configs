import re
import subprocess
from datetime import date
from pathlib import Path

README = Path("README.md")
TODAY = date.today().isoformat()

# 1. Get changed shovel blocks using git diff
diff_output = subprocess.run(
    ["git", "diff", "HEAD~1", "HEAD", "--unified=0", "--", str(README)],
    capture_output=True, text=True
).stdout

# 2. Parse which shovel names changed
changed_shovels = set(re.findall(r"^\+### (.+?) Shovel", diff_output, re.MULTILINE))

if not changed_shovels:
    print("No shovel sections changed. Exiting.")
    exit(0)

print(f"Detected updated shovel sections: {changed_shovels}")

# 3. Read README.md
text = README.read_text(encoding="utf-8")
lines = text.splitlines()

# 4. Process each section
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    shovel_match = re.match(r"### (.+?) Shovel", line)
    if shovel_match:
        shovel_name = shovel_match.group(1)
        output_lines.append(line)
        i += 1

        # Copy the rest of the section
        section_lines = []
        while i < len(lines):
            if re.match(r"### .+? Shovel", lines[i]):  # next shovel starts
                break
            section_lines.append(lines[i])
            i += 1

        # Remove any existing Last updated line
        if section_lines and re.match(r"<sub><sup>Last updated: \d{4}-\d{2}-\d{2}</sup></sub>", section_lines[-1]):
            section_lines.pop()

        # If shovel changed, append the update line
        if shovel_name in changed_shovels:
            # Ensure spacing rule: at least one blank line before the update tag
            if section_lines and section_lines[-1].strip() != "":
                section_lines.append("")
            section_lines.append(f"<sub><sup>Last updated: {TODAY}</sup></sub>")
        output_lines.extend(section_lines)
    else:
        output_lines.append(line)
        i += 1

# 5. Overwrite if changes occurred
new_text = "\n".join(output_lines) + "\n"
if new_text != text:
    README.write_text(new_text, encoding="utf-8")
    print("README.md updated with new timestamps.")
else:
    print("README.md already up to date.")