

import os
import random
from openai import OpenAI
from typing import Literal, get_args
import json
import re
from simulator.character_generator import generate_a_new_client_character
from utils.llm_utils import get_oa_client


call_category_options = Literal[
    'Info',
    'Operation',
    'Objection'
]

call_subcategory_options = Literal[
    'learning more about packages, offer with a possibility to upselling and cross-selling',
    'objection to bill',
    'cancellation request or possible churn',
    'paying the bill'
]


sentiment_magnitude_options = Literal[
    'slightly',
    'averagely',
    'extremely'
]

sentiment_type_options = Literal[
    'angry',
    'neutral',
    'happy',
    'sad'
]


def generate_sample_call_center_dialog(
        client_name: str,
        client_surname: str,
        client_id: int,
        client_gender: str,
        call_datetime_str: str,
        is_first_call: bool,
        repetitive_calls: bool,
        call_category: call_category_options,
        call_micro_category: str,
        sentiment_type: sentiment_type_options,
        sentiment_magnitude: sentiment_magnitude_options,
        number_of_words: int = 500,
        company_name: str = "A Bank",
        language: str = "Spanish",
        client: OpenAI | None = None
):
    if client is None:
        client = get_oa_client()

    # models = client.models.list()
    # print(models)

    additional_prompt_repetitive_call = ""
    if (not is_first_call) and repetitive_calls:
        additional_prompt_repetitive_call = ""

    cr_prompt = f"""
    I want you to generate a sample dialog between a call center operator and a client. 
    The company is in banking sector. You will call the agents as 'OPERATOR' and 'CLIENT'.
    
    Company name is {company_name}.
    
    The client's name is {client_name} {client_surname}. Client is {client_gender}. The operator is the opposite gender.
    
    The call starts at {call_datetime_str}.

    The call reason o the client is {call_category}.
    
    The call sub category is {call_micro_category}.
    
    {additional_prompt_repetitive_call}.

    The general sentiment of the client is {sentiment_magnitude} {sentiment_type}.

    I want the dialog to be approximately {number_of_words} words and in {language} language.
    
    The client id is {client_id} but don't need to mention unless necessary.

    Generate the dialog as Json list in order. In the list each Json object will have the following 3 keys: 
    "agent_type", "dialog_text", "dialog_text_in_en".

    agent_type will be either 'OPERATOR' or 'CLIENT'.
    
    dialog_text will be in {language}.
    dialog_text_en will be in English

    """

    completion = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {
                "role": "system",
                "content": "You will generate call center dialogs between a call center operator in "
                           "banking sector and a client."
            },
            {
                "role": "user",
                "content": cr_prompt
            }
        ]
    )

    json_str = re.sub('\s+', ' ', completion.choices[0].message.content.replace("`", ""))[4:].replace("[ ",
                                                                                                      "[").replace("{ ",
                                                                                                                   "{").replace(
        "] ", "]").replace("} ", "}").strip()
    try:
        json_result = json.loads(json_str)
    except json.decoder.JSONDecodeError as jde:
        print(json_str[:20] + " ... " + json_str[-20:])
        # raise jde
        return None
    return json_result


def generate_random_dialogs(randomly_generate: bool = True, number_of_words: int = 500, language: str = "Spanish"):

    character_info = generate_a_new_client_character(randomly_generate=randomly_generate)

    i = 0

    result = generate_sample_call_center_dialog(
        client_name=character_info['client_name'],
        client_surname=character_info['client_surname'],
        client_id=character_info['client_id'],
        client_gender=character_info['client_gender'],
        call_datetime_str=character_info['dialogs'][i]['dialog_start_datetime'],
        is_first_call=character_info['dialogs'][i]['is_first_call'],
        repetitive_calls=character_info['dialogs'][i]['repetitive_calls'],
        call_category=character_info['dialogs'][i]['call_category'],
        call_micro_category=character_info['dialogs'][i]['call_micro_category'],
        sentiment_type=character_info['dialogs'][i]['sentiment_type'],
        sentiment_magnitude=character_info['dialogs'][i]['sentiment_magnitude'],
        number_of_words=number_of_words,
        language=language
    )

    result = {
        'client_name': character_info['client_name'],
        'client_surname': character_info['client_surname'],
        'client_id': character_info['client_id'],
        'client_gender': character_info['client_gender'],
        'call_datetime': character_info['dialogs'][i]['dialog_start_datetime'],
        'dialog_id': character_info['dialogs'][i]['dialog_id'],
        'repetitive_calls': character_info['dialogs'][i]['repetitive_calls'],
        'is_first_call': character_info['dialogs'][i]['is_first_call'],
        'category_id': character_info['dialogs'][i]['cr_category_id'],
        'category': character_info['dialogs'][i]['call_category'],
        'subcategory_id': character_info['dialogs'][i]['cr_subcategory_id'],
        'subcategory': character_info['dialogs'][i]['call_subcategory'],
        'micro_category_id': character_info['dialogs'][i]['cr_micro_category_id'],
        'micro_category': character_info['dialogs'][i]['call_micro_category'],
        'sentiment_type': character_info['dialogs'][i]['sentiment_type'],
        'sentiment_magnitude': character_info['dialogs'][i]['sentiment_magnitude'],
        'dialog': result,
    }

    return result

