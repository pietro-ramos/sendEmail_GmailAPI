import time
import msal


class GraphAuth:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self._authority = f"https://login.microsoftonline.com/{tenant_id}"
        self._app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=self._authority,
            client_credential=client_secret,
        )
        self._token = None
        self._expires_at = 0.0

    def get_token(self) -> str:
        now = time.time()
        if not self._token or now >= (self._expires_at - 60):
            result = self._app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            if "access_token" not in result:
                error_msg = result.get("error_description") or result.get("error") or "unknown error"
                raise RuntimeError(f"Falha ao obter token do Graph: {error_msg}")
            self._token = result["access_token"]
            self._expires_at = now + float(result.get("expires_in", 3600))
        return self._token
