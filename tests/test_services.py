"""
Unit tests for CommerceCalc AI, Updater, and Public APIs Services.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.services.api_directory_service import APIDirectoryService
from src.services.updater import UpdateChecker, parse_semver, CURRENT_VERSION
from src.services.ai_service import CommerceCalcAI, get_api_key


class TestAPIDirectoryService:
    def test_curated_apis_catalog(self):
        apis = APIDirectoryService.get_curated_apis()
        assert len(apis) >= 6
        names = [a["name"] for a in apis]
        sources = [a["repo_source"] for a in apis]
        assert any("public-apis" in s for s in sources)
        assert any("openapi-directory" in s for s in sources)
        assert any("Pipedream" in s for s in sources)

    def test_pincode_validation(self):
        # Invalid PIN length
        res = APIDirectoryService.lookup_pincode_zone("123")
        assert res["success"] is False
        assert "6 digits" in res["error"]

    def test_pipedream_invalid_url(self):
        res = APIDirectoryService.send_to_pipedream("invalid_url", {"test": 123})
        assert res["success"] is False
        assert "valid Pipedream" in res["error"]

    @patch("urllib.request.urlopen")
    def test_forex_rates_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"result":"success","rates":{"INR":85.5,"USD":1.0},"time_last_update_utc":"2026-10-23"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = APIDirectoryService.fetch_live_forex_rates("USD")
        assert res["success"] is True
        assert res["inr_rate"] == 85.5
        assert res["base"] == "USD"


class TestUpdateChecker:
    def test_parse_semver(self):
        assert parse_semver("v1.0.0") == (1, 0, 0)
        assert parse_semver("1.2.3") == (1, 2, 3)
        assert parse_semver("v2.10.4") == (2, 10, 4)
        assert parse_semver("invalid") == (0, 0, 0)

    def test_version_info(self):
        info = UpdateChecker.get_version_info()
        assert info["version"] == CURRENT_VERSION
        assert "Python" in info["python_env"]
        assert "PySide6" in info["ui_framework"]

    @patch("urllib.request.urlopen")
    def test_check_for_updates_available(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"tag_name":"v2.0.0","name":"Release 2.0.0","body":"Big AI updates","html_url":"https://github.com/..."}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        checker = UpdateChecker(current_version="1.0.0")
        res = checker.check_for_updates()
        assert res["success"] is True
        assert res["update_available"] is True
        assert res["latest_version"] == "v2.0.0"

    @patch("urllib.request.urlopen")
    def test_check_for_updates_already_current(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"tag_name":"v1.0.0","name":"Release 1.0.0","body":"No updates","html_url":"https://github.com/..."}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        checker = UpdateChecker(current_version="1.0.0")
        res = checker.check_for_updates()
        assert res["success"] is True
        assert res["update_available"] is False


class TestCommerceCalcAI:
    def test_ai_configured(self):
        ai = CommerceCalcAI()
        # Verifies that cloud AI providers (Groq, OpenRouter, or Gemini) are configured
        assert ai.is_configured() is True
        assert ai.gemini_key != "" or ai.groq_key != "" or ai.openrouter_key != ""

    def test_prompt_generation(self):
        ai = CommerceCalcAI()
        with patch.object(ai, "generate_response", return_value="Verified Output") as mock_gen:
            res = ai.analyze_product_profitability({
                "product_name": "Leather Wallet",
                "selling_price": "799",
                "purchase_cost": "250",
            })
            assert res == "Verified Output"
            assert mock_gen.called
