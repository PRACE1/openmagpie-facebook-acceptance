import inspect

# 1. ActionEnvelope fields
print("=== ActionEnvelope fields ===")
from facebook_camofox_client.domain_actions.envelope import ActionEnvelope
for n, f in ActionEnvelope.model_fields.items():
    print(f"  {n}: {f.annotation}")

# 2. execute return type
print("\n=== execute return ===")
from facebook_camofox_client.domain_posts.listen import PostsListenAction
sig = inspect.signature(PostsListenAction.execute)
print(f"  return: {sig.return_annotation}")

# 3. Classes in dependency modules
print("\n=== Classes ===")
modules = [
    'facebook_camofox_client.domain_camofox.session_manager',
    'facebook_camofox_client.domain_cursors.repository',
    'facebook_camofox_client.domain_events.emitter',
]
for m in modules:
    mod = __import__(m, fromlist=[""])
    classes = [x for x in dir(mod) if not x.startswith("_") and inspect.isclass(getattr(mod, x))]
    print(f"  {m}: {classes}")