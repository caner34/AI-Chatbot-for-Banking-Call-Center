
import streamlit as st
from PyPDF2 import PdfReader
import docx
import json
from io import StringIO


def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF file."""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(uploaded_file):
    """Extract text from DOCX file."""
    doc = docx.Document(uploaded_file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


def extract_text_from_json(uploaded_file):
    """Extract text from JSON file."""
    content = json.load(uploaded_file)
    return json.dumps(content, indent=4)


def extract_text(uploaded_file):
    """Determine file type and extract text accordingly."""
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx") or uploaded_file.name.endswith(".doc"):
        return extract_text_from_docx(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        return extract_text_from_json(uploaded_file)
    else:
        st.error("Unsupported file format.")
        return ""

