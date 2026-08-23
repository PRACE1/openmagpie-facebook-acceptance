import json

with open(r"C:\Users\R5 5600 GT\openmagpie\live_acceptance_305056891435827_20260823_133744.json", "r", encoding="utf-8") as f:
    raw = f.read()

print("=== RAW FILE PREVIEW (first 500 chars) ===")
print(repr(raw[:500]))
print()

# Try to parse
try:
    data = json.loads(raw)
    print(f"Type after json.load: {type(data)}")
    if isinstance(data, list):
        print(f"List length: {len(data)}")
        if data:
            print(f"First item type: {type(data[0])}")
            print(f"First item preview: {repr(str(data[0])[:300])}")
            if isinstance(data[0], str):
                inner = json.loads(data[0])
                print(f"Parsed inner type: {type(inner)}")
                print(f"Inner keys: {list(inner.keys()) if isinstance(inner, dict) else 'N/A'}")
except Exception as e:
    print(f"Parse error: {e}")
