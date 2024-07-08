import numpy as np
import pandas as pd
from pydantic import BaseModel, ValidationError, Field, model_validator
from typing import List, Optional, Any, Hashable
import timeit
import os
import json


class FileImporter:
    """
    Decorator for importing data from Excel, CSV, or JSON files into Pydantic models.

    Args:
        file_path (str, optional): Default file path for importing. Can be overridden
            when calling decorated class methods.

    Usage:
        @FileImporter(file_path="path_to_file")
        class MyDataImporter:
            field1: int
            field2: str

            def __init__(self, filepath: Optional[str] = None):
                self.filepath = filepath

    Raises:
        ValueError: If the provided file path is empty or the file format is unsupported,
                    or if there are errors during file reading or data validation.

    Returns:
        tuple: A tuple containing two elements:
            - A list of validated Pydantic model instances.
            - A list of dictionaries describing validation errors, each dictionary containing:
                - 'row_num': Row number where the error occurred.
                - 'column_name': Name of the column where the error occurred.
                - 'error_message': Description of the validation error.

    """

    def __init__(self, file_path=None):
        self.file_path = file_path

    def __call__(self, cls):
        """
        Decorator function that wraps around a class and adds file import functionality.

        Args:
            cls (type): The class to be decorated, containing Pydantic model fields.

        Returns:
            function: Wrapper function that performs file import, validation, and error handling.
        """
        def wrapper(*args, **kwargs):
            """
            Wrapper function that performs file import, validation, and error handling.

            Args:
                *args: Positional arguments passed to the decorated class constructor.
                **kwargs: Keyword arguments passed to the decorated class constructor,
                          including 'filepath' to override default file path.

            Raises:
                ValueError: If file path is empty, unsupported file format, or errors during
                            file reading or data validation.

            Returns:
                tuple: A tuple containing two elements:
                    - A list of validated Pydantic model instances.
                    - A list of dictionaries describing validation errors.
            """
            # Extract and store filepath from kwargs or use the default filepath
            filepath = kwargs.get('filepath', self.file_path)

            if not filepath:
                raise ValueError("Filepath is required for import_file")

            # Dynamically create a Pydantic model based on the annotations
            class DynamicModel(BaseModel, cls):
                pass

            for field, field_type in cls.__annotations__.items():
                DynamicModel.__annotations__[field] = field_type

            class FileRecords(DynamicModel):
                @classmethod
                def import_file(cls) -> tuple[list[Any], list[dict[str, Hashable | Any]]]:
                    """
                    Imports data from the specified file and validates against the Pydantic model.

                    Returns:
                        tuple: A tuple containing two elements:
                            - A list of validated Pydantic model instances.
                            - A list of dictionaries describing validation errors.
                    """
                    return cls._process_file_flow(filepath)

                @classmethod
                def _process_file_flow(cls, file_path: str) -> tuple[list[Any], list[dict[str, Hashable | Any]]]:
                    """
                    Processes the specified file, performs validation, and returns results.

                    Args:
                        file_path (str): Path to the file to be processed.

                    Raises:
                        ValueError: If unsupported file format or errors during file reading or validation.

                    Returns:
                        tuple: A tuple containing two elements:
                            - A list of validated Pydantic model instances.
                            - A list of dictionaries describing validation errors.
                    """
                    # Determine file type
                    file_extension = os.path.splitext(filepath)[1].lower()

                    if file_extension in ['.xlsx', '.xls']:
                        df = cls._read_excel_file(file_path)
                    elif file_extension == '.csv':
                        df = cls._read_csv_file(file_path)
                    elif file_extension == '.json':
                        df = cls._read_json_file(file_path)
                    else:
                        raise ValueError(f"Unsupported file format {file_extension}. Please upload an Excel, CSV, or JSON file.")

                    df = df.replace(np.nan, None)
                    df = cls._validate_headers(df, list(DynamicModel.__annotations__.keys()))
                    return cls._validate_inputs(df)

                @staticmethod
                def _read_excel_file(file_path: str) -> pd.DataFrame:
                    """
                    Reads an Excel file and returns its contents as a pandas DataFrame.

                    Args:
                        file_path (str): Path to the Excel file.

                    Raises:
                        ValueError: If there is an error reading the Excel file.

                    Returns:
                        pd.DataFrame: Contents of the Excel file as a pandas DataFrame.
                    """
                    try:
                        return pd.read_excel(file_path)
                    except Exception as e:
                        raise ValueError(f"Error reading Excel file: {e}")

                @staticmethod
                def _read_csv_file(file_path: str) -> pd.DataFrame:
                    """
                    Reads a CSV file and returns its contents as a pandas DataFrame.

                    Args:
                        file_path (str): Path to the CSV file.

                    Raises:
                        ValueError: If there is an error reading the CSV file.

                    Returns:
                        pd.DataFrame: Contents of the CSV file as a pandas DataFrame.
                    """
                    try:
                        return pd.read_csv(file_path)
                    except Exception as e:
                        raise ValueError(f"Error reading CSV file: {e}")

                @staticmethod
                def _read_json_file(file_path: str) -> pd.DataFrame:
                    """
                    Reads a JSON file and returns its contents as a pandas DataFrame.

                    Args:
                        file_path (str): Path to the JSON file.

                    Raises:
                        ValueError: If there is an error reading the JSON file.

                    Returns:
                        pd.DataFrame: Contents of the JSON file as a pandas DataFrame.
                    """
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            return pd.DataFrame(data)
                    except Exception as e:
                        raise ValueError(f"Error reading JSON file: {e}")

                @classmethod
                def _validate_headers(cls, df: pd.DataFrame, expected_columns: List[str]) -> pd.DataFrame:
                    """
                    Validates the headers of the DataFrame against expected columns.

                    Args:
                        df (pd.DataFrame): DataFrame to validate.
                        expected_columns (List[str]): List of expected column names.

                    Raises:
                        ValueError: If there are missing or extra headers in the DataFrame.

                    Returns:
                        pd.DataFrame: DataFrame with validated headers.
                    """
                    actual_columns = set(df.columns)
                    if not set(expected_columns).issubset(actual_columns):
                        raise ValueError(
                            f"Invalid headers in the file. Expected columns: {expected_columns}, Found columns: {actual_columns}")
                    return df[expected_columns]

                @classmethod
                def _validate_inputs(cls, df: pd.DataFrame) -> tuple[list[cls], list[dict[str, Hashable | Any]]]:
                    """
                    Validates the data in the DataFrame against the Pydantic model.

                    Args:
                        df (pd.DataFrame): DataFrame containing data to validate.

                    Returns:
                        tuple: A tuple containing two elements:
                            - A list of validated Pydantic model instances.
                            - A list of dictionaries describing validation errors, each dictionary containing:
                                - 'row_num': Row number where the error occurred.
                                - 'column_name': Name of the column where the error occurred.
                                - 'error_message': Description of the validation error.
                    """
                    valid_data = []
                    errors = []

                    for index, row in df.iterrows():
                        try:
                            # Convert each row to a dictionary and create a BaseModel instance
                            file_row = FileRecords(**row.to_dict())
                            valid_data.append(file_row)
                        except ValidationError as e:
                            # Append error details to errors list
                            for err in e.errors():
                                errors.append({
                                    'row_num': index,
                                    'column_name': err['loc'][0],
                                    'error_message': err['msg']
                                })

                    return valid_data, errors

            # Replace import_file method in the original class with FileRecords import_file method
            cls.import_file = FileRecords.import_file

            # Initialize the decorated class and return the validated data directly
            instance = cls(*args, **kwargs)
            return instance.import_file()

        return wrapper


# Example usage:
@FileImporter(file_path="..\\data_csv.csv")
class DataFileImport:
    """
    Example Pydantic model for importing data from an Excel file.

    Fields:
        to_test (int): An integer field.
        name (str): A string field.
        pre_update_url (Optional[str]): An optional string field.
        development_url (Optional[str]): An optional string field.
        post_update_url (Optional[str]): An optional string field.
        registration (Optional[str]): An optional string field.
        login (Optional[str]): An optional string field.
        password (Optional[str]): An optional string field.
        video_page (Optional[str]): An optional string field.
        new_test (int): An integer field.

    Methods:
        check_at_least_one_url(cls, values):
            Validates that at least one of 'pre_update_url', 'development_url', or 'post_update_url' is provided.

            Args:
                cls (type): The class type.
                values (dict): Dictionary containing field values.

            Returns:
                dict: The validated field values.
    """

    to_test: int = Field(ge=0, le=1)
    name: str
    pre_update_url: Optional[str] = None
    development_url: Optional[str] = None
    post_update_url: Optional[str] = None
    registration: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    video_page: Optional[str] = None
    new_test: int = Field(ge=0, le=1)

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_url(cls, values):
        """
        Validates that at least one of 'pre_update_url', 'development_url', or 'post_update_url' is provided.

        Args:
            cls (type): The class type.
            values (dict): Dictionary containing field values.

        Returns:
            dict: The validated field values.

        Raises:
            ValueError: If none of 'pre_update_url', 'development_url', or 'post_update_url' are provided.
        """
        pre_update_url = values.get('pre_update_url')
        development_url = values.get('development_url')
        post_update_url = values.get('post_update_url')

        if not any([pre_update_url, development_url, post_update_url]):
            raise ValueError(
                f'At least one of pre_update_url, development_url, or post_update_url must be provided. {values}')

        return values


def main():
    """
    Main function to demonstrate usage of the decorated class.

    Raises:
        ValueError: If there are errors during file import or validation.
    """
    try:
        data, errors = DataFileImport()
        print(f"Validated data: {data}")
        if errors:
            print(f"Validation errors:")
            for err in errors:
                print(f"Row {err['row_num']}, Column {err['column_name']}: {err['error_message']}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Time the execution of the script
    execution_time = timeit.timeit(main, number=1)
    print(f"Execution time: {execution_time} seconds")
