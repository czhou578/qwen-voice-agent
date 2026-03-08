import subprocess

try:
    result = subprocess.run(["python", "-c", "import piper; print('PIPER_IS_HERE')"], capture_output=True, text=True, timeout=10)
    with open("result.txt", "w") as f:
        f.write("STDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr)
except Exception as e:
    with open("result.txt", "w") as f:
        f.write(str(e))
