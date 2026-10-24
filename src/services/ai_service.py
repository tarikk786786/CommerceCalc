"""
Universal AI & LLM Service Engine for CommerceCalc.

Integrates:
- Google Gemini (gemini-2.5-flash, gemini-1.5-flash) via google.genai
- Groq Cloud (llama-3.1-8b-instant, etc.)
- OpenRouter / Custom OpenAI-compatible endpoints

Reads credentials securely from appinfo11.txt and environment variables.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal


def get_api_key(key_name: str) -> str:
    """Fetch API key from environment, appinfo11.txt, or workspace root."""
    # 1. Environment variable
    val = os.environ.get(key_name, "").strip()
    if val:
        return val

    # 2. Check local appinfo11.txt or root appinfo11.txt
    paths_to_check = [
        Path("appinfo11.txt"),
        Path("../appinfo11.txt"),
        Path("../../appinfo11.txt"),
        Path("c:/Users/tarik/Desktop/MY TOOLS/appinfo11.txt"),
        Path("c:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/appinfo11.txt"),
    ]
    for p in paths_to_check:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.startswith(f"{key_name}="):
                        val = line.split("=", 1)[1].strip()
                        if val:
                            return val
            except Exception:
                pass
    return ""


class CommerceCalcAI:
    """Universal AI intelligence provider for CommerceCalc."""

    def __init__(self, provider: str = "gemini", model_name: str = "gemini-2.5-flash"):
        self.provider = provider
        self.model_name = model_name
        self.gemini_key = get_api_key("GEMINI_API_KEY") or get_api_key("GOOGLE_API_KEY")
        self.groq_key = get_api_key("GROQ_API_KEY")
        self.openrouter_key = get_api_key("OPENROUTER_API_KEY")

    def is_configured(self) -> bool:
        """Check if at least one valid cloud AI provider has an API key."""
        return bool(self.gemini_key or self.groq_key or self.openrouter_key)

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using available LLM with automatic fallback."""
        errors = []

        # 1. Primary: Google Gemini 2.5 Flash
        if self.gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                full_prompt = f"{system_prompt}\n\nUser Request:\n{user_prompt}"
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                )
                if res.text:
                    return res.text.strip()
            except Exception as e:
                errors.append(f"Gemini: {str(e)}")

        # 2. Fallback: Groq Cloud
        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                chat = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.2,
                )
                if chat.choices and chat.choices[0].message.content:
                    return chat.choices[0].message.content.strip()
            except Exception as e:
                errors.append(f"Groq: {str(e)}")

        # 3. Fallback: OpenRouter
        if self.openrouter_key:
            try:
                from openai import OpenAI
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.openrouter_key)
                chat = client.chat.completions.create(
                    model="meta-llama/llama-3.1-8b-instruct:free",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1500,
                )
                if chat.choices and chat.choices[0].message.content:
                    return chat.choices[0].message.content.strip()
            except Exception as e:
                errors.append(f"OpenRouter: {str(e)}")

        raise RuntimeError(f"All AI LLM providers failed. Diagnostic logs:\n" + "\n".join(errors))

    def analyze_product_profitability(self, product_data: Dict[str, Any]) -> str:
        """AI financial diagnosis of a product's economics."""
        system_prompt = (
            "You are CommerceCalc AI, an elite e-commerce financial analyst, Amazon/Flipkart "
            "marketplace operations director, and Indian GST tax strategist. "
            "Analyze the product financial breakdown provided by the user. "
            "Provide: 1) Executive Verdict (Health score 1-10 & status), "
            "2) Critical Margin Bottlenecks (Logistics % vs Platform fees vs Ads), "
            "3) Actionable Pricing & Profit Maximization Tactics (e.g. bundling, courier weight optimization, RTO buffer), "
            "and 4) Indian GST/ITC compliance advice. Keep it concise, structured with Markdown headers and bullet points."
        )
        user_prompt = (
            f"Product Name: {product_data.get('product_name', 'Unnamed Product')}\n"
            f"Channel: {product_data.get('channel', 'General')}\n"
            f"Selling Price: ₹{product_data.get('selling_price', '0')}\n"
            f"Purchase Cost: ₹{product_data.get('purchase_cost', '0')}\n"
            f"Net Taxable Revenue: ₹{product_data.get('net_revenue', '0')}\n"
            f"Fulfillment / Courier: ₹{product_data.get('fulfillment_cost', '0')}\n"
            f"Marketplace Fees: ₹{product_data.get('marketplace_fees', '0')}\n"
            f"Advertising (CAC): ₹{product_data.get('advertising', '0')}\n"
            f"Expected Return/RTO Loss: ₹{product_data.get('return_loss', '0')}\n"
            f"Net Operating Profit: ₹{product_data.get('net_profit', '0')}\n"
            f"Contribution Margin: {product_data.get('margin_pct', '0')}%\n"
            f"Markup on Cost: {product_data.get('markup_pct', '0')}%\n"
            f"GST Rate: {product_data.get('gst_rate', '0')}%\n"
        )
        return self.generate_response(system_prompt, user_prompt)

    def classify_product_and_fees(self, product_title_or_desc: str) -> str:
        """AI Category, HSN Code, GST Slab, and Marketplace Fee Predictor."""
        system_prompt = (
            "You are CommerceCalc AI Indian E-Commerce Category & Tax Classifier. "
            "Given a product title or description, identify: "
            "1) Standard Indian HSN Code (4 to 8 digits), "
            "2) Applicable Indian GST Slab (0%, 5%, 12%, 18%, or 28%) with official rationale, "
            "3) Amazon India & Flipkart Category Classification, "
            "4) Estimated Marketplace Referral Commission Range (%) for this category in India, "
            "5) Typical Return & RTO risk level (Low, Medium, High). "
            "Format cleanly with bullet points and bold headers."
        )
        return self.generate_response(system_prompt, f"Classify this product:\n{product_title_or_desc}")

    def optimize_advertising_roas(self, campaign_data: Dict[str, Any]) -> str:
        """AI Marketing Funnel & ROAS Optimization Copilot."""
        system_prompt = (
            "You are CommerceCalc AI Performance Marketing Director (Meta Ads, Google Ads, Amazon Sponsored Products). "
            "Analyze the advertising metrics provided. Diagnose if poor ROAS stems from: "
            "ad creative fatigue (low CTR), high bidding costs (high CPC), low conversion rate (weak landing page / uncompetitive price), "
            "or low product margins. Give 3 specific numerical recommendations: Maximum safe CPC bid, Target ROAS, and budget shift."
        )
        user_prompt = (
            f"Ad Spend: ₹{campaign_data.get('ad_spend', '0')}\n"
            f"Impressions: {campaign_data.get('impressions', '0')}\n"
            f"Clicks: {campaign_data.get('clicks', '0')}\n"
            f"CTR: {campaign_data.get('ctr', '0')}%\n"
            f"CPC: ₹{campaign_data.get('cpc', '0')}\n"
            f"Orders: {campaign_data.get('orders', '0')}\n"
            f"Conversion Rate: {campaign_data.get('cvr', '0')}%\n"
            f"Attributed Revenue: ₹{campaign_data.get('attributed_revenue', '0')}\n"
            f"Current ROAS: {campaign_data.get('roas', '0')}x\n"
            f"Break-Even ROAS: {campaign_data.get('be_roas', '0')}x\n"
            f"Contribution Margin (Before Ads): {campaign_data.get('margin_before_ads', '0')}%\n"
        )
        return self.generate_response(system_prompt, user_prompt)

    def audit_bulk_portfolio(self, summary_data: Dict[str, Any]) -> str:
        """Executive portfolio review of bulk imported spreadsheet."""
        system_prompt = (
            "You are CommerceCalc AI Portfolio Director. Provide an executive summary of the bulk spreadsheet calculation results. "
            "Highlight: 1) Overall Portfolio Health & Win-Rate, 2) Critical warning about loss-making SKUs, "
            "3) Strategic recommendations for bundling or re-negotiating supplier costs, and 4) Top 3 immediate actions."
        )
        user_prompt = (
            f"Total SKUs Imported: {summary_data.get('total_rows', 0)}\n"
            f"Profitable SKUs: {summary_data.get('profitable_rows', 0)}\n"
            f"Loss-Making SKUs: {summary_data.get('loss_rows', 0)}\n"
            f"Total Batch Net Profit: ₹{summary_data.get('total_profit', '0')}\n"
            f"Average Contribution Margin: {summary_data.get('avg_margin', '0')}%\n"
            f"Loss Leader Examples: {summary_data.get('loss_examples', 'None')}\n"
        )
        return self.generate_response(system_prompt, user_prompt)

    def simulate_competitor_price_war(self, base_data: Dict[str, Any]) -> str:
        """Simulate defensive pricing strategies against marketplace undercutters."""
        system_prompt = (
            "You are CommerceCalc AI Game-Theoretic Pricing Strategist. "
            "The user sells an e-commerce product and faces aggressive competitor price-slashing on Amazon/Flipkart. "
            "Analyze their cost floor and break-even limit. "
            "Advise: 1) Maximum defensive price match before burning capital, "
            "2) Non-price counter-strategies (Value-add bundles, faster dispatch, prime badge, customer reviews), "
            "and 3) When to hold price vs when to discount."
        )
        user_prompt = (
            f"Current Retail Price: ₹{base_data.get('selling_price', '0')}\n"
            f"Product Cost: ₹{base_data.get('purchase_cost', '0')}\n"
            f"Courier + Marketplace Fees: ₹{base_data.get('fixed_fees', '0')}\n"
            f"Current Net Profit: ₹{base_data.get('net_profit', '0')}\n"
            f"Break-Even Price Floor: ₹{base_data.get('breakeven_price', '0')}\n"
            f"Competitor Discount Rumor: {base_data.get('competitor_discount', '15% lower')}\n"
        )
        return self.generate_response(system_prompt, user_prompt)


# Backward and forward compatibility alias
AIService = CommerceCalcAI
