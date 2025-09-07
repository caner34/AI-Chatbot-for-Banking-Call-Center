import numpy as np
from openai import OpenAI
from twilio.rest import Client
import json
import re
import openai
import streamlit as st
from utils.category_utils import import_category_hierarchy
from variables import globals
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


def embed_text(text_list):
	# """Get OpenAI embeddings for a list of texts."""
	# response = openai.Embedding.create(
	#     input=text_list,
	#     model="text-embedding-ada-002"
	# )
	# return [data['embedding'] for data in response['data']]

	embedder = SentenceTransformer('all-MiniLM-L6-v2')

	return embedder.encode(text_list, convert_to_tensor=True)


# --- RAG (Chunking + Embeddings + Retrieval) ---
def chunk_text(text, chunk_size=500):
	"""Split text into smaller chunks of a given size."""
	words = text.split()
	return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def retrieve_relevant_chunks(chunks, user_question, top_k=2):
	"""Retrieve the most relevant text chunks based on cosine similarity."""
	# Embed the chunks and user question
	embeddings = embed_text(chunks + [user_question])
	chunk_embeddings = embeddings[:-1]
	question_embedding = embeddings[-1]

	# Compute cosine similarity
	similarities = cosine_similarity([question_embedding], chunk_embeddings)[0]
	top_indices = np.argsort(similarities)[-top_k:][::-1]

	# Return the top relevant chunks
	return [chunks[i] for i in top_indices]


def get_oa_client():
	OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
	client = OpenAI(api_key=OPENAI_API_KEY)
	return client


def get_sms_client():
	client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
	return client


def get_oa_response(document_text, user_question,
					system_content="You are a useful assistant, try to answer questions from the document text."):
	"""Query the OpenAI GPT API for answers based on the document text."""
	client = globals.client
	if client is None:
		client = get_oa_client()

	try:
		prompt = f"Document Text:\n{document_text}\n\nQuestion: {user_question}\nAnswer:"
		response = client.chat.completions.create(
			model="gpt-4",
			messages=[
				{"role": "system", "content": system_content},
				{"role": "user", "content": prompt}
			],
			max_tokens=200,
			temperature=0.5
		)
		return response.choices[0].message.content.strip()
	except Exception as e:
		# st.write("Error:", len(document_text), e)
		return "Unable to generate an answer. Please try again."


def generate_oa_prompt_for_dialog_analysis(dialog, language: str = "Turkish"):
	"""Generate a structured prompt for OpenAI based on the dialog."""

	category_hierarchy = import_category_hierarchy()

	dialog_text = ""
	for entry in dialog:
		agent_type = entry["agent_type"]
		# text = entry["dialog_text_in_en"]
		text = entry["dialog_text"]
		dialog_text += f"{agent_type}: {text}\n"

	prompt = f"""
    You are analyzing a customer service call. Below is the conversation between a customer and an operator:

    {dialog_text}

    Please provide the following information in JSON format:
    1. the main micro-category and a list of micro-categories related to this conversation as tuples in this form 
        (category, subcategory, micro-category) (choose values from this hierarchy: {category_hierarchy}).
    2. Personal data mentioned in the dialog (e.g., names, IDs, birthdate, e-mails etc.). Note that transactional values are not personal.
    3. The sentiment type of Clients sentiments (angry, neutral, happy, sad).
    4. The sentiment magnitude of clients sentiments (slightly, averagely, extremely).
    5. A summarization of the dialog.
    6. A brief evaluation of the operator's performance.
    7. if you see an error or a shortcoming of the operator, give Recommendations 
       for improving customer service and benefiting the company by avoiding churn or leading to upselling, 
       specifically based on the call experience.

    Ensure your output is valid JSON. Use single quotes (') for dictionary, do not use double quotes (") in json string.

    the fields are:
    "Micro-Categories" (list of tuples)
    "Main Micro-Category" (tuple)
    "Personal Data" (list of strings)
    "Sentiment Analysis" (object with "Sentiment Type" and "Sentiment Magnitude" keys)
    "Summary" (string)
    "Operator Performance" (string)
    "Recommendations" (list of strings)

    in json value strings must be in {language} except for Sentiment Analysis, Micro-Categories and Main Micro-Category.

    """

	return prompt


def query_oa(prompt, system_content="You are a call center customer experience analyst for a Banking company."):
	"""Query the OpenAI GPT API with the generated prompt."""
	client = globals.client
	if client is None:
		client = get_oa_client()

	try:

		response = client.chat.completions.create(
			model="gpt-4",  # Update model as "gpt-3.5-turbo" or any supported model
			messages=[
				{"role": "system", "content": system_content},
				{"role": "user", "content": prompt}
			],
			max_tokens=2000,
			temperature=0.7
		)

		return response.choices[0].message.content.strip()

	except Exception as e:
		print(f"EXCEPTION on query_oa - Error: {e}")
		return None
