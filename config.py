import os
from dotenv import load_dotenv

load_dotenv()


def get_local_secret(name, default=None):
    return os.getenv(name, default)

GSPREAD_SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
GSHEET_CREDENTIALS_PATH = get_local_secret("GSHEET_CREDENTIALS_PATH")
URL_FOR_GSHEET = get_local_secret("URL_FOR_GSHEET")
CLASS_SHEET_NAME = 'Classes'
SPELLS_SHEET_NAME = 'Spells'
RACES_SHEET_NAME = 'Races'
FEATURES_SHEET_NAME = 'Features'
TRAITS_SHEET_NAME = 'Traits'
SKILLS_SHEET_NAME = 'Skills'

