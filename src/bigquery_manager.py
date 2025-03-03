"""
BigQueryManager Module

This module provides a class to manage interactions with Google BigQuery, allowing execution
of SQL queries and optional storage of results in a specified destination table.
"""

import os
import re
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

load_dotenv()


class BigQueryManager:
    """
    A manager class to interact with Google BigQuery, providing functionality to execute SQL queries
    and optionally save query results to a specified table.

    Attributes:
        project_id (str): The GCP project ID.
        dataset_id (str): The BigQuery dataset ID.
        client (bigquery.Client): An instance of the BigQuery client.

    Methods:
        execute_query(query: str, destination_table: str = None):
            Executes the provided SQL query and returns results
            as a DataFrame if no destination table is specified.
    """

    def __init__(self, project_id, dataset_id):
        """
        Initializes the BigQueryManager with project and dataset IDs.

        Args:
            project_id (str): The GCP project ID.
            dataset_id (str): The BigQuery dataset ID.
        """

        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = dataset_id

    def execute_query(self, query, destination_table=None):
        """
        Run a query. Optionally save the results to a table or return the result as a DataFrame.
        """
        job_config = bigquery.QueryJobConfig()

        # Handle destination table for non-DDL queries
        if destination_table and not query.strip().lower().startswith(
            ("create", "alter")
        ):
            table_ref = f"{self.project_id}.{self.dataset_id}.{destination_table}"
            job_config.destination = table_ref
            job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE

        query = re.sub(r"^```sql(.*)```$", r"\1", query, flags=re.DOTALL)
        query_job = self.client.query(query, job_config=job_config)
        result: RowIterator = query_job.result()  # Wait for the query to complete

        # Return DataFrame if no destination_table is provided
        if not destination_table:
            return result.to_dataframe()

    def get_table_schema(self, table_id):
        """
        Retrieve metadata for a table.
        Returns a DataFrame with columns: Column Name, Field Type, Mode, and Description.
        """
        try:
            # Ensure proper table reference format
            if '.' not in table_id:
                # Single table name provided
                table_ref = f"{self.project_id}.{self.dataset_id}.{table_id}"
            elif table_id.count('.') == 1:
                # dataset.table format provided
                table_ref = f"{self.project_id}.{table_id}"
            else:
                # Already fully qualified
                table_ref = table_id
            
            table = self.client.get_table(table_ref)  # Fetch table metadata

            # Extract schema information
            schema_data = []
            for field in table.schema:
                schema_data.append(
                    {
                        "Column Name": field.name,
                        "Field Type": field.field_type,
                        "Mode": field.mode,
                        "Description": (
                            field.description if field.description else "N/A"
                        ),
                    }
                )

            # Convert to DataFrame
            schema_df = pd.DataFrame(schema_data)

            # Fix: Explicitly check if DataFrame is empty
            if schema_df.empty:
                return None  # Return None if no schema data is found

            return schema_df

        except Exception as e:
            return f"error: {e}"  # Return None if the table doesn't exist


# Usage
if __name__ == "__main__":

    project_id = os.getenv("PROJECT_ID")
    dataset_id = os.getenv("DATASET_ID")

    # Instantiate BigQueryManager with the project and dataset IDs
    bq_manager = BigQueryManager(project_id=project_id, dataset_id=dataset_id)

    # Example: Run a query to create or fetch data
    print(bq_manager.get_table_schema("hd.us_census_data_207"))
