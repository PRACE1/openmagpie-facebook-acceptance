from pathlib import Path
import re

file_path = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
text = file_path.read_text()

print("=== All .get( occurrences ===")
lines = text.splitlines()
for i, line in enumerate(lines, 1):
    if ".get(" in line:
        print(f"  Line {i}: {line.strip()}")

# Replace post.get("field", default) and post.get("field") with getattr
# Pattern 1: post.get("field", default) -> getattr(post, "field", default)
text = re.sub(r'post\.get\("([^"]+)"\s*,\s*([^)]+)\)', r'getattr(post, "\1", \2)', text)
# Pattern 2: post.get("field") -> getattr(post, "field", None)
text = re.sub(r'post\.get\("([^"]+)"\)', r'getattr(post, "\1", None)', text)

print("\n=== Verifying no post.get( remains ===")
remaining = [line for line in text.splitlines() if "post.get(" in line]
if remaining:
    for line in remaining:
        print(f"  STILL: {line.strip()}")
else:
    print("  All post.get( replaced.")

file_path.write_text(text)
print("\nDone. Re-run the acceptance test.")