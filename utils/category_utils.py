
import os
from utils.io_utils import load_json_from_folder


def import_category_hierarchy(
        file_name: str = 'category_hierarchy_call_center_for_banking_sector.json',
        input_folder: str = os.path.join('assets', 'structured')
):

    return load_json_from_folder(file_name=file_name, input_folder=input_folder)


