import importlib.util

if importlib.util.find_spec("piper") is not None:
    print("piper is installed")
else:
    print("piper is NOT installed")
