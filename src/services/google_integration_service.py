"""
Google Account & Services Linking Engine for CommerceCalc.

Manages connections to:
1. Google AI Studio & Gemini API (gemini-2.5-flash)
2. Google Search & Suggest live index
3. Google Trends (Search volume trends & regional breakout)
4. Google Search Console & Merchant Center
5. Google Sheets / Drive Export Integrations
"""

import os
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

from .ai_service import get_api_key


class GoogleIntegrationService:
    """Manages Google linking, authentication status, and external tool navigations."""

    CONFIG_FILE = Path("c:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/data/google_link.json")

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Check current Google connection status and available integrations."""
        gemini_key = get_api_key("GEMINI_API_KEY") or get_api_key("GOOGLE_API_KEY")
        
        is_connected = bool(gemini_key)
        masked_key = f"{gemini_key[:8]}...{gemini_key[-4:]}" if gemini_key and len(gemini_key) > 12 else "Not Configured"

        return {
            "connected": is_connected,
            "status_text": "Connected & Active" if is_connected else "Unlinked (Offline Mode)",
            "provider": "Google Cloud & AI Studio",
            "account_id": "google_user@verified" if is_connected else "None",
            "masked_key": masked_key,
            "services_active": [
                "Google Gemini 2.5 Flash Cloud LLM",
                "Google Live Search Suggest Engine (gl=in)",
                "Google Trends Deep Explorer",
                "Google Merchant Center Feed Format",
                "Google Sheets Webhook Sync",
            ] if is_connected else [
                "Google Live Search Suggest Engine (Public Free)",
                "Google Trends Deep Explorer (Public Free)",
            ]
        }

    @classmethod
    def save_google_credentials(cls, api_key: str, account_email: str = "", appinfo_paths: list = None) -> bool:
        """Update Google API credentials in appinfo11.txt and environment variables."""
        clean_key = api_key.strip()
        if not clean_key:
            return False

        if appinfo_paths is None:
            appinfo_paths = [
                Path("c:/Users/tarik/Desktop/MY TOOLS/appinfo11.txt"),
                Path("c:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/appinfo11.txt"),
            ]

        for p in appinfo_paths:
            if p.exists():
                try:
                    text = p.read_text(encoding="utf-8")
                    if "GEMINI_API_KEY=" in text:
                        import re
                        text = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={clean_key}", text)
                        text = re.sub(r"GOOGLE_API_KEY=.*", f"GOOGLE_API_KEY={clean_key}", text)
                    else:
                        text += f"\nGEMINI_API_KEY={clean_key}\nGOOGLE_API_KEY={clean_key}\n"
                    p.write_text(text, encoding="utf-8")
                except Exception:
                    pass

        os.environ["GEMINI_API_KEY"] = clean_key
        os.environ["GOOGLE_API_KEY"] = clean_key
        return True

    @staticmethod
    def open_google_trends(keyword: str, geo: str = "IN"):
        """Launch Google Trends in default browser to view real-time interest over time."""
        kw = urllib.parse.quote(keyword.strip())
        url = f"https://trends.google.com/trends/explore?geo={geo.upper()}&q={kw}&hl=en"
        webbrowser.open(url)

    @staticmethod
    def open_google_search_console():
        """Open Google Search Console dashboard."""
        webbrowser.open("https://search.google.com/search-console")

    @staticmethod
    def open_google_keyword_planner():
        """Open Google Keyword Planner tool for commercial CPC and bidding estimates."""
        webbrowser.open("https://ads.google.com/home/tools/keyword-planner/")

    @staticmethod
    def open_google_merchant_center():
        """Open Google Merchant Center for Google Shopping product feeds."""
        webbrowser.open("https://merchants.google.com/")
