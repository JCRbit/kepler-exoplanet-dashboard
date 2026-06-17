import base64

def get_base64_image(image_path: str) -> str:
    """
    Reads a local image and converts it to a Base64 string 
    for secure embedding within Streamlit HTML components.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()