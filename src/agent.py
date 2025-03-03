"""
This module defines the agent for handling queries to BigQuery using a conversational ReAct agent.
It leverages LangChain, Google Generative AI (Gemini), and a session-based memory.
"""

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks.tracers import LangChainTracer
from dotenv import load_dotenv
from .tools import fetch_bigquery_schema, execute_bigquery_query
import asyncio
from contextlib import contextmanager


# Load environment variables
load_dotenv()

# Initialize the LangSmith tracer using your API key from the environment
langsmith_tracer = LangChainTracer()

# Add this helper function
@contextmanager
def get_async_loop():
    """Creates and manages an event loop in the current thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()
        asyncio.set_event_loop(None)

# Modify the llm initialization
with get_async_loop():
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        callbacks=[langsmith_tracer],
    )

conversation = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Define available tools for the agent
tools = [fetch_bigquery_schema, execute_bigquery_query]


# Create the agent with session-based memory
def get_agent():
    """
    Initializes and returns a conversational ReAct agent with session-based memory.

    Returns:
        AgentExecutor: A LangChain agent configured with BigQuery tools and memory.
    """
    return initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=st.session_state.memory,
        callbacks=[langsmith_tracer],
    )


def process_query(user_input: str) -> str:
    """Process a user query using the agent."""
    with get_async_loop():
        agent = get_agent()
        return agent.run(user_input)
