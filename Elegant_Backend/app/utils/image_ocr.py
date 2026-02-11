from google.cloud import vision
from google.oauth2 import service_account

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    creds = service_account.Credentials.from_service_account_file(
        r"C:\credentials\google_vision_api.json"
    )

    client = vision.ImageAnnotatorClient(credentials=creds)

    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    if not response.text_annotations:
        return ""

    return response.text_annotations[0].description
