import os
import toml
from typing import List, Type, TypeVar, Dict, Optional

from Utilities.Data_Structures import SubscriptionConfig, SiteUpdateStatus, DataFileImport
from Utilities.File_IO import FileImporter
from pydantic import BaseModel

# Define your Pydantic models here (as you provided)
T = TypeVar('T', bound=BaseModel)


class ConfigLoader:
    update_status_mapping = {
        0: SiteUpdateStatus.PRE_UPDATE,
        1: SiteUpdateStatus.UPDATED,
        2: SiteUpdateStatus.POST_UPDATED,
    }

    def __init__(self, file_path: str = None):
        self.file_path = file_path
        self.config_objects = self._load_config_objects()
        self.loaded_configs = {}  # To store loaded TOML configurations

    def __iter__(self):
        return iter(self.config_objects)

    def __str__(self):
        return '\n'.join(str(obj) for obj in self.config_objects)

    def __repr__(self):
        return f'ConfigLoader(file_path={self.file_path}, config_objects={self.config_objects})'

    def _load_config_objects(self) -> List[SubscriptionConfig]:
        imported_data = DataFileImport(self.file_path)[0]  # Assumes DataFileImport returns [0] for the rows
        print("imported_data---------->>", imported_data)
        return self.process_imported_data(imported_data, SubscriptionConfig)

    @staticmethod
    def dict_to_pydantic(model: Type[T], data: Dict) -> T:
        return model(**data)

    # @staticmethod
    # def load_toml_config_as_object(name: str) -> Dict:
    #     file_path = os.path.join("SiteConfig", f"{name}.toml")
    #
    #     if os.path.exists(file_path):
    #         with open(file_path, 'r') as file:
    #             config_data = toml.load(file)
    #         subscription_data = config_data['subscription']
    #         subscription_data['name'] = name  # Ensure the name is included
    #         return subscription_data
    #     else:
    #         raise FileNotFoundError(f"No configuration file found for {name} at {file_path}")

    @staticmethod
    def load_toml_config_as_object(name: str) -> Dict:
        file_path = os.path.join("SiteConfig", f"{name}.toml")
        sample_file_path = os.path.join("SiteConfig", "sample.toml")

        if not os.path.exists(file_path):
            if not os.path.exists(sample_file_path):
                raise FileNotFoundError(f"Sample configuration file not found at {sample_file_path}")

            # Load data from sample.toml
            with open(sample_file_path, 'r') as sample_file:
                sample_data = toml.load(sample_file)

            # Write the sample data to the new file
            with open(file_path, 'w') as new_file:
                toml.dump(sample_data, new_file)

        # Load and return the data from the specified file
        with open(file_path, 'r') as file:
            config_data = toml.load(file)

        subscription_data = config_data.get('subscription', {})
        subscription_data['name'] = name  # Ensure the name is included

        return subscription_data

    @staticmethod
    def process_imported_data(successful_rows: List[BaseModel], model: Type[T]) -> List[T]:
        config_objects = []
        for row in successful_rows:
            try:
                subscription_data = ConfigLoader.load_toml_config_as_object(row.name)

                # Add update_status to the appropriate env based on the row data
                env_config = subscription_data.get('env', {})

                if 'prod' in env_config:
                    if row.prod is not None:
                        env_config['prod']['update_status'] = ConfigLoader.update_status_mapping.get(row.prod)
                    if env_config['prod'].get('update_status') is None:
                        env_config.pop('prod')

                if 'stage' in env_config:
                    if row.stage is not None:
                        env_config['stage']['update_status'] = ConfigLoader.update_status_mapping.get(row.stage)
                    if env_config['stage'].get('update_status') is None:
                        env_config.pop('stage')

                if 'dev' in env_config:
                    if row.dev is not None:
                        env_config['dev']['update_status'] = ConfigLoader.update_status_mapping.get(row.dev)
                    if env_config['dev'].get('update_status') is None:
                        env_config.pop('dev')

                subscription_data['env'] = env_config

                config = ConfigLoader.dict_to_pydantic(model, subscription_data)
                config_objects.append(config)
            except FileNotFoundError as e:
                print(e)
        return config_objects

# #  name='ultimateqa'
# # env=EnvConfig(
# #     prod=ProdEnvConfig(url='https://courses.ultimateqa.com',
# #                        update_status='pre_update',
# #                        login=LoginConfig(
# #                            login_url='https://courses.ultimateqa.com/users/sign_in',
# #                            username_xpath='//*[@id="user[email]"]',
# #                            username='mishra@test.com',
# #                            password_xpath='//*[@id="user[password]"]',
# #                            password='qatest123',
# #                            sign_in_xpath='button:text("Sign in")'),
# #                        video={'video1': VideoConfig(video_url='', xpath=''), 'video2': VideoConfig(video_url='', xpath='')},
# #                        pdf={'pdf1': PdfConfig(pdf_url='', xpath=''), 'pdf2': PdfConfig(pdf_url='', xpath='')},
# #                        search={'search1': SearchConfig(search_url='', xpath='', keyword=''), 'search2': SearchConfig(search_url='', xpath='', keyword='')}, internal_pages=[], external_pages=[]),
# #     stage=StageEnvConfig(url='', update_status='updated', login=LoginConfig(login_url='https://www.saucedemo.com/', username_xpath='//*[@id="user-name"]', username='standard_user', password_xpath='//*[@id="
# # password"]', password='secret_sauce', sign_in_xpath='//*[@id="login-button"]'), video={'video1': VideoConfig(video_url='', xpath=''), 'video2': VideoConfig(vi
# # deo_url='', xpath='')}, pdf={'pdf1': PdfConfig(pdf_url='', xpath=''), 'pdf2': PdfConfig(pdf_url='', xpath='')}, search={'search1': SearchConfig(search_url='', xpath='', keyword=''), 'search2': SearchConfig(search_url='', xpath='', keyword='')}, internal_pages=[], external_pages=[]), dev=None)
# #
# #
# #
# # name='ultimateqa1' env=EnvConfig(prod=ProdEnvConfig(url='https://courses.ultimateqa.com', update_status='pre_update', login=LoginConfig(login_url='https://cou
# # rses.ultimateqa.com/users/sign_in', username_xpath='//*[@id="user[email]"]', username='mishra@test.com', password_xpath='//*[@id="user[password]"]', password=
# # 'qatest123', sign_in_xpath='button:text("Sign in")'), video={'video1': VideoConfig(video_url='', xpath=''), 'video2': VideoConfig(video_url='', xpath='')}, pd
# # f={'pdf1': PdfConfig(pdf_url='', xpath=''), 'pdf2': PdfConfig(pdf_url='', xpath='')}, search={'search1': SearchConfig(search_url='', xpath='', keyword=''), 's
# # earch2': SearchConfig(search_url='', xpath='', keyword='')}, internal_pages=[], external_pages=[]), stage=StageEnvConfig(url='', update_status='updated', logi
# # n=LoginConfig(login_url='https://www.saucedemo.com/', username_xpath='//*[@id="user-name"]', username='standard_user', password_xpath='//*[@id="password"]', p
# # assword='secret_sauce', sign_in_xpath='//*[@id="login-button"]'), video={'video1': VideoConfig(video_url='', xpath=''), 'video2': VideoConfig(video_url='', xp
# # ath='')}, pdf={'pdf1': PdfConfig(pdf_url='', xpath=''), 'pdf2': PdfConfig(pdf_url='', xpath='')}, search={'search1': SearchConfig(search_url='', xpath='', keyword=''), 'search2': SearchConfig(search_url='', xpath='', keyword='')}, internal_pages=[], external_pages=[]), dev=None)

# @FileImporter
# class TomlConfigImporter(BaseModel):
#     subscription: SubscriptionConfig

#
# class ConfigLoader:
#     update_status_mapping = {
#         0: SiteUpdateStatus.PRE_UPDATE,
#         1: SiteUpdateStatus.UPDATED,
#         2: SiteUpdateStatus.POST_UPDATED,
#     }
#
#     def __init__(self, file_path: str = None):
#         self.file_path = file_path
#         self.config_objects = self._load_config_objects()
#
#     def __iter__(self):
#         return iter(self.config_objects)
#
#     def __str__(self):
#         return '\n'.join(str(obj) for obj in self.config_objects)
#
#     def __repr__(self):
#         return f'ConfigLoader(file_path={self.file_path}, config_objects={self.config_objects})'
#
#     def _load_config_objects(self) -> List[SubscriptionConfig]:
#         print(self.file_path)
#         imported_data = SubscriptionConfig(self.file_path)  # Load TOML config directly
#         return self.process_imported_data([imported_data.subscription], SubscriptionConfig)
#
#     @staticmethod
#     def dict_to_pydantic(model: Type[T], data: Dict) -> T:
#         return model(**data)
#
#     @staticmethod
#     def load_toml_config_as_object(name: str) -> Dict:
#         file_path = os.path.join("SiteConfig", f"{name}.toml")
#
#         if os.path.exists(file_path):
#             with open(file_path, 'r') as file:
#                 config_data = toml.load(file)
#             subscription_data = config_data['subscription']
#             subscription_data['name'] = name  # Ensure the name is included
#             return subscription_data
#         else:
#             raise FileNotFoundError(f"No configuration file found for {name} at {file_path}")
#
#     @staticmethod
#     def process_imported_data(successful_rows: List[BaseModel], model: Type[T]) -> List[T]:
#         config_objects = []
#         for row in successful_rows:
#             try:
#                 subscription_data = ConfigLoader.load_toml_config_as_object(row.name)
#
#                 # Add update_status to the appropriate env based on the row data
#                 env_config = subscription_data.get('env', {})
#
#                 if 'prod' in env_config:
#                     if row.prod is not None:
#                         env_config['prod']['update_status'] = ConfigLoader.update_status_mapping.get(row.prod)
#                     if env_config['prod'].get('update_status') is None:
#                         env_config.pop('prod')
#
#                 if 'stage' in env_config:
#                     if row.stage is not None:
#                         env_config['stage']['update_status'] = ConfigLoader.update_status_mapping.get(row.stage)
#                     if env_config['stage'].get('update_status') is None:
#                         env_config.pop('stage')
#
#                 if 'dev' in env_config:
#                     if row.dev is not None:
#                         env_config['dev']['update_status'] = ConfigLoader.update_status_mapping.get(row.dev)
#                     if env_config['dev'].get('update_status') is None:
#                         env_config.pop('dev')
#
#                 subscription_data['env'] = env_config
#
#                 config = ConfigLoader.dict_to_pydantic(model, subscription_data)
#                 config_objects.append(config)
#             except FileNotFoundError as e:
#                 print(e)
#         return config_objects


# Example usage of the TomlConfigImporter
# config_loader = ConfigLoader(
#     file_path='C:\\Users\\deepa\\Documents\\Automation_QA\\QAPlay\\SiteConfig\\ultimateqa.toml')
# for config in config_loader:
#     print(config)
