import urllib.request
import os

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

MODEL_PATH = "en_US-lessac-medium.onnx"
JSON_PATH = "en_US-lessac-medium.onnx.json"

def download_file(url, path):
    if not os.path.exists(path):
        print(f"Downloading {path}...")
        urllib.request.urlretrieve(url, path)
        print(f"Downloaded {path}.")
    else:
        print(f"{path} already exists.")

if __name__ == "__main__":
    download_file(MODEL_URL, MODEL_PATH)
    download_file(JSON_URL, JSON_PATH)
