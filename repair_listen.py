from pathlib import Path

file_path = Path(r"C:\Users\5 5600 GT\facebook-camofox-client\src\facebook_camofox_client\domain_posts\listen.py")
lines = file_path.read_text(encoding="utf-8").splitlines()

# Find the for-loop and rewrite the block cleanly
output = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Find the for-loop line
    if 'for post in raw_results.get("results", [])' in line:
        indent = len(line) - len(line.lstrip())
        body = " " * (indent + 4)
        
        output.append(line)
        output.append(body + "post = post_to_dict(post)  # boundary: dataclass -> dict")
        output.append(body + "if _is_degraded(post):")
        output.append(body + "    continue")
        output.append(body + "normalized = self.normalizer.normalize(post, envelope.account_id, envelope.action_type)")
        output.append(body + "new_posts.append(normalized)")
        
        # Skip ahead past the old broken block until we find the next non-indented line or return
        i += 1
        while i < len(lines):
            next_line = lines[i]
            # Stop when we hit a line at same or lower indentation that's not blank/comment
            stripped = next_line.strip()
            if stripped and not stripped.startswith("#"):
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= indent:
                    break
            i += 1
        continue
    
    output.append(line)
    i += 1

file_path.write_text("\n".join(output) + "\n", encoding="utf-8")
print("Repaired listen.py loop block.")