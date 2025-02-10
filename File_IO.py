import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import numpy as np
import pandas as pd
import toml
from pydantic import ValidationError


class FileReader:
    def read(self, file_path: str) -> pd.DataFrame:
        try:
            return self._read_file(file_path)
        except Exception as e:
            raise ValueError(f"Error reading {self.__class__.__name__}: {e}")

    def _read_file(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError


class ExcelFileReader(FileReader):
    def _read_file(self, file_path: str) -> pd.DataFrame:
        return pd.read_excel(file_path, engine='openpyxl')


class CSVFileReader(FileReader):
    def _read_file(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path, low_memory=False)


class JSONFileReader(FileReader):
    def _read_file(self, file_path: str) -> pd.DataFrame:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return pd.DataFrame(data)


class TomlFileReader(FileReader):
    def _read_file(self, file_path: str) -> pd.DataFrame:
        with open(file_path, 'r') as f:
            x = toml.load(f)
            return toml.load(f)


class Validator:

    @classmethod
    def validate_headers(cls, df: pd.DataFrame, expected_columns: List[str]) -> pd.DataFrame:
        actual_columns = set(df.columns)
        if not set(expected_columns).issubset(actual_columns):
            raise ValueError(
                f"Invalid headers in the file. Expected columns: {expected_columns}, Found columns: {actual_columns}")
        return df[expected_columns]

    @classmethod
    def validate_inputs_parallel(cls, df: pd.DataFrame, ModelClass):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(cls.validate_row, row, ModelClass) for index, row in df.iterrows()]
            results = [future.result() for future in futures]

        valid_data = [result[0] for result in results if result[0] is not None]
        errors = [error for result in results for error in (result[1] or [])]
        return valid_data, errors

    @staticmethod
    def validate_row(row, ModelClass):
        try:
            return ModelClass(**row.to_dict()), None
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                expected_type = ModelClass.__annotations__[error['loc'][0]]
                expected = getattr(expected_type, '__args__', expected_type)
                error_detail = {
                    'row': row.name + 1,
                    'column': error['loc'][0],
                    'message': error['msg'],
                    'expected': expected,
                    'actual': row[error['loc'][0]]
                }
                error_details.append(error_detail)
            return None, error_details


class FileImporter:
    _file_readers = {
        '.xlsx': ExcelFileReader(),
        '.xls': ExcelFileReader(),
        '.csv': CSVFileReader(),
        '.json': JSONFileReader(),
        '.toml': TomlFileReader()
    }

    def __init__(self, file_path=None):
        self.file_path = file_path

    def __call__(self, cls):
        def wrapper(filepath=None):

            if type(filepath) is str:
                filepath = filepath or self.file_path
                if not filepath:
                    raise ValueError("Filepath is required for import_file")

                file_extension = os.path.splitext(filepath)[1].lower()
                reader = self._file_readers.get(file_extension)
                print(reader)

                if reader is None:
                    raise ValueError(f"Unsupported file format {file_extension}. Please upload a supported file type.")

                if file_extension == '.toml':
                    # For TOML, load the entire content and convert it to the Pydantic model
                    toml_data = reader.read(filepath)
                    return cls(**toml_data)  # Directly convert the TOML data to the Pydantic model
                else:
                    # For other formats, assume they return a DataFrame
                    df = reader.read(filepath)
                    df = df.replace(np.nan, None)
                    valid_data, errors = Validator.validate_inputs_parallel(df, cls)
                    return valid_data, errors

            elif type(filepath) is pd.DataFrame:
                df = filepath
                df = df.replace(np.nan, None)
                valid_data, errors = Validator.validate_inputs_parallel(df, cls)
                return valid_data, errors

            elif type(filepath) is list:
                df = pd.DataFrame.from_records(filepath)
                df = df.replace(np.nan, None)
                valid_data, errors = Validator.validate_inputs_parallel(df, cls)
                return valid_data, errors

            elif type(filepath) is dict:
                df = pd.DataFrame.from_dict(filepath)
                df = df.replace(np.nan, None)
                valid_data, errors = Validator.validate_inputs_parallel(df, cls)
                return valid_data, errors

            else:
                print("Invalid Input File")

        # Return a callable that automatically uses the wrapper
        return wrapper
