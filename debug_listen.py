from pathlib import Path

file_path = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
lines = file_path.read_text().splitlines()

patched = []
for i, line in enumerate(lines):
    # Insert debug dump right before the for-loop that processes results
    if 'for post in raw_results.get("results", [])' in line:
        indent = len(line) - len(line.lstrip())
        s = " " * indent
        patched.append(line)
        patched.append(s + 'print("[DEBUG] raw_results type:", type(raw_results).__name__)')
        patched.append(s + 'print("[DEBUG] results count:", len(raw_results.get("results", [])))')
        patched.append(s + 'print("[DEBUG] counters:", raw_results.get("counters", {}))')
        patched.append(s + 'print("[DEBUG] degraded:", raw_results.get("degraded", False))')
        continue
    
    # Insert debug at return statement
    if line.strip().startswith("return PostsListenOutput"):
        indent = len(line) - len(line.lstrip())
        s = " " * indent
        patched.append(s + 'print("[DEBUG] Returning", len(new_posts), "posts, cursor_advanced=", cursor_advanced)')
        patched.append(line)
        continue
    
    patched.append(line)

file_path.write_text("\n".join(patched) + "\n")
print("Debug logging added to listen.py")