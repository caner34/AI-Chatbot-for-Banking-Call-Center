import os
import random
from enum import Enum
from utils.io_utils import load_json_from_folder
import pandas as pd


class Gender(Enum):

    FEMALE = "Female"
    MALE = "Male"
    OTHER = "Other"


def get_firstname_list(
        gender: Gender,
        input_folder: str = os.path.join('assets', 'structured', 'names')
):
    if gender == Gender.OTHER:
        gender = random.choice([Gender.FEMALE, Gender.MALE])

    first_name_file_names_by_gender = {
        Gender.MALE: 'male_name_us.csv',
        Gender.FEMALE: 'female_name_us.csv',
    }
    # first_name_file_names_by_gender = {
    #     Gender.MALE: 'male_name_local.txt',
    #     Gender.FEMALE: 'female_name_local.txt',
    # }

    file_name = first_name_file_names_by_gender[gender]

    return pd.read_csv(os.path.join(input_folder, file_name), sep=';', header=None, names=['name', 'name_en', 'number'])['name'].tolist()


def get_lastname_list(
        file_name: str = 'lastnames_us.csv',  # 'surnames_local.csv',
        input_folder: str = os.path.join('assets', 'structured', 'names')
):

    return pd.read_csv(os.path.join(input_folder, file_name), sep=';', header=None, names=['name', 'name_en', 'number'])['name'].tolist()

