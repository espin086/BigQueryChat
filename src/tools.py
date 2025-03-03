"""
This module provides utility functions as LangChain tools to interact with Google BigQuery.
It includes functions for fetching table schemas and executing SQL queries.

Functions:
- fetch_bigquery_schema(table_id: str): Retrieves the schema of a specified BigQuery table.
- execute_bigquery_query(sql_query: str): Executes a given SQL query on BigQuery
    and returns the results.

Dependencies:
- os (For loading environment variables)
- dotenv (For managing environment configurations)
- langchain.tools (For registering tools)
- bigquery_manager (Custom class to manage BigQuery interactions)
"""

import os
from langchain.tools import tool
from src.bigquery_manager import BigQueryManager
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")

# Initialize BigQueryManager
bq_manager = BigQueryManager(project_id=project_id, dataset_id=dataset_id)


@tool
def fetch_bigquery_schema(table_id: str):
    """Fetches the schema of a specified BigQuery table."""
    schema_info = bq_manager.get_table_schema(table_id)
    
    if schema_info is None:
        return f"Table `{table_id}` not found."

    # Convert schema info to string format if it's not already a DataFrame
    try:
        if isinstance(schema_info, pd.DataFrame):
            return f"Schema for table {table_id}:\n\n{schema_info.to_markdown(index=False)}"
        else:
            # If schema_info is a string or other format, return it directly
            return f"Schema information: {schema_info}"
    except Exception as e:
        return f"Error executing: {str(e)}"


@tool
def execute_bigquery_query(sql_query: str) -> str:
    """Executes an SQL query on BigQuery and returns the result."""
    try:
        result_df = bq_manager.execute_query(sql_query)
        return (
            result_df.to_string(index=False)
            if not result_df.empty
            else "No results found."
        )
    except Exception as e:
        return f"Error executing query: {str(e)}"
