import requests
import base64
from io import BytesIO
from PIL import Image

STABLE_DIFFUSION_URL = "http://127.0.0.1:7860"

def txt2img(prompt: str, steps: int = 20) -> Image.Image:
    payload = {
        "prompt": prompt,
        "steps": steps,
    }

    try:
        response = requests.post(f"{STABLE_DIFFUSION_URL}/sdapi/v1/txt2img", json=payload)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error connecting to Stable Diffusion API: {e}")
    except ValueError:
        raise RuntimeError("Invalid JSON response from Stable Diffusion API.")

    if "images" not in result or not result["images"]:
        raise KeyError(f"'images' key not found in API response. Full response: {result}")

    image_base64 = result["images"][0].split(",", 1)[-1]
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))

def img2img(init_image: Image.Image, prompt: str, strength: float = 0.7, steps: int = 25) -> Image.Image:
    try:
        # Convert PIL image to base64
        buffered = BytesIO()
        init_image.save(buffered, format="PNG")
        b64 = base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        raise RuntimeError(f"Failed to convert initial image to base64: {e}")

    payload = {
        "init_images": [f"data:image/png;base64,{b64}"],
        "prompt": prompt,
        "strength": strength,
        "steps": steps,
    }

    try:
        response = requests.post(f"{STABLE_DIFFUSION_URL}/sdapi/v1/img2img", json=payload)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error connecting to Stable Diffusion API: {e}")
    except ValueError:
        raise RuntimeError("Invalid JSON response from Stable Diffusion API.")

    if "images" not in result or not result["images"]:
        raise KeyError(f"'images' key not found in API response. Full response: {result}")

    image_base64 = result["images"][0].split(",", 1)[-1]
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))
