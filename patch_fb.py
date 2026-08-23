import os, shutil

# 1. Patch schema
schema_path = r"packages\openmagpie-schema\src\openmagpie_schema\feed_payloads.py"
with open(schema_path, "r") as f:
    content = f.read()

if "FacebookPostPayload" not in content:
    fb_class = 'class FacebookPostPayload(FeedItemPayload):\n    PAYLOAD_KIND: ClassVar[str] = "facebook_post"\n\n'
    content = content.replace("FeedItemData = Annotated[", fb_class + "FeedItemData = Annotated[")
    content = content.replace("NewTweetPayload,", "NewTweetPayload | FacebookPostPayload,")
    with open(schema_path, "w") as f:
        f.write(content)
    print("[OK] Patched feed_payloads.py")
else:
    print("[SKIP] Schema already patched")

# 2. Create facebook connector package
fb_dir = r"apps\core\sources\connectors\facebook"
os.makedirs(fb_dir, exist_ok=True)

init_path = os.path.join(fb_dir, "__init__.py")
if not os.path.exists(init_path):
    open(init_path, "w").close()
    print("[OK] Created facebook/__init__.py")

# 3. Copy payload from facebook_plugin
src = r"facebook_plugin\payloads.py"
dst = os.path.join(fb_dir, "payloads.py")
if os.path.exists(src) and not os.path.exists(dst):
    shutil.copy2(src, dst)
    print("[OK] Copied payloads.py into connectors/facebook")
elif not os.path.exists(src):
    print("[WARN] facebook_plugin\payloads.py not found — create it manually")

# 4. Create connector.py with registration
conn = os.path.join(fb_dir, "connector.py")
if not os.path.exists(conn):
    with open(conn, "w") as f:
        f.write('from sources.payload_registry import register\nfrom .payloads import FacebookPostPayload\n\nregister("facebook", [FacebookPostPayload])\n')
    print("[OK] Created connector.py")

# 5. Patch apps.py to import facebook
apps_path = r"apps\core\sources\apps.py"
with open(apps_path, "r") as f:
    apps = f.read()
if "facebook" not in apps:
    apps = apps.replace("twitter", "twitter, facebook")
    with open(apps_path, "w") as f:
        f.write(apps)
    print("[OK] Patched apps.py")
else:
    print("[SKIP] apps.py already imports facebook")

print("\nDone. Run the test with:")
print(r".venv\Scripts\python.exe -m pytest apps\core\sources\tests.py::FeedItemPayloadParityTests -v")