from __future__ import annotations

from pathlib import Path
from typing import Any


DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive.file",)
AUTH_MODE_SERVICE_ACCOUNT = "service_account"
AUTH_MODE_OAUTH = "oauth"


class DriveUploadError(RuntimeError):
    pass


def upload_to_drive(
    local_path: Path,
    credentials_file: Path,
    folder_name: str,
    folder_id: str | None = None,
    auth_mode: str = AUTH_MODE_SERVICE_ACCOUNT,
    token_file: Path | None = None,
) -> dict[str, str]:
    service = _build_drive_service(
        credentials_file=credentials_file,
        auth_mode=auth_mode,
        token_file=token_file,
    )
    target_folder_id = folder_id or _get_or_create_folder(service, folder_name)

    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise DriveUploadError(
            "Google Drive dependencies are not installed. Install google-api-python-client and google-auth."
        ) from exc

    media = MediaFileUpload(str(local_path), resumable=False)
    existing_file_id = _find_file_by_name(service, local_path.name, target_folder_id)
    if existing_file_id:
        file = (
            service.files()
            .update(fileId=existing_file_id, media_body=media, fields="id, webViewLink")
            .execute()
        )
    else:
        metadata = {"name": local_path.name, "parents": [target_folder_id]}
        file = (
            service.files()
            .create(body=metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )
    return {
        "drive_file_id": file["id"],
        "drive_url": file.get("webViewLink") or f"https://drive.google.com/file/d/{file['id']}/view",
    }


def _build_drive_service(
    credentials_file: Path,
    auth_mode: str,
    token_file: Path | None,
) -> Any:
    normalized_auth_mode = auth_mode.strip().lower()
    if normalized_auth_mode == AUTH_MODE_OAUTH:
        return _build_oauth_service(credentials_file, token_file)
    if normalized_auth_mode == AUTH_MODE_SERVICE_ACCOUNT:
        return _build_service_account_service(credentials_file)
    raise DriveUploadError(f"Unsupported Google Drive auth mode: {auth_mode}")


def _build_service_account_service(service_account_file: Path) -> Any:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise DriveUploadError(
            "Google Drive dependencies are not installed. Install google-api-python-client and google-auth."
        ) from exc

    if not service_account_file.exists():
        raise DriveUploadError(f"Google Drive service account file not found: {service_account_file}")

    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=DRIVE_SCOPES,
    )
    return build("drive", "v3", credentials=credentials)


def _build_oauth_service(client_secret_file: Path, token_file: Path | None) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise DriveUploadError(
            "OAuth dependencies are not installed. Install google-auth-oauthlib."
        ) from exc

    if not client_secret_file.exists():
        raise DriveUploadError(f"Google Drive OAuth client file not found: {client_secret_file}")

    token_path = token_file or client_secret_file.with_name("google-drive-token.json")
    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), DRIVE_SCOPES)

    if credentials is None or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), DRIVE_SCOPES)
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=credentials)


def _get_or_create_folder(service: Any, folder_name: str) -> str:
    escaped_name = folder_name.replace("'", "\\'")
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{escaped_name}' and trashed=false"
    )
    result = service.files().list(q=query, spaces="drive", fields="files(id, name)", pageSize=1).execute()
    files = result.get("files", [])
    if files:
        return files[0]["id"]

    folder = (
        service.files()
        .create(
            body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id",
        )
        .execute()
    )
    return folder["id"]


def _find_file_by_name(service: Any, filename: str, folder_id: str) -> str | None:
    escaped_name = filename.replace("'", "\\'")
    query = f"'{folder_id}' in parents and name='{escaped_name}' and trashed=false"
    result = service.files().list(q=query, spaces="drive", fields="files(id)", pageSize=1).execute()
    files = result.get("files", [])
    return files[0]["id"] if files else None
