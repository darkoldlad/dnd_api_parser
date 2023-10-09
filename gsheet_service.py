import gspread
from google.oauth2 import service_account
from config import GSPREAD_SCOPE, GSHEET_CREDENTIALS_PATH, URL_FOR_GSHEET


class Gsheet:
    def __init__(self, sheet_url = URL_FOR_GSHEET, scopes = GSPREAD_SCOPE, cred_path = GSHEET_CREDENTIALS_PATH):
        self.sheet = gspread.authorize(
            service_account.Credentials.from_service_account_file(cred_path)
            .with_scopes(scopes)
        ).open_by_url(sheet_url)

    def get_worksheet(self, gsheet_name: str):
        try:
            worksheet = self.sheet.worksheet(gsheet_name)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.sheet.add_worksheet(title=gsheet_name, rows="1000", cols="26")
            return worksheet
