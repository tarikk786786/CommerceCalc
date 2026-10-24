"""
Unit tests for GoogleIntegrationService and Google linking functionality.
"""

import os
from unittest.mock import patch
from apps.CommerceCalc.src.services.google_integration_service import GoogleIntegrationService


def test_google_integration_status():
    status = GoogleIntegrationService.get_status()
    assert isinstance(status, dict)
    assert "connected" in status
    assert "services_active" in status
    assert len(status["services_active"]) > 0


def test_google_integration_save_credentials(tmp_path):
    test_key = "AIzaSyFakeKeyForTesting123456789"
    fake_appinfo = tmp_path / "appinfo11.txt"
    fake_appinfo.write_text("GEMINI_API_KEY=\nGOOGLE_API_KEY=\n", encoding="utf-8")
    with patch.dict(os.environ, {}, clear=True):
        res = GoogleIntegrationService.save_google_credentials(test_key, appinfo_paths=[fake_appinfo])
        assert res is True
        assert os.environ.get("GEMINI_API_KEY") == test_key
        assert os.environ.get("GOOGLE_API_KEY") == test_key
        content = fake_appinfo.read_text(encoding="utf-8")
        assert f"GEMINI_API_KEY={test_key}" in content


def test_google_integration_empty_key():
    res = GoogleIntegrationService.save_google_credentials("   ")
    assert res is False


@patch("webbrowser.open")
def test_google_trends_launch(mock_open):
    GoogleIntegrationService.open_google_trends("wireless earbuds", geo="IN")
    mock_open.assert_called_once()
    url = mock_open.call_args[0][0]
    assert "trends.google.com" in url
    assert "wireless%20earbuds" in url
    assert "geo=IN" in url


@patch("webbrowser.open")
def test_google_search_console_launch(mock_open):
    GoogleIntegrationService.open_google_search_console()
    mock_open.assert_called_once_with("https://search.google.com/search-console")


@patch("webbrowser.open")
def test_google_keyword_planner_launch(mock_open):
    GoogleIntegrationService.open_google_keyword_planner()
    mock_open.assert_called_once_with("https://ads.google.com/home/tools/keyword-planner/")


@patch("webbrowser.open")
def test_google_merchant_center_launch(mock_open):
    GoogleIntegrationService.open_google_merchant_center()
    mock_open.assert_called_once_with("https://merchants.google.com/")
