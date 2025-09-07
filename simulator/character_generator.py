import random
from utils.category_utils import import_category_hierarchy
from utils.character_utils import Gender, get_firstname_list, get_lastname_list
from utils.time_utils import generate_random_datetime, convert_datetime_to_str
from datetime import timedelta
from typing import Literal, get_args
from variables import globals

sentiment_magnitude_options = Literal['slightly', 'averagely', 'extremely'
]

sentiment_type_options = Literal[
    'neutral',
    'angry',
    'happy',
    'sad'
]

gender_options = [
    Gender.MALE, Gender.FEMALE
]


def get_sentiment_type_options():
    return get_args(sentiment_type_options)


def get_sentiment_magnitude_options():
    return get_args(sentiment_magnitude_options)


def generate_a_new_client_character(
        randomly_generate: bool = True,
        can_have_repetitive_calls: bool = False
):
    client_id = random.randint(10000000, 99999999)
    gender = globals.cr_client_gender
    if randomly_generate or globals.cr_client_gender is None:
        gender = random.choice(gender_options)
    else:
        gender = Gender.MALE if globals.cr_client_gender == 'Male' else Gender.FEMALE
    gender_str = gender.value
    list_firstname = get_firstname_list(gender=gender)[:400]
    list_lastname = get_lastname_list()[:400]
    name = str(list_firstname[random.randint(0, len(list_firstname) - 1)]).capitalize()
    surname = str(list_lastname[random.randint(0, len(list_lastname) - 1)]).upper()
    # if gender == Gender.FEMALE and random.randint(0, 1) == 1:
    #     surname += ' ' + str(list_lastname[random.randint(0, len(list_lastname) - 1)]).upper()
    full_name = name + ' ' + surname

    number_of_calls = 1
    list_calling_datetime = [generate_random_datetime()]

    if can_have_repetitive_calls:
        repetitive_calls = bool(random.randint(0, 1))

        if repetitive_calls:
            number_of_calls = random.randint(2, 3)
            for call_id in range(number_of_calls):
                if call_id == 0:
                    pass
                previous_call_datetime = list_calling_datetime[-1]
                time_gap_between_calls_in_milliseconds = random.randint(0, 7 * 24 * 60 * 60 * 1000)
                new_call_datetime = previous_call_datetime - timedelta(
                    milliseconds=time_gap_between_calls_in_milliseconds)
                list_calling_datetime.append(new_call_datetime)

    else:
        repetitive_calls = False

    character_info = {
        'client_gender': gender_str,
        'client_name': name,
        'client_surname': surname,
        'client_full_name': full_name,
        'client_id': client_id,
        'dialogs': [],
    }

    category_hierarchy = import_category_hierarchy()

    for i, cr_datetime in enumerate(list_calling_datetime):

        if randomly_generate:
            list_categories = category_hierarchy['categories']
            cr_category_id = random.randint(0, len(list_categories) - 1)
            cr_category = list_categories[cr_category_id]
            cr_category_str = cr_category['name']

            list_subcategories = cr_category['subcategories']
            cr_subcategory_id = random.randint(0, len(list_subcategories) - 1)
            cr_subcategory = list_subcategories[cr_subcategory_id]
            cr_subcategory_str = cr_subcategory['name']

            list_micro_categories = cr_subcategory['microcategories']
            cr_micro_category_id = random.randint(0, len(list_micro_categories) - 1)
            cr_micro_category_str = list_micro_categories[cr_micro_category_id]

            cr_sentiment_type_options = get_args(sentiment_type_options)
            cr_sentiment_magnitude_options = get_args(sentiment_magnitude_options)

            cr_sentiment_type_option = random.choice(cr_sentiment_type_options)
            cr_sentiment_magnitude_option = random.choice(cr_sentiment_magnitude_options)

            globals.cr_call_category_id = cr_category_id
            globals.cr_call_category = cr_category_str
            globals.cr_call_subcategory_id = cr_subcategory_id
            globals.cr_call_subcategory = cr_subcategory_str
            globals.cr_call_micro_category_id = cr_micro_category_id
            globals.cr_call_micro_category = cr_micro_category_str
            globals.cr_sentiment_type_option = cr_sentiment_type_option
            globals.cr_sentiment_magnitude_option = cr_sentiment_magnitude_option

        character_info['dialogs'].append({
            'dialog_id': i,
            'dialog_start_datetime': convert_datetime_to_str(cr_datetime),
            'repetitive_calls': repetitive_calls,
            'is_first_call': i == 0,
            'cr_category_id': globals.cr_call_category_id,
            'call_category': globals.cr_call_category,
            'cr_subcategory_id': globals.cr_call_subcategory_id,
            'call_subcategory': globals.cr_call_subcategory,
            'cr_micro_category_id': globals.cr_call_micro_category_id,
            'call_micro_category': globals.cr_call_micro_category,
            'sentiment_type': globals.cr_sentiment_type_option,
            'sentiment_magnitude': globals.cr_sentiment_magnitude_option,
        })

    return character_info
