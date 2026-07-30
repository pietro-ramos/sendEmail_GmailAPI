from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


GMAIL_SEND_SCOPES = ("https://www.googleapis.com/auth/gmail.send",)


class Auth:
    def __init__(
        self,
        token_path: str = "token.json",
        credentials_path: str = "credentials.json",
        scopes: tuple[str, ...] = GMAIL_SEND_SCOPES,
        force_browser_login: bool = False,
    ) -> None:
        self.token_path = Path(token_path)
        self.credentials_path = Path(credentials_path)
        self.scopes = scopes
        self.force_browser_login = force_browser_login
        self.creds = None

        if not force_browser_login and self.token_path.is_file():
            self.creds = Credentials.from_authorized_user_file(
                self.token_path,
                self.scopes,
            )
        if not self.creds or not self.creds.valid:
            self._refresh_or_authenticate()

    def _refresh_or_authenticate(self) -> None:
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
        else:
            if not self.credentials_path.is_file():
                raise FileNotFoundError(
                    f"Credenciais Gmail não encontradas: {self.credentials_path}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                self.scopes,
            )
            login_options = {"port": 0}
            if self.force_browser_login:
                login_options["prompt"] = "select_account"
            self.creds = flow.run_local_server(**login_options)

        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(self.creds.to_json(), encoding="utf-8")

    def get_service(self):
        if not self.creds or not self.creds.valid:
            self._refresh_or_authenticate()
        return build(
            "gmail",
            "v1",
            credentials=self.creds,
            cache_discovery=False,
        )
