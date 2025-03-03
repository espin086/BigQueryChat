"""
BigQuery Chatbot Streamlit Application

This module defines a Streamlit-based chatbot application that interacts with
BigQuery tables. It maintains persistent chat history using SQLite and
incorporates ReAct-based agents along with LangSmith for enhanced querying
and schema inspection.

Key Features:
- Streamlit UI for chatbot interactions.
- Integration with BigQuery for querying structured data.
- Persistent chat history using SQLite.
- ReAct-based agents for better contextual understanding.
- LangSmith for query optimization and schema exploration.

Usage:
Run this module with Streamlit to launch the chatbot application.

Example:
    ```bash
    streamlit run streamlit_app.py
    ```
"""

from collections import defaultdict
import streamlit as st
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from src.sql_lite_handler import DatabaseManager
from src.format_message import format_message, format_timestamp_label
from src.agent import process_query

# Define button styles (CSS) for Streamlit buttons
BUTTON_STYLE = """
<style>
    div[data-testid="stButton"] button {
        width: 100%;  /* Make buttons take full width */
        padding: 10px;
        background-color: #545353; /* Default background */
        color: white; /* Default text color */
        border: none;
        border-radius: 5px;
        text-align: center;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #6b6b6b;  /* Darker background on hover */
        color: #4CAF50; /* Green text on hover */
    }
    div[data-testid="stButton"] button:active, 
    div[data-testid="stButton"] button:focus {
        background-color: #4CAF50 !important;  /* Green background on click */
        color: white !important;  /* White text on click */
        outline: none !important;  /* Remove focus outline */
        box-shadow: 0 0 5px #4CAF50;  /* Optional glow effect */
    }
</style>
"""

load_dotenv()

# Initialize session state for memory if not exists
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True
    )

# Initialize the database manager
db_manager = DatabaseManager()
db_manager.create_db_if_not_there()

# Streamlit UI setup
st.set_page_config(page_title="BigQuery Chatbot", layout="wide")
st.title("BigQuery Chatbot")

# Sidebar for past conversations
st.sidebar.header("Conversation History")

# Start new conversation
new_conversation = st.sidebar.text_input("New Conversation Topic")
if st.sidebar.button("Start New Conversation"):
    if new_conversation:
        conversation_id = db_manager.save_conversation(new_conversation)
        st.session_state.conversation_id = conversation_id
        st.session_state.topic = new_conversation
        st.session_state.messages = []  # Reset messages for new conversation
        st.session_state.memory.clear()  # Clear previous memory

# Delete conversation
conversation_to_delete = st.sidebar.selectbox(
    "Select Conversation to Delete",
    [None] + [row[0] for row in db_manager.get_all_topics()],
)
if st.sidebar.button("Delete Selected Conversation"):
    if conversation_to_delete:
        conversation_id_to_delete = db_manager.get_conversation_id_by_topic(
            conversation_to_delete
        )
        db_manager.delete_conversation(conversation_id_to_delete)

# Get all conversations
past_conversations = db_manager.get_all_conversations()

# Group conversations by timestamp label
grouped_conversations = defaultdict(list)
for conversation_id, topic, timestamp in past_conversations:
    label = format_timestamp_label(timestamp)
    grouped_conversations[label].append((conversation_id, topic))

# Inject the CSS into the app
st.sidebar.markdown(BUTTON_STYLE, unsafe_allow_html=True)

# Display grouped conversations in the sidebar
for label, conversations in grouped_conversations.items():
    # Print the label (e.g., "Today", "Yesterday") once
    st.sidebar.write(f"### {label}")

    for conversation_id, topic in conversations:
        # Create an actual Streamlit button
        if st.sidebar.button(topic, key=f"load_{conversation_id}"):
            st.session_state.conversation_id = conversation_id
            st.session_state.topic = topic
            messages = db_manager.get_messages_by_conversation(conversation_id)

            # Reset memory and messages
            st.session_state.messages = []
            st.session_state.memory.clear()

            # Load messages into session state and memory
            for sender, text in messages:
                st.session_state.messages.append((sender, text))
                st.session_state.memory.save_context(
                    {"input": sender}, {"output": text}
                )

    # Add a separator after each group
    st.sidebar.write("---")

# Ensure messages and conversation state exist
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
    st.session_state.topic = None
    st.session_state.messages = []

# Main chat area
if st.session_state.conversation_id:
    st.header(f"Topic: {st.session_state.topic}")

    chat_container = st.container()
    with chat_container:
        for sender, message in st.session_state.messages:
            if sender == "User":
                # Right-aligned user message
                st.markdown(
                    f"""
                    <div style='display: flex; justify-content: flex-end; margin-bottom: 10px;'>
                        <div style='background-color: #292828; padding: 10px; border-radius: 10px; max-width: 70%; text-align: left;'>
                            {message}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                formatted_message, code_snippets, dataframes = format_message(message)

                # Render text messages
                if formatted_message:
                    st.markdown(formatted_message, unsafe_allow_html=True)

                # Render code blocks
                for code, language in code_snippets:
                    st.code(code, language=language)

                # Render DataFrames separately
                for df in dataframes:
                    st.dataframe(df)

    col1, col2 = st.columns([5, 1])

    with col1:
        user_input = st.text_input(
            "Type your message here...", key="input", label_visibility="collapsed"
        )

    with col2:
        send_button = st.button("Send", use_container_width=True)

    if send_button and user_input:
        with st.spinner("Processing..."):
            bot_response = process_query(user_input)

        # Save messages in session state and memory
        st.session_state.messages.append(("User", user_input))
        st.session_state.messages.append(("Bot", bot_response))
        st.session_state.memory.save_context(
            {"input": user_input}, {"output": bot_response}
        )

        # Save to database
        db_manager.save_message(st.session_state.conversation_id, "User", user_input)
        db_manager.save_message(st.session_state.conversation_id, "Bot", bot_response)

        # Replace st.rerun() with experimental_rerun()
        st.experimental_rerun()
else:
    st.header("Start a new conversation or select an existing one from the sidebar.")
