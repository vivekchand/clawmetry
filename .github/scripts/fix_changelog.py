import subprocess, sys, re

# Get main's content (current)
main_content = subprocess.check_output(
    ['git', 'show', 'origin/main:CHANGELOG.md']
).decode('utf-8')

# Get original branch CHANGELOG from before the accidental overwrite
orig_content = subprocess.check_output(
    ['git', 'show', '353860e5:CHANGELOG.md']
).decode('utf-8')

print(f"main: {len(main_content)} chars, orig branch: {len(orig_content)} chars")

# Get all ### Release: headings from both
def get_headings(content):
    return [m.group(0) for m in re.finditer(r'^### Release:[^\n]*', content, re.MULTILINE)]

main_headings = get_headings(main_content)
orig_headings = get_headings(orig_content)

print(f"Main headings ({len(main_headings)}): {main_headings}")
print(f"Orig headings (first 5): {orig_headings[:5]}")

# Find headings in main that are NOT in orig (unique to main = new since branch diverged)
orig_heading_set = set(orig_headings)
unique_to_main = [h for h in main_headings if h not in orig_heading_set]
print(f"Unique to main: {unique_to_main}")

# Find first heading that is common to both (branch had it before diverging)
first_common = None
for h in main_headings:
    if h in orig_heading_set:
        first_common = h
        break
print(f"First common heading: {first_common}")

if not first_common:
    print("ERROR: No common headings found between main and original branch", file=sys.stderr)
    sys.exit(1)

# Build merged content:
# [main's header + unique-to-main sections] + [original branch content from first_common onward]
# This preserves all of main's new work AND the branch's hook-collision section

first_common_idx_main = main_content.find(first_common)
main_prefix = main_content[:first_common_idx_main]

first_common_idx_orig = orig_content.find(first_common)
orig_suffix = orig_content[first_common_idx_orig:]

merged = main_prefix + orig_suffix
print(f"Merged: {len(merged)} chars")

# Verify key sections are present
HOOK = "### Release: ClawMetry will never delete another tool"
KILL = "### Release: the kill switch"

if HOOK not in merged:
    print("ERROR: hook-collision section NOT in merged result!", file=sys.stderr)
    sys.exit(1)
if KILL not in merged:
    print("ERROR: kill switch section NOT in merged result!", file=sys.stderr)
    sys.exit(1)

print(f"kill switch at idx: {merged.find(KILL)}")
print(f"first_common at idx: {merged.find(first_common)}")
print(f"hook-collision at idx: {merged.find(HOOK)}")

with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
    f.write(merged)
print("Success - wrote merged CHANGELOG.md")
