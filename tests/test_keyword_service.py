"""
Unit tests for Google High-Rank Keyword Finder and SEO Service.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.services.keyword_service import GoogleKeywordResearchService


class TestGoogleKeywordService:
    def test_empty_query_returns_empty_list(self):
        res = GoogleKeywordResearchService.fetch_google_suggestions("")
        assert res == []

    @patch("urllib.request.urlopen")
    def test_mock_google_autocomplete(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'["shoes", ["shoes for men", "shoes online", "shoes for women"]]'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        results = GoogleKeywordResearchService.fetch_google_suggestions("shoes", country="in", deep_scan=False)
        assert len(results) >= 3
        kws = [r["keyword"] for r in results]
        assert "shoes for men" in kws
        assert "shoes online" in kws

    def test_intent_classification(self):
        metrics = GoogleKeywordResearchService._calculate_keyword_metrics("buy leather wallet online", 0, "leather wallet")
        assert "Transactional" in metrics["intent"]
        assert "₹" in metrics["est_cpc"]
        assert "%" in metrics["kd_pct"]

    def test_amazon_249_byte_optimizer(self):
        # Long string with punctuation, stop words, and duplicate terms
        raw = "wallet, leather wallet! mens wallet, best RFID blocking, the, and, wallet for men, leather gift item"
        res = GoogleKeywordResearchService.optimize_amazon_backend_search_terms(raw)

        assert res["byte_count"] <= 249
        assert res["is_safe"] is True
        assert "," not in res["clean_terms"]
        assert "!" not in res["clean_terms"]
        # Duplicate word "wallet" must appear only once
        words = res["clean_terms"].split()
        assert words.count("wallet") == 1
        # Stop-words like 'the', 'and' removed
        assert "the" not in words
        assert "and" not in words

    def test_negative_keywords_generation(self):
        res = GoogleKeywordResearchService.generate_negative_keywords("leather wallet")
        assert "negative_phrase" in res
        assert "negative_exact" in res
        assert "free" in res["negative_phrase"]
        assert any("leather wallet free" in k for k in res["negative_exact"])

    def test_keyword_density_analysis(self):
        text = "This genuine leather wallet is a classic bifold leather wallet for men."
        kws = ["leather wallet", "bifold", "shoes"]
        res = GoogleKeywordResearchService.analyze_keyword_density(text, kws)
        assert len(res) == 3

        lw = next(r for r in res if r["keyword"] == "leather wallet")
        assert lw["count"] == 2
        assert "Optimal" in lw["status"] or "Warning" in lw["status"]

        shoes = next(r for r in res if r["keyword"] == "shoes")
        assert shoes["count"] == 0
        assert "Missing" in shoes["status"]

    def test_ai_seo_strategy_mock(self):
        with patch("src.services.keyword_service.CommerceCalcAI") as MockAI:
            mock_instance = MockAI.return_value
            mock_instance.generate_response.return_value = "Optimized Product Title: Premium Men's Cotton T-Shirt"

            res = GoogleKeywordResearchService.generate_seo_strategy_with_ai(
                "cotton t shirt", ["cotton t shirt for men", "best cotton t shirt"], channel="Amazon India"
            )
            assert "Premium Men's Cotton T-Shirt" in res
            assert mock_instance.generate_response.called
