
# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from variables import globals
from utils.llm_utils import get_sms_client


def send_sms(to_number: str, to_name: str = ""):
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    client = get_sms_client()

    to_name = to_name if to_name == "" else " " + to_name
    to_number = to_number if to_number.startswith("+") else "+" + to_number

    client_name = globals.dialog_scenario_info['client_name']
    client_surname = globals.dialog_scenario_info['client_surname']
    client_fullname = client_name + ' ' + client_surname
    client_id = globals.dialog_scenario_info['client_id']
    call_datetime = globals.dialog_scenario_info['call_datetime']
    client_gender = globals.dialog_scenario_info['client_gender']
    gender_pronoun = "He" if client_gender == "Male" else "She"
    main_micro_category = globals.call_insights_and_analysis_json['Main Micro-Category'][2]
    sentiment_type = globals.call_insights_and_analysis_json['Sentiment Analysis']['Sentiment Type']
    sentiment_magnitude = globals.call_insights_and_analysis_json['Sentiment Analysis']['Sentiment Magnitude']
    sentiment_magnitude = sentiment_magnitude if str(sentiment_type).lower() != "neutral" else ""

    max_operator_performance_length = 400
    max_recommendations_length = 600

    operator_performance = globals.call_insights_and_analysis_json['Operator Performance']
    operator_performance = operator_performance if len(operator_performance) < max_operator_performance_length \
        else operator_performance[:max_operator_performance_length] + '...'

    recommendations = globals.call_insights_and_analysis_json['Recommendations']
    recommendations = ''.join(recommendations)
    recommendations = recommendations if len(recommendations) < max_recommendations_length \
        else recommendations[:max_recommendations_length] + '...'

    message = client.messages.create(
        body=f"Hello{to_name}, our customer {client_fullname} with the Client ID {client_id} called at {call_datetime} "
             f"for {main_micro_category}. {gender_pronoun} was {sentiment_magnitude} {sentiment_type}. "
             f"{operator_performance} {recommendations}",
        from_="+15878420800",
        to=to_number,
    )

    print(message.body + " ")

    return


# send_sms("905467613035", "Caner")
