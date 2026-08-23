import inspect
from facebook_camofox_client.domain_camofox.session_manager import CamofoxSessionManager

print("=== CamofoxSessionManager.__init__ ===")
sig = inspect.signature(CamofoxSessionManager.__init__)
for n, p in sig.parameters.items():
    ann = p.annotation if p.annotation != inspect.Parameter.empty else "?"
    default = p.default if p.default != inspect.Parameter.empty else "required"
    print(f"  {n}: {ann} = {default}")

print("\n=== CamofoxSessionManager class doc ===")
print(CamofoxSessionManager.__doc__ or "(no docstring)")

print("\n=== CamofoxSessionManager methods ===")
for name, meth in inspect.getmembers(CamofoxSessionManager, predicate=inspect.isfunction):
    if not name.startswith("_"):
        print(f"  {name}{inspect.signature(meth)}")