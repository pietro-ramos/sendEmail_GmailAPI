import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']


class Auth:
    def __init__(self):
        self.creds = None
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not self.creds or not self.creds.valid:
            self._refresh_or_authenticate()

    def _refresh_or_authenticate(self):
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            self.creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(self.creds.to_json())

    def get_service(self):
        if not self.creds or not self.creds.valid:
            self._refresh_or_authenticate()
        return build('gmail', 'v1', credentials=self.creds)
