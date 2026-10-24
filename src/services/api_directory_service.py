"""
E-Commerce Public APIs, Forex, Logistics & Pipedream Integration Service.

Leverages:
1. Public APIs (public-apis/public-apis): Verified free financial & commerce APIs.
2. Public API Lists (public-api-lists/public-api-lists): Searchable API directory.
3. OpenAPI Directory (APIs-guru/openapi-directory): Machine-readable API inspection.
4. Free Public APIs (free-public-apis/apis): Alternative shopping, logistics & currency endpoints.
5. Pipedream (PipedreamHQ/pipedream): Webhook workflow integration for automated order & price sync.
"""

import json
import urllib.request
import urllib.parse
from decimal import Decimal
from typing import Dict, Any, List, Optional


class APIDirectoryService:
    """Service to query free public APIs, check forex, resolve pincodes, and trigger Pipedream webhooks."""

    # Curated directory of free e-commerce APIs from Public APIs & OpenAPI Directory
    CURATED_APIS = [
        {
            "name": "Open Exchange Rates (Free Endpoint)",
            "category": "Currency & Finance",
            "repo_source": "public-apis/public-apis",
            "auth": "None",
            "cors": "Yes",
            "url": "https://open.er-api.com/v6/latest/USD",
            "description": "Real-time foreign exchange rates for over 160 fiat currencies with USD base.",
        },
        {
            "name": "Frankfurter FX API",
            "category": "Currency & Finance",
            "repo_source": "free-public-apis/apis",
            "auth": "None",
            "cors": "Yes",
            "url": "https://api.frankfurter.app/latest",
            "description": "European Central Bank reference rates for tracking foreign exchange fluctuations.",
        },
        {
            "name": "India Postal Pincode Directory",
            "category": "Logistics & Shipping",
            "repo_source": "public-apis/public-apis",
            "auth": "None",
            "cors": "Yes",
            "url": "https://api.postalpincode.in/pincode/{PINCODE}",
            "description": "Resolves Indian 6-digit PIN codes to Post Office names, Districts, Divisions, and States.",
        },
        {
            "name": "Open Food & Product Facts",
            "category": "Products & Barcodes",
            "repo_source": "APIs-guru/openapi-directory",
            "auth": "None",
            "cors": "Yes",
            "url": "https://world.openfoodfacts.org/api/v2/product/{BARCODE}",
            "description": "Open collaborative database of barcodes (EAN/UPC/GTIN) with product metadata and categories.",
        },
        {
            "name": "Pipedream Webhook Event Ingestion",
            "category": "Workflow Automation",
            "repo_source": "PipedreamHQ/pipedream",
            "auth": "Webhook URL",
            "cors": "Yes",
            "url": "https://pipedream.com",
            "description": "Serverless event bus and webhook listener to route CommerceCalc calculations to Google Sheets, Slack, and Shopify.",
        },
        {
            "name": "GitHub Releases API (CommerceCalc Updater)",
            "category": "Developer & Updates",
            "repo_source": "APIs-guru/openapi-directory",
            "auth": "None",
            "cors": "Yes",
            "url": "https://api.github.com/repos/CommerceCalc/CommerceCalc/releases/latest",
            "description": "REST API for continuous software version checks, changelog retrieval, and release binary downloads.",
        },
        {
            "name": "FakeStoreAPI",
            "category": "E-Commerce Mock Data",
            "repo_source": "public-api-lists/public-api-lists",
            "auth": "None",
            "cors": "Yes",
            "url": "https://fakestoreapi.com/products",
            "description": "Free pseudo-real e-commerce JSON data for testing retail carts, product feeds, and pricing models.",
        },
        {
            "name": "CoinGecko Crypto Commerce Rates",
            "category": "Crypto Payments",
            "repo_source": "public-apis/public-apis",
            "auth": "None",
            "cors": "Yes",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether&vs_currencies=inr,usd",
            "description": "Live cryptocurrency conversion rates for stores accepting Web3 or USDT checkout.",
        },
    ]

    @staticmethod
    def fetch_live_forex_rates(base_currency: str = "USD") -> Dict[str, Any]:
        """Fetch live currency exchange rates from open.er-api.com (Public APIs cataloged)."""
        base = base_currency.upper().strip() or "USD"
        url = f"https://open.er-api.com/v6/latest/{base}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "CommerceCalc-Desktop/1.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    rates = data.get("rates", {})
                    inr_rate = rates.get("INR", 0)
                    return {
                        "success": True,
                        "base": base,
                        "rates": rates,
                        "inr_rate": float(inr_rate),
                        "last_update": data.get("time_last_update_utc", "Recent"),
                        "source": "Open Exchange Rates (Public APIs)",
                    }
        except Exception as e:
            # Fallback to Frankfurter if USD/EUR
            try:
                alt_url = f"https://api.frankfurter.app/latest?from={base}"
                req = urllib.request.Request(alt_url, headers={"User-Agent": "CommerceCalc-Desktop/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    rates = data.get("rates", {})
                    return {
                        "success": True,
                        "base": base,
                        "rates": rates,
                        "inr_rate": float(rates.get("INR", 0)),
                        "last_update": data.get("date", "Recent"),
                        "source": "Frankfurter (Public APIs)",
                    }
            except Exception as e2:
                return {
                    "success": False,
                    "error": f"Primary API: {str(e)} | Secondary API: {str(e2)}",
                    "inr_rate": 83.50 if base == "USD" else 90.00,  # safe fallback estimate
                    "source": "Offline Fallback",
                }

    @staticmethod
    def lookup_pincode_zone(pincode: str) -> Dict[str, Any]:
        """Query Indian postal API to verify PIN code and resolve State, District & Zone classification."""
        clean_pin = "".join(filter(str.isdigit, pincode.strip()))
        if len(clean_pin) != 6:
            return {
                "success": False,
                "error": "Indian PIN codes must be exactly 6 digits.",
            }

        url = f"https://api.postalpincode.in/pincode/{clean_pin}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "CommerceCalc-Desktop/1.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.loads(response.read().decode("utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    status = data[0].get("Status")
                    if status == "Success":
                        post_offices = data[0].get("PostOffice", [])
                        if post_offices:
                            po = post_offices[0]
                            district = po.get("District", "")
                            state = po.get("State", "")
                            name = po.get("Name", "")
                            
                            # Determine tier based on metro districts
                            metros = {
                                "MUMBAI", "DELHI", "BANGALORE", "BENGALURU", "CHENNAI", 
                                "KOLKATA", "HYDERABAD", "AHMEDABAD", "PUNE", "GURGAON", 
                                "GURUGRAM", "NOIDA", "THANE", "FARIDABAD"
                            }
                            is_metro = district.upper() in metros or state.upper() in {"DELHI", "CHANDIGARH"}
                            zone_tier = "Metro (Tier 1)" if is_metro else "Non-Metro (Tier 2/3)"

                            return {
                                "success": True,
                                "pincode": clean_pin,
                                "post_office": name,
                                "district": district,
                                "state": state,
                                "is_metro": is_metro,
                                "zone_tier": zone_tier,
                                "source": "India Post Directory (Public APIs)",
                            }
                    return {
                        "success": False,
                        "error": data[0].get("Message", "Pincode not found in official registry."),
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to contact postal directory: {str(e)}",
            }
        return {"success": False, "error": "Unknown postal lookup response."}

    @staticmethod
    def send_to_pipedream(webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch financial calculation payload to Pipedream webhook for automation workflows."""
        if not webhook_url or not webhook_url.startswith("http"):
            return {
                "success": False,
                "error": "Please provide a valid Pipedream HTTP endpoint (e.g. https://eo...pipedream.net)",
            }

        try:
            body = json.dumps(payload, default=str).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CommerceCalc-Desktop/1.0",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=7) as res:
                return {
                    "success": True,
                    "status_code": res.status,
                    "message": f"Successfully delivered payload to Pipedream webhook ({res.status} OK)",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Pipedream webhook dispatch failed: {str(e)}",
            }

    @classmethod
    def get_curated_apis(cls) -> List[Dict[str, str]]:
        """Return the curated list of free public e-commerce APIs."""
        return cls.CURATED_APIS
