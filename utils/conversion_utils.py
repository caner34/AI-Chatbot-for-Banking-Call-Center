
import os
from typing import Literal
from utils.io_utils import load_json_from_folder, save_text_to_file, save_text_as_pdf


def convert_list_to_literal(cr_list: list) -> Literal:

    return Literal[*cr_list]


def convert_json_obj_to_txt(file_name: str | int = 0, input_folder: str = os.path.join("output", "samples")):

    if type(file_name) == int:
        file_name = f"sample_{file_name}.json"

    json_obj = load_json_from_folder(file_name=file_name, input_folder=input_folder)

    cr_call_category = json_obj['call_category']
    cr_sentiment_type = json_obj['sentiment_type']
    cr_sentiment_magnitude = json_obj['sentiment_magnitude']

    cr_dialog = json_obj['dialog']
    
    new_dialog = ''
    for cr_dict in cr_dialog:
        for k, v in cr_dict.items() :
            new_dialog += v + ': ' if k == 'agent_type' else v + ' '
            new_dialog = new_dialog.replace('CLIENT', 'MÜŞTERİ')

    file_name_root = file_name.replace(".json", '')
    new_file_name = f"sample_{file_name_root}__{cr_call_category}__{cr_sentiment_type}__{cr_sentiment_magnitude}.txt"

    save_text_to_file(
        text=new_dialog,
        file_name=new_file_name,
        output_folder=os.path.join("output", "samples_txt")
    )

    return


def convert_json_obj_to_pdf(file_name: str | int = 0, input_folder: str = os.path.join("output", "samples")):

    if type(file_name) == int:
        file_name = f"sample_{file_name}.json"

    json_obj = load_json_from_folder(file_name=file_name, input_folder=input_folder)

    cr_call_category = json_obj['call_category']
    cr_sentiment_type = json_obj['sentiment_type']
    cr_sentiment_magnitude = json_obj['sentiment_magnitude']

    cr_dialog = json_obj['dialog']

    new_dialog = ''
    for cr_dict in cr_dialog:
        for k, v in cr_dict.items() :
            new_dialog += v + ': ' if k == 'agent_type' else v + ' '
            new_dialog = new_dialog.replace('CLIENT', 'MÜŞTERİ')

    file_name_root = file_name.replace(".json", '')
    new_file_name = f"{file_name_root}__{cr_call_category}__{cr_sentiment_type}__{cr_sentiment_magnitude}.txt"

    output_folder = os.path.join('output', 'samples_pdf')
    file_path = os.path.join(output_folder, file_name)
    save_text_as_pdf(
        text=new_dialog,
        output_pdf_file=file_path
    )

    return


#
# for file_name in os.listdir(os.path.join('output', 'samples')):
#     print(file_name)
#     convert_json_obj_to_txt(file_name=file_name)
#
#
# for file_name in os.listdir(os.path.join('output', 'samples')):
#     print(file_name)
#     convert_json_obj_to_pdf(file_name=file_name)
#
