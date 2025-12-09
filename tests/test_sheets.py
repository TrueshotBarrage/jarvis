"""Tests for Google Sheets API wrapper."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.apis.sheets import SheetsAPI, SheetsAPIError


class TestSheetsAPI:
    """Test cases for SheetsAPI class."""

    @pytest.fixture
    def mock_credentials(self, tmp_path: Path) -> Path:
        """Create a mock credentials file."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"type": "service_account"}))
        return creds_file

    @pytest.fixture
    def sheets_api(self, mock_credentials: Path) -> SheetsAPI:
        """Create SheetsAPI instance with mock credentials path."""
        return SheetsAPI(credentials_path=str(mock_credentials))

    def test_init_default_credentials_path(self):
        """Test that default credentials path is used from settings."""
        with patch("jarvis.apis.sheets.settings") as mock_settings:
            mock_settings.google_credentials_path = "custom_creds.json"
            api = SheetsAPI()
            assert api.credentials_path == "custom_creds.json"

    def test_init_explicit_credentials_path(self):
        """Test that explicit credentials path overrides settings."""
        api = SheetsAPI(credentials_path="/path/to/creds.json")
        assert api.credentials_path == "/path/to/creds.json"

    def test_credentials_not_found(self, tmp_path: Path):
        """Test error when credentials file doesn't exist."""
        api = SheetsAPI(credentials_path=str(tmp_path / "nonexistent.json"))
        with pytest.raises(SheetsAPIError, match="Credentials file not found"):
            api._get_service()

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_get_values_raw(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test get_values returns raw 2D array."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        }

        result = sheets_api.get_values("test-sheet-id", "Sheet1")

        assert result == [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        mock_service.spreadsheets().values().get.assert_called_with(
            spreadsheetId="test-sheet-id", range="Sheet1"
        )

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_get_values_as_dict(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test get_values returns list of dicts when as_dict=True."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        }

        result = sheets_api.get_values("test-sheet-id", "Sheet1", as_dict=True)

        assert result == [
            {"Name": "Alice", "Age": "30"},
            {"Name": "Bob", "Age": "25"},
        ]

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_get_values_empty_sheet(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test get_values handles empty sheet."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        result = sheets_api.get_values("test-sheet-id", "Sheet1")
        assert result == [[]]

        result_dict = sheets_api.get_values("test-sheet-id", "Sheet1", as_dict=True)
        assert result_dict == []

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_get_values_headers_only(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test get_values handles sheet with only headers."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Name", "Age"]]
        }

        result = sheets_api.get_values("test-sheet-id", "Sheet1", as_dict=True)
        assert result == []

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_get_values_uneven_rows(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test get_values handles rows shorter than headers."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Name", "Age", "City"], ["Alice", "30"], ["Bob"]]
        }

        result = sheets_api.get_values("test-sheet-id", "Sheet1", as_dict=True)

        assert result == [
            {"Name": "Alice", "Age": "30", "City": ""},
            {"Name": "Bob", "Age": "", "City": ""},
        ]

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_get_spreadsheet_info(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test get_spreadsheet_info returns metadata."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().get().execute.return_value = {
            "properties": {"title": "My Budget"},
            "sheets": [
                {"properties": {"title": "Sheet1"}},
                {"properties": {"title": "Summary"}},
            ],
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/abc123",
        }

        result = sheets_api.get_spreadsheet_info("test-sheet-id")

        assert result == {
            "title": "My Budget",
            "sheets": ["Sheet1", "Summary"],
            "url": "https://docs.google.com/spreadsheets/d/abc123",
        }

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_invalid_spreadsheet_id(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test error handling for invalid spreadsheet ID."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Create a mock response with status 404
        mock_response = MagicMock()
        mock_response.status = 404
        mock_service.spreadsheets().values().get().execute.side_effect = HttpError(
            resp=mock_response, content=b"Not found"
        )

        with pytest.raises(SheetsAPIError, match="Spreadsheet not found"):
            sheets_api.get_values("invalid-id", "Sheet1")

    @patch("jarvis.apis.sheets.build")
    @patch("jarvis.apis.sheets.service_account.Credentials.from_service_account_file")
    def test_service_caching(
        self,
        _mock_from_file: MagicMock,
        mock_build: MagicMock,
        sheets_api: SheetsAPI,
    ):
        """Test that service is cached after first call."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        # Call twice
        sheets_api.get_values("test-sheet-id", "Sheet1")
        sheets_api.get_values("test-sheet-id", "Sheet1")

        # Build should only be called once
        assert mock_build.call_count == 1
