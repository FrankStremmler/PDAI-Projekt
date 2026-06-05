'''
'''
import datetime
from zoneinfo import ZoneInfo
import filetype
import base64
import os


def get_file_type(file_path: str) -> str:
    """
    Get the file type of a given file path.
    Knowing the filetype can be used to determine how to handle the file, maybe upload the file as is to the AI or convert to Base64.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The MIME type of the file, or 'unknown' if it cannot be determined.
    """
    try:
        kind = filetype.guess(file_path)
        if kind is not None:
            return kind.mime
        else:
            return 'unknown'
    except Exception as e:
        raise FileNotFoundError(f"Error determining file type for {file_path}") from e


def encode_file_to_base64(file_path: str) -> str:
    """
    Encode a file to a base64 string.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The base64-encoded string of the file's contents.
    """
    try:
        with open(file_path, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        raise FileNotFoundError(f"Error encoding file {file_path} to base64") from e