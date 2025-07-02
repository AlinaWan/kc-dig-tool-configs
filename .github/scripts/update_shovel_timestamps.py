import re
import subprocess
from datetime import date
from pathlib import Path

README = Path("README.md")
TODAY = date.today().isoformat()

def get_changed_lines():
    """Return a set of line numbers in README.md that changed in the last commit."""
    diff_output = subprocess.run(
        ["git", "diff", "HEAD~1", "HEAD", "-U0", "--", str(README)],
        capture_output=True, text=True
    ).stdout

    changed_lines = set()
    # Parse diff hunk headers for line numbers of changes
    for line in diff_output.splitlines():
        if line.startswith("@@"):
            # Example hunk line: @@ -24,0 +25,3 @@
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) else 1
                changed_lines.update(range(start, start + count))
    return changed_lines

def find_footer_start(lines):
    """Return the line index where the footer comment starts, or None if not found."""
    for i, line in enumerate(lines):
        if "<!-- OPTIMIZATION FOOTER -->" in line:
            return i
    return None

def parse_shovel_sections(lines, footer_start):
    """Parse shovel sections bounded by '###' headers, ignoring lines after footer."""
    sections = []
    current_section = None
    for i, line in enumerate(lines):
        # Stop parsing shovel sections if footer start reached
        if footer_start is not None and i >= footer_start:
            break

        # Detect shovel subsection header (### ...), e.g. "### Glinted Shovel"
        if re.match(r"### .+", line):
            # Close previous section
            if current_section:
                current_section['end'] = i - 1
                sections.append(current_section)
            current_section = {'title': line.strip()[4:], 'start': i, 'end': None}

    # Close last section before footer or EOF
    if current_section:
        # If footer exists, end at line before footer; else at EOF
        current_section['end'] = (footer_start - 1) if footer_start is not None else len(lines) - 1
        sections.append(current_section)

    return sections

def update_timestamps():
    text = README.read_text(encoding="utf-8")
    lines = text.splitlines()

    changed_lines = get_changed_lines()
    footer_start = find_footer_start(lines)
    sections = parse_shovel_sections(lines, footer_start)

    # Determine which shovel sections have changed lines
    changed_sections = set()
    for section in sections:
        if any(line_num >= section['start'] and line_num <= section['end'] for line_num in changed_lines):
            changed_sections.add(section['title'])

    if not changed_sections:
        print("No shovel sections changed.")
        return

    print(f"Changed shovel sections: {changed_sections}")

    output_lines = []
    i = 0
    while i < len(lines):
        # Stop appending shovel sections once footer reached, append footer and beyond as is
        if footer_start is not None and i == footer_start:
            # Append footer and everything after as is
            output_lines.extend(lines[i:])
            break

        line = lines[i]
        header_match = re.match(r"### (.+)", line)
        if header_match and (footer_start is None or i < footer_start):
            shovel_title = header_match.group(1)
            output_lines.append(line)
            i += 1

            # Gather section content
            section_content = []
            while i < len(lines):
                if (footer_start is not None and i >= footer_start) or re.match(r"### .+", lines[i]):
                    break
                section_content.append(lines[i])
                i += 1

            # Remove existing timestamp line if present at the end of section_content
            if section_content and re.match(r"<sub><sup>Last updated: \d{4}-\d{2}-\d{2}</sup></sub>", section_content[-1]):
                section_content.pop()

            # Append new timestamp if this section changed
            if shovel_title in changed_sections:
                # Ensure exactly one blank line before timestamp
                while section_content and section_content[-1].strip() == "":
                    section_content.pop()
                section_content.append("")  # one blank line
                section_content.append(f"<sub><sup>Last updated: {TODAY}</sup></sub>")

            output_lines.extend(section_content)
        else:
            # Lines outside shovel sections and before footer (if any)
            output_lines.append(line)
            i += 1

    new_text = "\n".join(output_lines) + "\n"
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print("README.md updated with new timestamps.")
    else:
        print("README.md already up to date.")

if __name__ == "__main__":
    update_timestamps()
