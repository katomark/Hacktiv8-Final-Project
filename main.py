import os
import sqlite3

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as gen_ai
from google.api_core import retry


# Prepare database
db_file = "paket_pulsa_ioh.db"


# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="IOH Virtual Sales Assistant!",
    page_icon=":brain:",  # Favicon emoji
    layout="centered",  # Page layout option
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set up Tools
def list_tables() -> list[str]:
    db_conn = sqlite3.connect(db_file)
    cursor = db_conn.cursor()

    # Fetch the table names.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = cursor.fetchall()
    return [t[0] for t in tables]

def describe_table(table_name: str) -> list[tuple[str, str]]:
    db_conn = sqlite3.connect(db_file)
    cursor = db_conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")

    schema = cursor.fetchall()
    # [column index, column name, column type, ...]
    return [(col[1], col[2]) for col in schema]

def execute_query(sql: str) -> list[list[str]]:
    print(' - DB CALL: execute_query, ' + sql)
    db_conn = sqlite3.connect(db_file)
    cursor = db_conn.cursor()

    cursor.execute(sql)
    return cursor.fetchall()
    
db_tools = [list_tables, describe_table, execute_query]

instruction = """You are a helpful sales representative that can interact with an SQL database for IOH cellular company in Indonesia. Your name is Robyn, a young woman.
You will take the users questions and turn them into SQL queries using the tools
available. Once you have the information you need, you will answer the user's question using
the data returned. Use list_tables to see what tables are present, describe_table to understand
the schema, and execute_query to issue an SQL SELECT query.
The sales target is highest revenue, so make sure you offer the most expensive items, but if user can't afford it you can lower the offering based on user preferences.
The question to user must polite as Gen Z and don't push hard the user. If the user question is not refer to company product, you can ask what item is user need right now in Indonesia Language. If first user question is about product, answer it directly. User may name Internet as Data, make sure you understand this. All information are in table paket_ioh. column nama_paket is package name, harga is price in Rupiah, voice is in minute, sms is maximum sms, data is package for access internet in GB, masa_berlaku is expired of the package in day. if column value is 0 mean it is not available example data = 0 mean this package is not for Internet.
"""


# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel(
    "models/gemini-1.5-flash-latest", tools=db_tools, system_instruction=instruction
)

# Define a retry policy. The model might make multiple consecutive calls automatically
# for a complex query, this ensures the client retries if it hits quota limits.
retry_policy = {"retry": retry.Retry(predicate=retry.if_transient_error)}

# Start a chat with automatic function calling enabled.
# chat = model.start_chat(enable_automatic_function_calling=True)

# Function to translate roles between Gemini and Streamlit terminology
def translate_role_for_streamlit(user_role):
    if user_role == "model":
        return "assistant"
    else:
        return user_role


# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True, history=[])


# Display the chatbot's title on the page
st.title("🤖 IOH Virtual Sales Assistant!")

# Display the chat history
for message in st.session_state.chat_session.history:
    with st.chat_message(translate_role_for_streamlit(message.role)):
        st.markdown(message.parts[0].text)
       
        
# Input field for user's message
user_prompt = st.chat_input("Tanya apa ... ")
if user_prompt:
    # Add user's message to chat and display it
    st.chat_message("user").markdown(user_prompt)

    # Send user's message to Gemini and get the response
    gemini_response = st.session_state.chat_session.send_message(user_prompt, request_options=retry_policy)
        
    # Display Gemini's response
    with st.chat_message("assistant"):
        st.markdown(gemini_response.text)