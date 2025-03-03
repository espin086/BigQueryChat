"""
This module provides functions for formatting messages, including text, code blocks,
and Markdown-based tables.
It also includes a function to format timestamps into human-friendly labels.

Functions:
- format_message(message): Parses a message containing text, code blocks, and tables
    to generate formatted HTML, extract code snippets, and convert Markdown tables into
    pandas DataFrames.
- format_timestamp_label(timestamp): Converts a given timestamp into a human-friendly
    label such as "Today", "Yesterday", or a date range.

Dependencies:
- re (Regular expressions for parsing text)
- datetime (Handling timestamps)
- pandas (Processing Markdown tables as DataFrames)
"""

import re
from datetime import datetime, timedelta
import pandas as pd


def format_message(message):
    """
    Formats the message to properly display text, code blocks, and DataFrames in Streamlit.
    Detects programming language dynamically from code blocks.
    Ensures code is displayed separately and text is formatted correctly.
    """

    # Find all code blocks including their language (e.g., `python`, `sql`)
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", message, re.DOTALL)

    # Find Markdown table patterns
    df_pattern = r"\|\s*(.*?)\s*\|(?:\n\|[-\s|]+\|)?\n((?:\|.*\|(?:\n|$))*)"
    df_matches = re.findall(df_pattern, message)

    # Split the message into normal text and code sections (without the language)
    parts = re.split(r"```(?:\w+)?\n(.*?)```", message, flags=re.DOTALL)

    formatted_html = ""
    code_snippets = []  # Store `st.code()` outputs separately
    dataframes = []  # Store DataFrame representations

    code_index = 0  # Keep track of which code block we are processing

    for i, part in enumerate(parts):
        part = part.strip()

        if i % 2 == 0:
            # Normal text (not code)
            if part:
                non_table_text = re.sub(df_pattern, "", part, flags=re.DOTALL).strip()
                if non_table_text:
                    formatted_html += f"""
                    <div style='background-color: #545353; padding: 10px; border-radius: 10px; max-width: 70%; 
                    text-align: left; color: white; margin-bottom: 10px;'>
                        {non_table_text}
                    </div>
                    """

            # Check if this text block contains a DataFrame representation
            for header, rows in df_matches:
                # Extract column headers
                headers = [h.strip() for h in header.split("|") if h.strip()]

                # Process row data, ensuring consistent column count
                data = []
                for idx, r in enumerate(rows.strip().split("\n")):
                    row_values = [col.strip() for col in r.split("|") if col.strip()]

                    # **Ignore the first row that contains Markdown table separators**
                    if idx == 0 and all(col.startswith(":") for col in row_values):
                        continue  # Skip formatting row (e.g., `:----|:----|:----|`)

                    # **Ensure row length matches headers**
                    if len(row_values) == len(headers):
                        data.append(row_values)

                # Create DataFrame only if valid data is available
                if data:
                    df = pd.DataFrame(data, columns=headers)
                    dataframes.append(df)

        else:
            # Code block (every odd index in `parts`)
            if code_index < len(code_blocks):
                language, code = code_blocks[code_index]  # Extract language and code

                # Default to plain text if no language is provided
                language = language.lower() if language else "plaintext"

                # Append the code snippet separately (to avoid HTML rendering issues)
                code_snippets.append((code.strip(), language))
                code_index += 1

    # Return both formatted text, code snippets, and DataFrames separately
    return formatted_html, code_snippets, dataframes


def format_timestamp_label(timestamp):
    """
    Format the timestamp into a label:
    - 'Today' if the date is today's date
    - 'Yesterday' if the date is yesterday's date
    - 'Previous 7 days' if the date is within the last 7 days but not today or yesterday
    - 'Previous 30 days' if the date is within the last 30 days but not in the previous 7 days
    - Otherwise, show the full date in 'YYYY-MM-DD' format
    """
    # Parse the timestamp if it is a string
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.strptime(
                timestamp, "%Y-%m-%d %H:%M:%S"
            )  # Update format as per your input
        except ValueError:
            try:
                timestamp = datetime.strptime(
                    timestamp, "%Y-%m-%d"
                )  # Handle date-only format
            except ValueError:
                return "Invalid timestamp"

    # Ensure we are working with a datetime object
    if not isinstance(timestamp, datetime):
        return "Invalid timestamp"

    today = datetime.now().date()
    timestamp_date = timestamp.date()

    if timestamp_date == today:
        return "Today"
    elif timestamp_date == today - timedelta(days=1):
        return "Yesterday"
    elif today - timedelta(days=7) <= timestamp_date < today - timedelta(days=1):
        return "Previous 7 days"
    elif today - timedelta(days=30) <= timestamp_date < today - timedelta(days=7):
        return "Previous 30 days"
    else:
        return timestamp.strftime("%Y-%m-%d")  # Return full date if older
