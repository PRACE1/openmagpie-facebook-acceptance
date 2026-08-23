from pathlib import Path

file_path = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
lines = file_path.read_text().splitlines()

patched = []
added_import = False

for line in lines:
    # Strip old debug lines
    if "[DEBUG]" in line:
        continue
    
    # Add dataclasses import if missing
    if not added_import and (line.strip().startswith("import ") or line.strip().startswith("from ")):
        if "import dataclasses" not in line:
            patched.append("import dataclasses")
            added_import = True
    
    # Revert _is_degraded back to dict .get() (posts are now dicts)
    if 'getattr(post, "post_id", "")' in line:
        patched.append(line.replace('getattr(post, "post_id", "")', 'post.get("post_id", "")'))
        continue
    if 'getattr(post, "text", None)' in line:
        patched.append(line.replace('getattr(post, "text", None)', 'post.get("text")'))
        continue
    
    # Replace __dict__ hack with proper asdict
    if "post = post.__dict__" in line:
        indent = len(line) - len(line.lstrip())
        patched.append(" " * indent + "post = dataclasses.asdict(post)")
        continue
    
    patched.append(line)

file_path.write_text("\n".join(patched) + "\n")
print("Fixed: _is_degraded uses dict .get(), loop uses dataclasses.asdict(post)")