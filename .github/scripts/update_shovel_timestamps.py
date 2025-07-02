import re
import subprocess
from datetime import date
from pathlib import Path

README = Path("README.md")
TODAY = date.today().isoformat()

# Step 1: Get diff of README between previous and current commit
diff_output = subprocess.run(
    ["git", "diff", "HEAD~1", "HEAD", "--unified=0", "--", str(README)],
    capture_output=True,
    text=True,
).stdout

# Step 2: Find changed ### headings from the diff
changed_sections = set(re.findall(r"^\+### (.+)", diff_output, re.MULTILINE))

if not changed_sections:
    print("No subsection headings under ### changed — skipping update.")
    exit(0)

print(f"Detected changed subsections: {changed_sections}")

# Step 3: Read README content
text = README.read_text(encoding="utf-8")
lines = text.splitlines()

# Step 4: Parse and rewrite tool sections
output_lines = []
inside_tools_section = False
i = 0

while i < len(lines):
    line = lines[i]

    # Activate parsing only after this heading
    if line.strip() == "## 🪄 Best Enchants, Stat Priorities, and Charm Sets":
        inside_tools_section = True
        output_lines.append(line)
        i += 1
        continue

    # While inside the tools section, look for ### subsections
    if inside_tools_section and line.startswith("### "):
        section_header = line
        section_name = line[4:].strip()
        output_lines.append(section_header)
        i += 1

        section_lines = []

        while i < len(lines):
            if lines[i].startswith("### ") or lines[i].startswith("## "):
                break
            section_lines.append(lines[i])
            i += 1

        # Remove trailing blank lines
        while section_lines and section_lines[-1].strip() == "":
            section_lines.pop()

        # Remove existing update line if present
        if section_lines and re.match(r"<sub><sup>Last updated: \d{4}-\d{2}-\d{2}</sup></sub>", section_lines[-1]):
            section_lines.pop()
            while section_lines and section_lines[-1].strip() == "":
                section_lines.pop()

        # If this section changed, add a fresh timestamp
        if section_name in changed_sections:
            section_lines.append("")  # Required empty line
            section_lines.append(f"<sub><sup>Last updated: {TODAY}</sup></sub>")
            print(f"Updated timestamp for section: {section_name}")

        output_lines.extend(section_lines)
        continue

    # If we're past the enchant section or before it, just copy lines
    output_lines.append(line)
    i += 1

# Step 5: Write new content if changed
new_text = "\n".join(output_lines) + "\n"
if new_text != text:
    README.write_text(new_text, encoding="utf-8")
    print("README.md updated with new timestamps.")
else:
    print("README.md already up to date. No changes made.")