'''
Functions for openAI API calls, such as creating a function call, parsing the response, and handling errors.
Used to upload files to the AI depending on the file type, and to create function calls for the AI to execute.
'''

import core.global_functions as global_functions

def create_function_call(function_name: str, arguments: dict) -> dict:
    '''
    Create a function call for the AI to execute.
    Args:
        function_name (str): The name of the function to call.
        arguments (dict): The arguments to pass to the function.
    Returns:
        dict: The function call object.
    '''
    return {
        "name": function_name,
        "arguments": arguments
    }

def parse_function_response(response: dict) -> dict:
    '''
    Parse the response from the AI after executing a function call.
    Args:
        response (dict): The response from the AI.
    Returns:
        dict: The parsed response, containing the function name and the result of the function execution.
    '''
    if "function_call" in response:
        function_name = response["function_call"]["name"]
        result = response["function_call"]["result"]
        return {
            "function_name": function_name,
            "result": result
        }
    else:
        raise ValueError("Response does not contain a function call.")


def upload_file_to_ai(file_path: str) -> dict:
    '''
    Upload a file to the AI, depending on the file type.
    If the file type is supported by the AI, it can be uploaded as is. Otherwise, it will be encoded to base64 and uploaded as a string.
    Args:
        file_path (str): The path to the file to upload.
    Returns:
        dict: The response from the AI after uploading the file, containing the file type and the file content (either as a URL or as a base64 string).
    '''
    file_type = global_functions.get_file_type(file_path)
    if file_type in ["image/jpeg", "image/png", "application/pdf"]:  # Example of supported file types
        # Upload the file as is (this is a placeholder, actual upload code will depend on the AI's API)
        return {
            "file_type": file_type,
            "file_content": f"URL_to_uploaded_{os.path.basename(file_path)}"
        }
    else:
        # Encode the file to base64 and upload as a string
        encoded_content = global_functions.encode_file_to_base64(file_path)
        return {
            "file_type": file_type,
            "file_content": encoded_content
        }
