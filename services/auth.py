import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class Auth:
    def __init__(
        self,
        token_path='token.json',
        credentials_path='credentials.json',
        force_browser_login=False,
    ):
        self.creds = None
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.force_browser_login = force_browser_login
        if not force_browser_login and os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        if not self.creds or not self.creds.valid:
            self._refresh_or_authenticate()

    def _refresh_or_authenticate(self):
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                SCOPES,
            )
            login_options = {"port": 0}
            if self.force_browser_login:
                login_options["prompt"] = "select_account"
            self.creds = flow.run_local_server(**login_options)

        with open(self.token_path, 'w') as token:
            token.write(self.creds.to_json())

    def get_service(self):
        if not self.creds or not self.creds.valid:
            self._refresh_or_authenticate()
        return build('gmail', 'v1', credentials=self.creds)
