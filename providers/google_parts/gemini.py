import os


def get_client() -> "genai.Client":
    from google import genai
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY in .env nicht gesetzt")
    return genai.Client(api_key=api_key)


def upload_file(client: "genai.Client", file_path: str, mime_type: str):
    from google.genai import types
    with open(file_path, "rb") as f:
        uploaded_file = client.files.upload(
            file=f,
            config=types.UploadFileConfig(mime_type=mime_type)
        )
    return uploaded_file


def generate_structured(
    client: "genai.Client",
    model: str,
    prompt: str,
    file_path: str,
    mime_type: str,
    response_schema: type,
    temperature: float = 0.1,
):
    from google.genai import types
    uploaded_file = upload_file(client, file_path, mime_type)
    try:
        response = client.models.generate_content(
            model=model,
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=temperature,
            ),
        )
        return response.text, uploaded_file
    except Exception:
        client.files.delete(name=uploaded_file.name)
        raise
