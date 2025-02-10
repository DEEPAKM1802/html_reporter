from enum import Enum, StrEnum
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
# from Contracts.Contract_File_IO import FileImporter
from Utilities.File_IO import FileImporter


class SiteEnv(str, Enum):
    PRODUCTION = 'prod'
    DEVELOPMENT = 'dev'
    STAGE = 'stage'


class SiteUpdateStatus(StrEnum):
    PRE_UPDATE = 'pre_update'
    UPDATED = 'updated'
    POST_UPDATED = 'post_updated'


class Site(BaseModel):
    name: str
    env: str
    url: str
    update_status: str


class TestStatus(str, Enum):
    PASS = "Passed"
    FAIL = "Failed"
    EXISTING_SITE_ISSUE = "Existing Site Issue"
    ERROR = "Error"


class TestResult(BaseModel):
    Name: str
    Status: TestStatus
    Description: Optional[str] = None
    Actual_Result: Optional[Any] = None
    Proof_Path: Optional[List] = None


class ComparisonResult(BaseModel):
    Name: str
    Status: TestStatus
    Description: Optional[str] = None
    Expected_Result: Optional[Any] = None


# TOML Definitions
class SubscriptionConfig(BaseModel):
    class VideoConfig(BaseModel):
        video_url: str
        xpath: str

    class PdfConfig(BaseModel):
        pdf_url: str
        xpath: str

    class SearchConfig(BaseModel):
        search_url: str
        xpath: str
        keyword: str

    class LoginConfig(BaseModel):
        login_url: str
        username_xpath: str
        username: str
        password_xpath: str
        password: str
        sign_in_xpath: str

    class ProdEnvConfig(BaseModel):
        url: Optional[str] = None
        update_status: Optional[str] = None
        login: Optional['SubscriptionConfig.LoginConfig'] = None
        video: Optional[Dict[str, 'SubscriptionConfig.VideoConfig']] = None
        pdf: Optional[Dict[str, 'SubscriptionConfig.PdfConfig']] = None
        search: Optional[Dict[str, 'SubscriptionConfig.SearchConfig']] = None
        internal_pages: Optional[List[str]] = []
        external_pages: Optional[List[str]] = []

    class StageEnvConfig(BaseModel):
        url: Optional[str] = None
        update_status: Optional[str] = None
        login: Optional['SubscriptionConfig.LoginConfig'] = None
        video: Optional[Dict[str, 'SubscriptionConfig.VideoConfig']] = None
        pdf: Optional[Dict[str, 'SubscriptionConfig.PdfConfig']] = None
        search: Optional[Dict[str, 'SubscriptionConfig.SearchConfig']] = None
        internal_pages: Optional[List[str]] = []
        external_pages: Optional[List[str]] = []

    class DevEnvConfig(BaseModel):
        url: Optional[str] = None
        update_status: Optional[str] = None
        login: Optional['SubscriptionConfig.LoginConfig'] = None
        video: Optional[Dict[str, 'SubscriptionConfig.VideoConfig']] = None
        pdf: Optional[Dict[str, 'SubscriptionConfig.PdfConfig']] = None
        search: Optional[Dict[str, 'SubscriptionConfig.SearchConfig']] = None
        internal_pages: Optional[List[str]] = []
        external_pages: Optional[List[str]] = []

    class EnvConfig(BaseModel):
        prod: Optional['SubscriptionConfig.ProdEnvConfig'] = None
        stage: Optional['SubscriptionConfig.StageEnvConfig'] = None
        dev: Optional['SubscriptionConfig.DevEnvConfig'] = None

    # class Config:  # This is where you set arbitrary_types_allowed=True
    #     arbitrary_types_allowed = True

    name: str
    env: EnvConfig


@FileImporter(file_path="C:\\Users\\deepa\\Documents\\Automation_QA\\QAPlay\\InputFiles\\data1.xlsx")
class DataFileImport(BaseModel):
    name: str
    prod: Optional[int] = None
    dev: Optional[int] = None
    stage: Optional[int] = None


# # For DataFileImport (Excel file)
# data_import = DataFileImport()
# print(data_import)  # Should print the processed DataFileImport objects
#
# # For SubscriptionConfig (TOML file)
# subscription_config = SubscriptionConfig('C:\\Users\\deepa\\Documents\\Automation_QA\\QAPlay\\SiteConfig\\ultimateqa'
#                                          '.toml')
# print(subscription_config)  # Should print the SubscriptionConfig object
