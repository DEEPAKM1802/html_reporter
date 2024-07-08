import timeit
from typing import Any, List, Optional, Tuple, Type
import pandas as pd
import os
import json
from pydantic import BaseModel, ValidationError, Field, model_validator, create_model


class FileReader:
    def read(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError


class ExcelFileReader(FileReader):
    def read(self, file_path: str) -> pd.DataFrame:
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")


class CSVFileReader(FileReader):
    def read(self, file_path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")


class JSONFileReader(FileReader):
    def read(self, file_path: str) -> pd.DataFrame:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f"Error reading JSON file: {e}")


class FileImporter:
    _file_readers = {
        '.xlsx': ExcelFileReader(),
        '.xls': ExcelFileReader(),
        '.csv': CSVFileReader(),
        '.json': JSONFileReader(),
    }

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def __call__(self, cls):


        def wrapper(*args, **kwargs):
            filepath = kwargs.get('filepath', self.file_path)

            if not filepath:
                raise ValueError("Filepath is required for import_file")

            file_extension = os.path.splitext(filepath)[1].lower()
            reader = self._file_readers.get(file_extension)

            if reader is None:
                raise ValueError(
                    f"Unsupported file format {file_extension}. Please upload an Excel, CSV, or JSON file.")

            # Dynamically create a Pydantic model based on the annotations
            class DynamicModel(BaseModel, cls):

                def __call__(self, *args, **kwargs):
                    for field, field_type in cls.__annotations__.items():
                        DynamicModel.__annotations__[field] = field_type

                    df = reader.read(filepath)
                    df = df.replace({pd.NA: None})
                    df = self._validate_headers(df, list(cls.__annotations__.keys()))
                    return self._validate_inputs(cls, df)

            return DynamicModel()
        cls.import_file = wrapper()
        return cls

    @staticmethod
    def _validate_headers(df: pd.DataFrame, expected_columns: List[str]) -> pd.DataFrame:
        actual_columns = set(df.columns)
        if not set(expected_columns).issubset(actual_columns):
            raise ValueError(
                f"Invalid headers in the file. Expected columns: {expected_columns}, Found columns: {actual_columns}")
        return df[expected_columns]

    @staticmethod
    def _validate_inputs(cls, df: pd.DataFrame) -> Tuple[List[Any], List[dict[str, Any]]]:
        valid_data = []
        errors = []

        for index, row in df.iterrows():
            row_dict = row.to_dict()
            # Filter out keys that are not attributes of DynamicModel
            filtered_row_dict = {key: value for key, value in row_dict.items() if key in DynamicModel.__annotations__}
            try:
                file_row = cls(**filtered_row_dict)
                valid_data.append(file_row)
            except ValidationError as e:
                errors.append({'index': index, 'error': str(e)})

        return valid_data, errors


@FileImporter(file_path="..\\data_csv.csv")
class DataFileImport:
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
        pre_update_url = values.get('pre_update_url')
        development_url = values.get('development_url')
        post_update_url = values.get('post_update_url')

        if not any([pre_update_url, development_url, post_update_url]):
            raise ValueError(
                f'At least one of pre_update_url, development_url, or post_update_url must be provided. {values}')

        return values


def main():
    try:
        data = DataFileImport()
        print(f"Validated data: {data}")
    #     if errors:
    #         print(f"Validation errors:")
    #         for err in errors:
    #             print(f"Row {err['row_num']}, Column {err['column_name']}: {err['error_message']}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Time the execution of the script
    execution_time = timeit.timeit(main, number=1)
    print(f"Execution time: {execution_time} seconds")
