import subprocess, sys

main_content = subprocess.check_output(
    ['git', 'show', 'origin/main:CHANGELOG.md']
).decode('utf-8')

print(f"main CHANGELOG.md length: {len(main_content)} chars")
print("--- First 500 chars ---")
print(repr(main_content[:500]))
print("--- ### Release: headings (first 30) ---")
lines = main_content.splitlines()
count = 0
for i, line in enumerate(lines):
    if line.startswith('### Release:'):
        print(f"  line {i}: {line[:120]}")
        count += 1
        if count >= 30:
            break
print("--- done ---")
sys.exit(0)
