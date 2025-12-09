"""Google Sheets API wrapper module.

This module provides a wrapper around the Google Sheets API
using service account authentication for server-to-server access.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from jarvis.config import settings


class SheetsAPIError(Exception):
    """Exception raised for Sheets API errors."""

    pass


class SheetsAPI:
    """Google Sheets API wrapper using service account authentication.

    This class provides methods to interact with Google Sheets API,
    reading cell values and spreadsheet metadata. It uses a service account
    for authentication, which requires sharing target spreadsheets with
    the service account's email address.

    Attributes:
        logger: Module logger instance.
        credentials_path: Path to service account credentials JSON.
    """

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def __init__(self, credentials_path: str | None = None) -> None:
        """Initialize the Sheets API client.

        Args:
            credentials_path: Path to the service account credentials JSON file.
                Defaults to config setting or "google_credentials.json".
        """
        self.logger = logging.getLogger(__name__)
        self.credentials_path = credentials_path or settings.google_credentials_path
        self._service: Any | None = None

    def _get_service(self) -> Any:
        """Get or create the Sheets API service.

        Returns:
            The Google Sheets API service object.

        Raises:
            SheetsAPIError: If credentials file is missing or invalid.
        """
        if self._service is not None:
            return self._service

        creds_path = Path(self.credentials_path)
        if not creds_path.exists():
            raise SheetsAPIError(
                f"Credentials file not found: {self.credentials_path}. "
                "Please download your service account credentials from "
                "Google Cloud Console and save them to this path."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=self.SCOPES
            )
            self._service = build("sheets", "v4", credentials=credentials)
            self.logger.info("Google Sheets API service initialized")
            return self._service
        except (GoogleAuthError, json.JSONDecodeError) as e:
            raise SheetsAPIError(f"Failed to initialize Sheets API: {e}") from e

    def get_values(
        self,
        spreadsheet_id: str,
        range: str = "Sheet1",
        as_dict: bool = False,
    ) -> list[list[Any]] | list[dict[str, Any]]:
        """Read cell values from a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID from the URL
                (e.g., "1swMouCuTbENYNcpVFettBCGtU7OmTvCRkaxauk0KBV1").
            range: A1 notation range (e.g., "Sheet1!A1:B10" or just "Sheet1").
                Defaults to "Sheet1" which returns all data in the first sheet.
            as_dict: If True, return list of dicts using first row as headers.
                If False, return raw 2D array.

        Returns:
            If as_dict is False: A 2D list of cell values.
            If as_dict is True: A list of dictionaries with first row as keys.

        Raises:
            SheetsAPIError: If the API request fails.
        """
        try:
            service = self._get_service()

            self.logger.info(f"Fetching values from spreadsheet {spreadsheet_id}, range: {range}")

            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range)
                .execute()
            )

            values = result.get("values", [])
            self.logger.info(f"Retrieved {len(values)} rows from {spreadsheet_id}")

            if not values:
                return [] if as_dict else [[]]

            if as_dict:
                return self._values_to_dicts(values)

            return values

        except HttpError as e:
            if e.resp.status == 404:
                raise SheetsAPIError(
                    f"Spreadsheet not found: {spreadsheet_id}. "
                    "Check the ID and ensure it's shared with the service account."
                ) from e
            raise SheetsAPIError(f"Sheets API request failed: {e}") from e

    def _values_to_dicts(self, values: list[list[Any]]) -> list[dict[str, Any]]:
        """Convert 2D array to list of dictionaries.

        Uses the first row as headers/keys for the dictionaries.

        Args:
            values: 2D list of cell values.

        Returns:
            List of dictionaries with first row values as keys.
        """
        if len(values) < 2:
            # Only headers or empty
            return []

        headers = values[0]
        rows = values[1:]

        result = []
        for row in rows:
            # Pad row with empty strings if shorter than headers
            padded_row = row + [""] * (len(headers) - len(row))
            row_dict = {headers[i]: padded_row[i] for i in range(len(headers))}
            result.append(row_dict)

        return result

    def get_spreadsheet_info(self, spreadsheet_id: str) -> dict[str, Any]:
        """Get spreadsheet metadata.

        Args:
            spreadsheet_id: The spreadsheet ID from the URL.

        Returns:
            Dictionary containing:
                - title: Spreadsheet title
                - sheets: List of sheet names in the spreadsheet
                - url: Web URL to the spreadsheet

        Raises:
            SheetsAPIError: If the API request fails.
        """
        try:
            service = self._get_service()

            self.logger.info(f"Fetching metadata for spreadsheet {spreadsheet_id}")

            result = (
                service.spreadsheets()
                .get(
                    spreadsheetId=spreadsheet_id,
                    fields="properties.title,sheets.properties.title,spreadsheetUrl",
                )
                .execute()
            )

            sheets = [sheet["properties"]["title"] for sheet in result.get("sheets", [])]

            return {
                "title": result.get("properties", {}).get("title", "Untitled"),
                "sheets": sheets,
                "url": result.get("spreadsheetUrl", ""),
            }

        except HttpError as e:
            if e.resp.status == 404:
                raise SheetsAPIError(
                    f"Spreadsheet not found: {spreadsheet_id}. "
                    "Check the ID and ensure it's shared with the service account."
                ) from e
            raise SheetsAPIError(f"Sheets API request failed: {e}") from e
