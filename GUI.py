
import os
import base64
import json
import pandas as pd
import ast
import datetime
import random
import streamlit as st
from google.cloud import texttospeech
from simulator.character_generator import gender_options, get_sentiment_type_options, get_sentiment_magnitude_options
from simulator.dialog_generation import generate_random_dialogs

from utils.category_utils import import_category_hierarchy
from utils.doc_read_utils import extract_text
from utils.io_utils import save_jsons_to_folder, to_snake_case
from utils.llm_utils import query_oa, generate_oa_prompt_for_dialog_analysis, get_oa_response, retrieve_relevant_chunks, \
    chunk_text
from utils.take_action_utils import send_sms
from utils.translation_utils import try_translate
from variables import globals
from assets.structured.translation import translation


cr_translation = translation['tr']
cr_translation = translation['en']

show_categories_and_sentiment_in_call_center_simulator_page = False


# Supported voices and languages
# https://cloud.google.com/text-to-speech/docs/voices

voice_options = {
    "English Male": {
        'display_name': "English Male",
        'language_code': "en-GB",
        'voice_code': "en-GB-Wavenet-D",
        'ssml_gender': texttospeech.SsmlVoiceGender.MALE,
    },

    "English Female": {
        'display_name': "English Female",
        'language_code': "en-GB",
        'voice_code': "en-GB-Wavenet-C",
        'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
    },

    "Turkish Male": {
        'display_name': "Turkish Male",
        'language_code': "tr-TR",
        'voice_code': "tr-TR-Wavenet-E",  # E
        'ssml_gender': texttospeech.SsmlVoiceGender.MALE,
    },

    "Turkish Female": {
        'display_name': "Turkish Female",
        'language_code': "tr-TR",
        'voice_code': "tr-TR-Wavenet-D",  # C
        'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
    },

    # "Arabic Male": {
    #     'display_name': "Arabic Male",
    #     'language_code': "ar-XA",
    #     'voice_code': "ar-XA-Wavenet-B",
    #     'ssml_gender': texttospeech.SsmlVoiceGender.MALE,
    # },
    #
    # "Arabic Female": {
    #     'display_name': "Arabic Female",
    #     'language_code': "ar-XA",
    #     'voice_code': "ar-XA-Wavenet-A",
    #     'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
    # },

}


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    'credentials', 'canerbrc34_tts_arabic_tests_cred_boreal-ward-445010-t6-dceafea1be7e.json'
)


def synthesize_text_to_speech(
        text, language_code, ssml_gender, voice_code: str = 'tr-TR-Wavenet-D'
):
    """
    Synthesizes speech from the input text using Google Cloud Text-to-Speech API.
    Args:
        text (str): The input text to be converted into speech.
        language_code (str): Language code for Turkish (e.g., 'tr-TR').
    Returns:
        bytes: The audio content in bytes.
    """
    try:
        # Initialize the Text-to-Speech client
        client = texttospeech.TextToSpeechClient()

        # Set the input text
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Configure the voice (language and gender)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_code,
            ssml_gender=ssml_gender
        )

        # Select audio format
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # Perform text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


def play_audio_directly(audio_bytes):
    """
    Generate an HTML audio player to play audio automatically.
    Args:
        audio_bytes (bytes): Audio content in bytes.
    """
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
                <audio controls autoplay id="audio-player">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                <script>
                    const player = document.getElementById("audio-player");
                    player.load();
                    player.play();
                </script>
            """
    audio_html = f"""
                <script>
                    console.log('ok0');
                    var audio = new Audio("data:audio/mp3;base64,{audio_base64}");
                    console.log('ok1');
                    audio.play().then(() => {{
                        console.log("Successfully played the audio.");
                    }}).catch(error => {{
                        console.log("Auto playback failed:", error);
                    }});
                    console.log('ok2');
                </script>
            """
    # st.markdown(audio_html, unsafe_allow_html=True)

    col1, col2 = st.columns([0.01, 0.99])

    with col1:
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    with col2:
        st.write("")

    return


def vocalize_text(agent_gender, dialog_text, language_code, client=None):

    # st.write("STEP 0", " - agent_gender:", agent_gender, " - language_code:", language_code)  # DELETE LATER

    ssml_gender = texttospeech.SsmlVoiceGender.MALE if agent_gender == "Male" else texttospeech.SsmlVoiceGender.FEMALE
    voice_code = [v['voice_code'] for (k, v) in voice_options.items()
                  if v['language_code'] == language_code and v['ssml_gender'] == ssml_gender][0]

    # st.write("STEP 1")  # DELETE LATER

    try:
        if client is None:
            # Initialize the Text-to-Speech client
            client = texttospeech.TextToSpeechClient()

        # st.write("STEP 2")  # DELETE LATER

        # Set the input text
        synthesis_input = texttospeech.SynthesisInput(text=dialog_text)

        # st.write("STEP 3")  # DELETE LATER

        # Configure the voice (language and gender)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_code,
            ssml_gender=ssml_gender
        )

        # st.write("STEP 4")  # DELETE LATER

        # Select audio format
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # st.write("STEP 5")  # DELETE LATER

        # Perform text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # st.write("STEP 6", " - response: ", len(response.audio_content))  # DELETE LATER

        play_audio_directly(response.audio_content)

        # st.write("STEP 7")  # DELETE LATER

        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        return


    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


def generate_scenario(randomly_generate: bool = True):

    globals.case_number = str(random.randint(100000000, 999999999))

    if randomly_generate or (globals.cr_client_gender is not None and globals.cr_sentiment_type_option is not None and globals.cr_sentiment_magnitude_option is not None and globals.cr_call_category is not None and globals.cr_call_subcategory is not None and globals.cr_call_micro_category is not None):
        globals.call_insights_and_analysis_json = None
        dialog_scenario_info = generate_random_dialogs(randomly_generate=randomly_generate)
        globals.dialog_scenario_info = dialog_scenario_info
    else:
        st.warning(cr_translation["please_fill_or_randomly_generate"])
        st.write("")
        pass
        st.info(f"globals.cr_client_gender: {globals.cr_client_gender}, "
                f"globals.cr_sentiment_type_option: {globals.cr_sentiment_type_option}, "
                f"globals.cr_sentiment_magnitude_option: {globals.cr_sentiment_magnitude_option}, "
                f"globals.cr_call_category: {globals.cr_call_category}, "
                f"globals.cr_call_subcategory: {globals.cr_call_subcategory}, "
                f"globals.cr_call_micro_category: {globals.cr_call_micro_category}")
        st.write("")

    return


def on_menu_selection_change():
    # globals.dialog_scenario_info = None
    st.session_state.qa_pairs = []
    globals.chunks = None
    pass

    return


def page_take_action_for_call():

    st.title(cr_translation['take_action_menu_title'])
    st.sidebar.title("Take Action")

    if globals.take_action_contact_list is not None and len(globals.take_action_contact_list) > 0:
        st.dataframe(globals.take_action_contact_list)
    else:
        st.info("No contact is assigned to be notified yet. Please add a contact on the side bar "
                "at the left hands side first.")

    # Display the form
    with st.sidebar.form("action_form"):
        name = st.text_input("Name")
        sms = st.text_input("SMS")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if globals.take_action_contact_list is None:
                globals.take_action_contact_list = pd.DataFrame(columns=["Name", "SMS", "Email"])

            # Save to DataFrame
            new_entry = {"Name": name, "SMS": sms, "Email": email}
            temp_df = pd.DataFrame([new_entry])
            globals.take_action_contact_list = pd.concat(
                [globals.take_action_contact_list, temp_df],
                ignore_index=True)

            st.success("Information submitted and saved successfully!")
            st.rerun()


def main():

    # Google Cloud Service Account Key JSON File
    # st.set_page_config(page_title="📞 Banking Call Center Simulator Demo - AI Labs")
    st.sidebar.title(cr_translation['side_bar_title'])
    # st.sidebar.subheader("")
    st.sidebar.header(cr_translation['ai_labs'])
    st.sidebar.header(cr_translation['menu'])
    # st.sidebar.header("Setup")

    list_menu_items = {
        "call_center_simulator": cr_translation['banking_call_center_simulator'],
        "call_center_dialog_ai_insights": cr_translation['ai_insights_menu_title'],
        "take_action_for_call": cr_translation['take_action_menu_title'],
        "tts_tester": cr_translation['tts_synthesizer_menu_title'],
        "file_upload": cr_translation['file_upload_menu_title'],
        "about": cr_translation['about_menu_title'],
    }

    menu_selection = st.sidebar.radio("Modules", list(list_menu_items.values()), on_change=on_menu_selection_change)

    if menu_selection == list_menu_items['tts_tester']:
        page_text_to_speech()
    elif menu_selection == list_menu_items['call_center_simulator']:
        page_call_center_simulator()
    elif menu_selection == list_menu_items['call_center_dialog_ai_insights']:
        page_call_center_dialog_ai_insights()
    elif menu_selection == list_menu_items['take_action_for_call']:
        page_take_action_for_call()
    elif menu_selection == list_menu_items['file_upload']:
        page_pdf_upload()
    elif menu_selection == list_menu_items['about']:
        page_about()

    if menu_selection == list_menu_items['call_center_simulator']:

        globals.is_able_to_import_scenario = True

        st.sidebar.subheader(cr_translation['scenario_generation_section'])

        scenario_generation_method = st.sidebar.selectbox(
            label=cr_translation['scenario_generation_method'], options=[cr_translation['randomly_generated'], cr_translation['manual']],
            index=0, placeholder='Choose an option please'
        )

        if scenario_generation_method == cr_translation['manual']:
            list_gender_options = [x.value for x in gender_options]
            list_sentiment_type_options = get_sentiment_type_options()
            list_sentiment_magnitude_options = get_sentiment_magnitude_options()
            category_hierarchy = import_category_hierarchy()
            list_categories = category_hierarchy['categories']
            list_categories_names = [x['name'] for x in list_categories]

            select_box_gender = st.sidebar.selectbox(
                label=cr_translation['clients_gender'], options=list_gender_options, index=None,
                placeholder=cr_translation['choose_an_option_please']
            )
            select_box_sentiment_type = st.sidebar.selectbox(
                label=cr_translation['sentiment_type'], options=list_sentiment_type_options, index=None,
                placeholder=cr_translation['choose_an_option_please']
            )
            select_box_sentiment_magnitude = st.sidebar.selectbox(
                label=cr_translation['sentiment_magnitude'], options=list_sentiment_magnitude_options, index=None,
                placeholder=cr_translation['choose_an_option_please']
            )
            select_box_category = st.sidebar.selectbox(
                label=cr_translation['call_category'], options=list_categories_names, index=None,
                placeholder=cr_translation['choose_an_option_please'], key="call_category", on_change=select_call_category
            )

            if globals.cr_call_category is not None:
                globals.cr_client_gender = select_box_gender
                globals.cr_sentiment_type_option = select_box_sentiment_type
                globals.cr_sentiment_magnitude_option = select_box_sentiment_magnitude

                globals.cr_call_category_id = list_categories_names.index(globals.cr_call_category)
                list_subcategories = list_categories[globals.cr_call_category_id]['subcategories']
                list_subcategories_names = [x['name'] for x in list_subcategories]

                select_box_subcategory = st.sidebar.selectbox(
                    label=cr_translation['call_subcategory'], options=list_subcategories_names, index=None,
                    placeholder=cr_translation['choose_an_option_please'], key="call_subcategory", on_change=select_call_subcategory
                )

                if globals.cr_call_subcategory is not None:
                    globals.cr_call_subcategory_id = list_subcategories_names.index(globals.cr_call_subcategory)
                    list_micro_category_names = list_subcategories[globals.cr_call_subcategory_id]['microcategories']

                    select_box_micro_category = st.sidebar.selectbox(
                        label=cr_translation['call_micro_category'], options=list_micro_category_names, index=None,
                        placeholder=cr_translation['choose_an_option_please'], key="call_micro_category", on_change=select_call_micro_category
                    )

        is_scenario_randomly_generated = False if scenario_generation_method == cr_translation['manual'] else True
        st.sidebar.button(label=cr_translation['generate_scenario'], on_click=generate_scenario, args=(is_scenario_randomly_generated,))

        # IMPORT SCENARIO
        st.sidebar.write("")
        if globals.imported_scenario is None and globals.is_able_to_import_scenario:
            st.sidebar.subheader(cr_translation['import_scenario_from_json'])
            globals.imported_scenario = st.sidebar.file_uploader(
                cr_translation['import_scenario_from_json_explanation'], type=["json"]
            )

        if globals.imported_scenario is not None:

            globals.case_number = str(globals.imported_scenario.name).split('__')[0]
            globals.dialog_scenario_info = json.load(globals.imported_scenario)
            globals.is_able_to_import_scenario = False
            print("STEP 1 globals.imported_scenario: ", (globals.imported_scenario is not None))

            if globals.imported_scenario is not None:
                print("STEP 2 globals.imported_scenario: ", (globals.imported_scenario is not None))
                globals.imported_scenario = None
                print("STEP 3 globals.imported_scenario: ", (globals.imported_scenario is not None))
                # st.rerun()

    return


# Streamlit UI
def page_text_to_speech():
    st.title(cr_translation['tr_gb_tts_generator'])
    st.write(cr_translation['tr_gb_tts_generator_description'])

    # Input area for Turkish text
    text = st.text_area(cr_translation["enter_text"], cr_translation['text_area_default_text'])  # Default: "Merhaba"

    default_index_select_box_voice_options = list(voice_options.keys()).index(
        [k for k, v in voice_options.items() if v['language_code'].startswith('tr-')][0])
    select_box_voice_options = st.selectbox(
        label=cr_translation['choose_a_voice_option'], options=list(voice_options.keys()), index=default_index_select_box_voice_options
    )

    if select_box_voice_options is None:
        select_box_voice_options = [k for k, v in voice_options.items() if v['language_code'].startswith('tr-')][-1]

    selected_language_code = voice_options[select_box_voice_options]['language_code']
    selected_voice_code = voice_options[select_box_voice_options]['voice_code']
    selected_ssml_gender = voice_options[select_box_voice_options]['ssml_gender']

    if st.button(cr_translation['generate_speech']):
        if text.strip():
            output_file = "output.mp3"
            audio_bytes = synthesize_text_to_speech(
                text=text, language_code=selected_language_code, ssml_gender=selected_ssml_gender,
                voice_code=selected_voice_code
            )
            if audio_bytes:
                play_audio_directly(audio_bytes)

            # # Audio player for generated speech
            # st.audio(output_file, format='audio/mp3')
        else:
            st.warning(cr_translation['please_enter_some_text'])


def page_call_center_simulator():

    command_start_expression = '<!--' if not show_categories_and_sentiment_in_call_center_simulator_page else ''
    command_end_expression = '-->' if not show_categories_and_sentiment_in_call_center_simulator_page else ''

    globals.scenario_exported = False

    st.title(cr_translation['banking_call_center_simulator_munu_title'])
    st.write("")
    st.write(cr_translation['banking_call_center_simulator_page_explanation'])
    st.write("")

    # Initialize the Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    if globals.dialog_scenario_info is not None:
        st.button(label=cr_translation['export_scenario_as_json'], on_click=export_scenario_as_json)

        # Display Client Information
        st.subheader(cr_translation['client_information'])


        # st.markdown(f"""
        # <style>
        #     .info-box {{
        #         background-color: #cbf5cb;
        #         border-radius: 10px;
        #         padding: 10px;
        #         box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
        #     }}
        # </style>
        # <div class='info-box'>
        #     <b>{cr_translation['Name']}:</b> {globals.dialog_scenario_info['client_name']} {globals.dialog_scenario_info['client_surname']}<br>
        #     <b>{cr_translation['Client ID']}:</b> {globals.dialog_scenario_info['client_id']}<br>
        #     <b>{cr_translation['Case Number']}:</b> {globals.case_number}<br>
        #     <b>{cr_translation['Gender']}:</b> {cr_translation[globals.dialog_scenario_info['client_gender']]}<br>
        #     <b>{cr_translation['Call Time']}:</b> {globals.dialog_scenario_info['call_datetime']}<br>
        #     {command_start_expression}<b>{cr_translation['Category']}:</b> {cr_translation['categories'][globals.dialog_scenario_info['category']]} -> {cr_translation['categories'][globals.dialog_scenario_info['subcategory']]} -> {cr_translation['categories'][globals.dialog_scenario_info['micro_category']]}<br>{command_end_expression}
        #     {command_start_expression}<b>{cr_translation['Sentiment']}:</b> {cr_translation[globals.dialog_scenario_info['sentiment_type'].lower()].capitalize()} ({cr_translation[globals.dialog_scenario_info['sentiment_magnitude']]})<br>{command_end_expression}
        #     <b>{cr_translation['Repetitive Calls']}:</b> {cr_translation[str(globals.dialog_scenario_info['repetitive_calls'])]}<br>
        #     <b>{cr_translation['First Call']}:</b> {cr_translation[str(globals.dialog_scenario_info['is_first_call'])]}
        # </div>
        # """, unsafe_allow_html=True)

        st.markdown(f""" 
                <style>
                    .info-box {{
                        background-color: #cbf5cb;
                        border-radius: 10px;
                        padding: 10px;
                        box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
                    }}
                </style>
                <div class='info-box'>
                    <b>{cr_translation['Name']}:</b> {globals.dialog_scenario_info['client_name']} {globals.dialog_scenario_info['client_surname']}<br>
                    <b>{cr_translation['Client ID']}:</b> {globals.dialog_scenario_info['client_id']}<br>
                    <b>{cr_translation['Case Number']}:</b> {globals.case_number}<br>
                    <b>{cr_translation['Gender']}:</b> {cr_translation[globals.dialog_scenario_info['client_gender']]}<br>
                    <b>{cr_translation['Call Time']}:</b> {globals.dialog_scenario_info['call_datetime']}<br>
                    {command_start_expression}<b>{cr_translation['Category']}:</b> {try_translate(cr_translation['categories'], globals.dialog_scenario_info['category'])} -> {try_translate(cr_translation['categories'], globals.dialog_scenario_info['subcategory'])} -> {try_translate(cr_translation['categories'], globals.dialog_scenario_info['micro_category'])}<br>{command_end_expression}
                    {command_start_expression}<b>{cr_translation['Sentiment']}:</b> {try_translate(cr_translation, globals.dialog_scenario_info['sentiment_type'].lower()).capitalize()} ({try_translate(cr_translation, globals.dialog_scenario_info['sentiment_magnitude'])})<br>{command_end_expression}
                    <b>{cr_translation['Repetitive Calls']}:</b> {cr_translation[str(globals.dialog_scenario_info['repetitive_calls'])]}<br>
                    <b>{cr_translation['First Call']}:</b> {cr_translation[str(globals.dialog_scenario_info['is_first_call'])]}
                </div>
                """, unsafe_allow_html=True)

        # Display Dialog
        st.write("")
        st.write("")
        st.subheader(cr_translation['dialog'])
        for i, d in enumerate(globals.dialog_scenario_info['dialog']):
            st.write("---")
            col1, col2 = st.columns([0.9, 0.1])

            with col1:
                st.markdown(f"**{d['agent_type']} ({cr_translation['turkish']}):** {d['dialog_text']}")

            with col2:
                cr_agent_gender = globals.dialog_scenario_info['client_gender'] if d['agent_type'] == "CLIENT" else (
                    cr_translation['female'] if globals.dialog_scenario_info['client_gender'] == cr_translation['male']
                    else cr_translation['male'])
                # Green Play Button for Turkish
                st.button(
                    "🇹🇷", key=f"play_tr_{i}", on_click=vocalize_text,
                    args=(cr_agent_gender, d['dialog_text'], "tr-TR", client,)
                )

            col1, col2 = st.columns([0.9, 0.1])

            with col1:
                st.markdown(f"**{d['agent_type']} (English):** {d['dialog_text_in_en']}")

            with col2:
                cr_agent_gender = globals.dialog_scenario_info['client_gender'] if d['agent_type'] == "CLIENT" else (
                    cr_translation['female'] if globals.dialog_scenario_info['client_gender'] == cr_translation['male']
                    else cr_translation['male'])
                # White Play Button for English
                st.button(
                    "🇬🇧", key=f"play_en_{i}", on_click=vocalize_text,
                    args=(cr_agent_gender, d['dialog_text_in_en'], "en-GB", client)
                )
    else:
        st.info(cr_translation['no_call_center_scenario'])
    return


def retrieve_ai_insights():
    dialog = globals.dialog_scenario_info['dialog']
    prompt = generate_oa_prompt_for_dialog_analysis(dialog)

    response = query_oa(prompt)

    # response = response.replace('"', "'")
    # response_json = json.loads(response)

    try:
        response_json = ast.literal_eval(response)
    except Exception as e:
        st.write(f"error response: {response} - ERROR: {e}")
    globals.call_insights_and_analysis_json = response_json

    return


def switch_button_for_show_dialog_scenario_json_on_insights_page():
    globals.show_dialog_scenario_json_on_insights_page = not globals.show_dialog_scenario_json_on_insights_page

    return


def switch_button_for_show_ai_insight_json_on_insights_page():
    globals.show_ai_insight_json_on_insights_page = not globals.show_ai_insight_json_on_insights_page

    return


def page_call_center_dialog_ai_insights():
    st.title(cr_translation['ai_insights_menu_title'])
    st.write("")
    st.write(cr_translation['ai_insights_paragraph'])

    st.write("")

    if globals.dialog_scenario_info is not None:


        if globals.call_insights_and_analysis_json is not None:
            insight_response = globals.call_insights_and_analysis_json

            st.sidebar.write("")
            # st.sidebar.markdown("---")

            st.sidebar.button(label=cr_translation['export_ai_insight_as_json'], on_click=export_ai_insight_as_json)

            st.title(cr_translation['insight_analysis_report'])
            st.write("")
            # Highlight Main Micro-Category
            st.header(f"🏆 {cr_translation['Main Category']}")
            main_category = insight_response["Main Micro-Category"]
            st.markdown(f"""
                <div style="background-color: #d4edda; border-left: 5px solid #28a745; padding: 10px; margin: 10px 0; border-radius: 5px;">
                    <b>{cr_translation["Category"]}:</b> {cr_translation['categories'][main_category[0]]} &nbsp;&nbsp; | &nbsp;&nbsp;
                    <b>{cr_translation["Subcategory"]}:</b> {cr_translation['categories'][main_category[1]]} &nbsp;&nbsp; | &nbsp;&nbsp;
                    <b>{cr_translation["Micro-Category"]}:</b> {cr_translation['categories'][main_category[2]]}
                </div>
            """, unsafe_allow_html=True)

            # Display Micro-Categories
            title_str_other_categories = cr_translation["Other Categories"]
            st.header(f"📌 {title_str_other_categories}")
            st.write(cr_translation["following_categories_identified"])

            for category, subcategory, micro_category in insight_response["Micro-Categories"]:
                st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 10px; margin: 5px; border-radius: 5px;">
                        <b>{cr_translation["Category"]}:</b> {cr_translation['categories'][category]} &nbsp;&nbsp; | &nbsp;&nbsp;
                        <b>{cr_translation["Subcategory"]}:</b> {cr_translation['categories'][subcategory]} &nbsp;&nbsp; | &nbsp;&nbsp;
                        <b>{cr_translation["Micro-Category"]}:</b> {cr_translation['categories'][micro_category]}
                    </div>
                """, unsafe_allow_html=True)

            # Display Personal Data
            title_str_personal_data = cr_translation["Personal Data"]
            st.header(f"🔍 {title_str_personal_data}")
            st.write(cr_translation['following_personal_data_notice'])
            for item in insight_response["Personal Data"]:
                st.markdown(f"- **{item}**")

            # Sentiment Analysis
            title_str_sentiment_analysis = cr_translation["Sentiment Analysis"]
            st.header(f"📈 {title_str_sentiment_analysis}")
            sentiment = insight_response["Sentiment Analysis"]
            st.markdown(f"""
                <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 10px; margin: 10px 0; border-radius: 5px;">
                    <b>{cr_translation['sentiment_type']}:</b> {try_translate(cr_translation, sentiment["Sentiment Type"].lower()).capitalize()}<br>
                    <b>{cr_translation['sentiment_magnitude']}:</b> {try_translate(cr_translation, sentiment["Sentiment Magnitude"].lower()).capitalize()}<br>
                </div>
            """, unsafe_allow_html=True)

            # st.markdown(f"""
            #     <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 10px; margin: 10px 0; border-radius: 5px;">
            #         <b>{cr_translation['sentiment_type']}:</b> {cr_translation[sentiment["Sentiment Type"].lower()].capitalize()}<br>
            #         <b>{cr_translation['sentiment_magnitude']}:</b> {cr_translation[sentiment["Sentiment Magnitude"].lower()].capitalize()}<br>
            #     </div>
            # """, unsafe_allow_html=True)


            # Summary
            title_str_summary = cr_translation["Summary"]
            st.header(f"📌 {title_str_summary}")
            st.info(insight_response["Summary"])

            # Operator Performance
            title_str_operator_performance = cr_translation["Operator Performance"]
            st.header(f"🌟 {title_str_operator_performance}")
            st.info(insight_response["Operator Performance"])

            # Recommendations
            title_str_recommendations = cr_translation["Recommendations"]
            st.header(f"💡 {title_str_recommendations}")
            st.write(cr_translation['recommendations_explanation'])
            for i, recommendation in enumerate(insight_response["Recommendations"], start=1):
                st.markdown(f"""
                    <div style="background-color: #e2e3e5; padding: 10px; margin: 5px; border-radius: 5px;">
                        <b>{i}.</b> {recommendation}
                    </div>
                """, unsafe_allow_html=True)

            # Footer Note
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: grey;'>Generated by AI Insight Analysis Tool © 2025 DataSpecta AI Labs</p>",
                        unsafe_allow_html=True)

            # Send SSM and E-Mail to Take Action
            if globals.take_action_contact_list is not None:
                st.write("TEST len contact list: ", len(globals.take_action_contact_list))
            if globals.take_action_contact_list is not None and len(globals.take_action_contact_list) > 0:
                for index, row in globals.take_action_contact_list.iterrows():

                    st.write("TEST len contact list: ", str(row))
                    to_number = row['SMS']
                    to_name = row['Name'] if row['Name'] is not None else ''
                    st.write(str((to_number is not None and len(to_number) > 0 and globals.dialog_scenario_info is not None and
                            globals.call_insights_and_analysis_json is not None)))
                    if (to_number is not None and len(to_number) > 0 and globals.dialog_scenario_info is not None and
                            globals.call_insights_and_analysis_json is not None):
                        st.write("Sending SMS", index)
                        send_sms(to_number=to_number, to_name=to_name)

        st.write("")
        st.sidebar.button(label=cr_translation["Retrieve AI Insights"], on_click=retrieve_ai_insights)
        st.write("")
        st.write("")
        st.write("")

        show_hide_button_label_for_dialog_display = cr_translation["Show Dialog Scenario"]
        if globals.show_dialog_scenario_json_on_insights_page:
            show_hide_button_label_for_dialog_display = cr_translation["Hide Dialog Scenario"]

        st.sidebar.button(
            label=show_hide_button_label_for_dialog_display,
            on_click=switch_button_for_show_dialog_scenario_json_on_insights_page
        )
        if globals.show_dialog_scenario_json_on_insights_page:
            copy_dialog_scenario_info = globals.dialog_scenario_info.copy()
            if not show_categories_and_sentiment_in_call_center_simulator_page:
                keys_to_be_deleted = [
                    'category_id', 'category', 'subcategory_id', 'subcategory',
                    'micro_category_id', 'micro_category', 'sentiment_type', 'sentiment_magnitude'
                ]
                for key in keys_to_be_deleted:
                    del copy_dialog_scenario_info[key]
            st.write("")
            st.write(copy_dialog_scenario_info)

        if globals.call_insights_and_analysis_json is not None:

            show_hide_button_label_for_ai_insight_display = cr_translation["Show AI Insights"]
            if globals.show_ai_insight_json_on_insights_page:
                show_hide_button_label_for_ai_insight_display = cr_translation["Hide AI Insights"]

            st.sidebar.button(
                label=show_hide_button_label_for_ai_insight_display,
                on_click=switch_button_for_show_ai_insight_json_on_insights_page
            )
            if globals.show_ai_insight_json_on_insights_page:
                st.write("")
                st.write(globals.call_insights_and_analysis_json)
    else:
        st.info(cr_translation['no_call_center_data_warning'])

    return


def export_ai_insight_as_json():

    file_name = to_snake_case(
        globals.case_number + '__' + 'ai_insights' + '__'
        + globals.dialog_scenario_info['micro_category']
        + '__' + globals.dialog_scenario_info['sentiment_magnitude']
        + '__' + globals.dialog_scenario_info['sentiment_type']
        + '__' + datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S.%f")[:-3]
    )

    file_name = file_name.replace(',', '').replace('& ', '').replace('/ ', '').replace('&', '').replace('/', '').replace('(', '').replace(')', '')

    save_jsons_to_folder(
        json_obj=globals.call_insights_and_analysis_json,
        file_name=file_name,
        output_folder=os.path.join('output', 'ai_insights')
    )

    return


def export_scenario_as_json():
    globals.scenario_exported = False
    file_name = to_snake_case(
        globals.case_number + '__' + 'scenario' + '__'
        + globals.dialog_scenario_info['micro_category']
        + '__' + globals.dialog_scenario_info['sentiment_magnitude']
        + '__' + globals.dialog_scenario_info['sentiment_type']
        + '__' + datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S.%f")[:-3]
    )

    file_name = file_name.replace(',', '').replace('& ', '').replace('/ ', '').replace('&', '').replace('/', '').replace('(', '').replace(')', '')

    save_jsons_to_folder(
        json_obj=globals.dialog_scenario_info,
        file_name=file_name,
        output_folder=os.path.join('output', 'scenarios')
    )

    globals.scenario_exported = True

    return


def select_call_category():
    globals.cr_call_category = st.session_state.call_category
    globals.cr_call_subcategory = None
    globals.cr_call_micro_category = None

    return


def select_call_subcategory():
    globals.cr_call_subcategory = st.session_state.call_subcategory
    globals.cr_call_micro_category = None

    return


def select_call_micro_category():
    globals.cr_call_micro_category = st.session_state.call_micro_category

    return


def toggle_chatbot_view():
    globals.classic_chatbot_view = not globals.classic_chatbot_view

    return


def page_pdf_upload():
    st.title("📄 Document Q&A Chatbot")
    globals.show_file_uploader_on_sidebar = True

    # Initialize session state for questions and answers
    if "qa_pairs" not in st.session_state:
        st.session_state.qa_pairs = []

    # globals.uploaded_file = False

    if globals.show_file_uploader_on_sidebar:
        # uploaded_file = st.sidebar.file_uploader("Upload PDF Document to Ask Related Questions About", type=["pdf", "doc", "docx", "json"])
        # Sidebar for file upload
        st.sidebar.header("Upload Document")
        globals.uploaded_file = st.sidebar.file_uploader(
            "Upload PDF Document to Ask Related Questions About", type=["pdf", "doc", "docx", "json"]
        )

    # Main content area
    if globals.uploaded_file:
        st.sidebar.success(f"File Uploaded: {globals.uploaded_file.name}")
        document_text = extract_text(globals.uploaded_file)
        if document_text:

            st.sidebar.success("Document text successfully loaded!")
            # st.session_state.qa_pairs = []

            # Split document into chunks
            chunks = globals.chunks
            if chunks is None:
                chunks = chunk_text(document_text)

            # Display document details
            st.write("### Ask Questions to Your Document")
            st.write("Type your questions below about the uploaded document.")

            st.write("")
            st.toggle("Classic Chatbot View", value=globals.classic_chatbot_view, on_change=toggle_chatbot_view)
            st.write("")

            user_question = st.chat_input("Please ask your question about the document")

            if user_question:

                with st.spinner("Retrieving answers... Please wait..."):
                    # Retrieve relevant chunks
                    relevant_chunks = retrieve_relevant_chunks(chunks, user_question)

                    # Get response from OpenAI
                    answer = get_oa_response(relevant_chunks, user_question)

                # st.write("answer: ", answer)

                # Append Q&A to session state
                st.session_state.qa_pairs.append({"question": user_question, "answer": answer})
                # st.experimental_rerun()

            # Display all questions and answers with icons
            st.write("### Q&A History")
            for qa in st.session_state.qa_pairs:
                if not globals.classic_chatbot_view:
                    st.markdown(f"<p style='font-size:18px;'>❓ <b>{qa['question']}</b></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size:18px; color:green;'>✅ {qa['answer']}</p>", unsafe_allow_html=True)
                else:
                    with st.chat_message(name="ai", avatar="assistant"):
                        st.write(qa['question'])
                    with st.chat_message(name="user", avatar="user"):
                        st.write(qa['answer'])
    else:
        st.info("Please upload a document to begin.")

    return


def page_about():
    pass


if __name__ == "__main__":
    main()

