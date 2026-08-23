from pathlib import Path
import re

file_path = Path(r"C:\Users\R5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
lines = file_path.read_text().splitlines()

print("=== Current .get( lines in listen.py ===")
for i, line in enumerate(lines, 1):
    if ".get(" in line:
        print(f"  Line {i}: {line.strip()}")

# Patch _is_degraded: replace post.get("x", y) with getattr(post, "x", y)
patched = []
in_target_func = False
func_start = -1

for i, line in enumerate(lines):
    stripped = line.strip()
    
    if stripped.startswith("def _is_degraded("):
        in_target_func = True
        func_start = i
        print(f"\n>>> Patching _is_degraded (starts at line {i+1})")
    
    if in_target_func:
        # End of function: next non-indented, non-blank, non-comment line
        if i > func_start and stripped and not line.startswith(" ") and not stripped.startswith("#"):
            in_target_func = False
            print(f">>> End of _is_degraded (before line {i+1})")
        
        if in_target_func and ".get(" in line:
            # Replace var.get("field", default) with getattr(var, "field", default)
            new_line = re.sub(r'(\w+)\.get\("([^"]+)"\s*,\s*([^)]+)\)', r'getattr(\1, "\2", \3)', line)
            if new_line != line:
                print(f"  Patched line {i+1}")
                print(f"    FROM: {line.strip()}")
                print(f"      TO: {new_line.strip()}")
                line = new_line
    
    patched.append(line)

file_path.write_text("\n".join(patched) + "\n")
print("\nDone. Re-run the acceptance test.")