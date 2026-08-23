import inspect
import pkgutil
import facebook_camofox_client

print("=== 1. PostsListenAction.__init__ params ===")
from facebook_camofox_client.domain_posts.listen import PostsListenAction
sig = inspect.signature(PostsListenAction.__init__)
for n, p in sig.parameters.items():
    ann = p.annotation if p.annotation != inspect.Parameter.empty else "?"
    default = p.default if p.default != inspect.Parameter.empty else "required"
    print(f"  {n}: {ann} = {default}")

print("\n=== 2. PostsListenAction.execute params ===")
sig2 = inspect.signature(PostsListenAction.execute)
for n, p in sig2.parameters.items():
    ann = p.annotation if p.annotation != inspect.Parameter.empty else "?"
    default = p.default if p.default != inspect.Parameter.empty else "required"
    print(f"  {n}: {ann} = {default}")

print("\n=== 3. ActionEnvelope location & fields ===")
ae_found = False
for m in pkgutil.walk_packages(facebook_camofox_client.__path__, prefix='facebook_camofox_client.'):
    try:
        mod = __import__(m.name, fromlist=['ActionEnvelope'])
        if hasattr(mod, 'ActionEnvelope'):
            ae = mod.ActionEnvelope
            print(f"  Module: {m.name}")
            print(f"  Fields: {list(ae.model_fields.keys()) if hasattr(ae, 'model_fields') else 'N/A'}")
            ae_found = True
            break
    except Exception:
        pass
if not ae_found:
    print("  ActionEnvelope not found via walk")

print("\n=== 4. CommitCallback location ===")
cb_found = False
for m in pkgutil.walk_packages(facebook_camofox_client.__path__, prefix='facebook_camofox_client.'):
    try:
        mod = __import__(m.name, fromlist=['CommitCallback'])
        if hasattr(mod, 'CommitCallback'):
            cb = mod.CommitCallback
            print(f"  Module: {m.name}")
            print(f"  Value:  {cb}")
            cb_found = True
            break
    except Exception:
        pass
if not cb_found:
    print("  CommitCallback not found via walk")

print("\n=== 5. Relevant modules (session/cursor/normalizer/event/emit) ===")
for m in pkgutil.walk_packages(facebook_camofox_client.__path__, prefix='facebook_camofox_client.'):
    if any(x in m.name for x in ['session', 'cursor', 'normalizer', 'event', 'emit']):
        print(f"  {m.name}")

print("\n=== 6. All top-level modules ===")
for m in pkgutil.iter_modules(facebook_camofox_client.__path__, prefix='facebook_camofox_client.'):
    print(f"  {m.name}")