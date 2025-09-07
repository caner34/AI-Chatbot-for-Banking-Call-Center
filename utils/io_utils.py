
import os
import json


def save_jsons_to_folder(json_obj, file_name: str, output_folder: str):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Define the file name
    file_name = f"{file_name}.json"
    file_path = os.path.join(output_folder, file_name)

    # Write the JSON data to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_obj, f, ensure_ascii=False, indent=4)

    print(f"Saved {file_name} to {output_folder}")

    return


def save_text_to_file(text: str, file_name: str, output_folder: str):
    """
    Saves the given text to a specified file in a given folder.

    :param text: The text content to save.
    :param file_name: The name of the file (with extension, e.g., 'example.txt').
    :param output_folder: The folder where the file should be saved.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Define the full file path
    file_path = os.path.join(output_folder, file_name)

    # Write the text to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)

    return


def to_snake_case(cr_text: str):
    return str(cr_text).replace(' ', '_').lower()


def load_json_from_folder(file_name: str, input_folder: str):
    """
    Loads a JSON file from a specified folder and returns its contents as a Python object.

    :param file_name: The name of the JSON file to load (without path).
    :param input_folder: The folder containing the JSON file.
    :return: The JSON object loaded from the file.
    """
    # Define the file path
    file_path = os.path.join(input_folder, file_name)

    # Ensure the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_name}' does not exist in '{input_folder}'.")

    # Load the JSON data from the file
    with open(file_path, "r", encoding="utf-8") as f:
        json_obj = json.load(f)

    # print(f"Loaded {file_name} from {input_folder}")

    return json_obj

