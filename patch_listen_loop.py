from pathlib import Path

file_path = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
lines = file_path.read_text().splitlines()

patched = []
in_loop = False

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Detect: for post in raw_results.get("results", []):
    if stripped.startswith('for post in raw_results.get("results", [])'):
        in_loop = True
        patched.append(line)
        # Insert conversion right after the for-loop line
        indent = len(line) - len(line.lstrip())
        spaces = " " * (indent + 4)
        patched.append(f"{spaces}# Convert dataclass instance to dict for downstream dict-only code")
        patched.append(f"{spaces}if hasattr(post, '__dict__'):")
        patched.append(f"{spaces}    post = post.__dict__")
        continue
    
    patched.append(line)

file_path.write_text("\n".join(patched) + "\n")
print("Patched listen.py loop to convert ExtractedPost -> dict.")