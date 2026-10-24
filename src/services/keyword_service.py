"""
Comprehensive E-Commerce SEO, Keyword Intelligence & Listing Optimization Suite.

Features:
1. Multi-Platform Search Query Engine (Google India, Amazon Buyers, Flipkart, Wholesale).
2. Intent, Volume Index, CPC (INR), and Keyword Difficulty (KD%) heuristics.
3. Amazon 249-Byte Backend Search Terms Formatter (De-duplication, punctuation removal, byte counter).
4. Negative Keyword Generator for Amazon PPC and Google Ads.
5. Live Keyword Density and On-Page SEO Analyzer.
6. Cloud AI Listing & PPC Strategy Copilot (Gemini 2.5 Flash / Groq).
"""

import urllib.request
import urllib.parse
import json
import re
from typing import List, Dict, Any, Optional
from .ai_service import CommerceCalcAI


class GoogleKeywordResearchService:
    """Full-featured e-commerce keyword research and SEO optimization engine."""

    GOOGLE_MODIFIERS = [
        "",  # Direct
        "for men",
        "for women",
        "best",
        "buy online",
        "price in india",
        "under 500",
        "under 1000",
        "under 2000",
        "combo pack",
        "review",
        "top brands",
    ]

    AMAZON_MODIFIERS = [
        "amazon",
        "amazon india",
        "amazon price",
        "amazon prime",
        "amazon best seller",
        "online shopping amazon",
    ]

    FLIPKART_MODIFIERS = [
        "flipkart",
        "flipkart price",
        "flipkart offer",
        "flipkart sale",
    ]

    WHOLESALE_MODIFIERS = [
        "wholesale",
        "wholesale market india",
        "manufacturer india",
        "bulk supplier",
    ]

    ALPHABET = [chr(i) for i in range(ord('a'), ord('z') + 1)]

    # Standard Amazon stop words and punctuation
    AMAZON_STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "in", "is", "it", "its", "of", "on", "that", "the", "to",
        "was", "were", "will", "with"
    }

    NEGATIVE_PRESETS = [
        "free", "crack", "torrent", "download", "pdf", "diy", "repair",
        "tutorial", "jobs", "salary", "second hand", "used", "fake", "replica",
        "first copy", "manual", "wiki", "code", "open source"
    ]

    @classmethod
    def fetch_google_suggestions(
        cls,
        seed_query: str,
        country: str = "in",
        language: str = "en",
        channel_filter: str = "All Channels",
        deep_scan: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query live Google autocomplete index across consumer, Amazon, Flipkart, and Wholesale modifiers.
        """
        seed = seed_query.strip()
        if not seed:
            return []

        queries_to_run = []

        if channel_filter in ("All Channels", "Google India (gl=in)", "General Consumer"):
            queries_to_run.extend([f"{seed} {mod}".strip() for mod in cls.GOOGLE_MODIFIERS])

        if channel_filter in ("All Channels", "Amazon India Buyers"):
            queries_to_run.extend([f"{seed} {mod}".strip() for mod in cls.AMAZON_MODIFIERS])

        if channel_filter in ("All Channels", "Flipkart Buyers"):
            queries_to_run.extend([f"{seed} {mod}".strip() for mod in cls.FLIPKART_MODIFIERS])

        if channel_filter in ("All Channels", "Wholesale & B2B"):
            queries_to_run.extend([f"{seed} {mod}".strip() for mod in cls.WHOLESALE_MODIFIERS])

        if deep_scan:
            # A-Z deep expansion
            for letter in cls.ALPHABET[:12]:
                queries_to_run.append(f"{seed} {letter}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

        discovered = {}

        for q in queries_to_run:
            encoded = urllib.parse.quote(q)
            url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={encoded}&hl={language}&gl={country}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=3.5) as res:
                    if res.status == 200:
                        data = json.loads(res.read().decode("utf-8"))
                        if len(data) > 1 and isinstance(data[1], list):
                            for rank_idx, suggestion in enumerate(data[1]):
                                clean_kw = suggestion.strip().lower()
                                if clean_kw and clean_kw not in discovered:
                                    metrics = cls._calculate_keyword_metrics(clean_kw, rank_idx, q)
                                    discovered[clean_kw] = metrics
            except Exception:
                continue

        return list(discovered.values())

    @classmethod
    def _calculate_keyword_metrics(cls, kw: str, rank_idx: int, seed_phrase: str) -> Dict[str, Any]:
        """Compute estimated volume, CPC, KD%, and intent tags based on market heuristics."""
        words = kw.split()
        word_count = len(words)

        # Detect channel
        channel = "Google Web"
        if "amazon" in kw:
            channel = "Amazon India"
        elif "flipkart" in kw:
            channel = "Flipkart"
        elif any(w in kw for w in ["wholesale", "manufacturer", "supplier", "bulk"]):
            channel = "B2B / Wholesale"

        # Detect search intent
        if any(w in kw for w in ["buy", "order", "price", "under", "shop", "cost", "combo", "sale"]):
            intent = "Transactional (Buyer Intent)"
            base_cpc = 28.0
            base_kd = 62
        elif any(w in kw for w in ["best", "top", "review", "vs", "compare"]):
            intent = "Commercial (Product Evaluation)"
            base_cpc = 22.0
            base_kd = 54
        elif channel in ("Amazon India", "Flipkart"):
            intent = "Marketplace Search"
            base_cpc = 32.0
            base_kd = 68
        elif channel == "B2B / Wholesale":
            intent = "B2B Sourcing"
            base_cpc = 45.0
            base_kd = 48
        else:
            intent = "Informational / Research"
            base_cpc = 14.0
            base_kd = 38

        # Long-tail keywords have lower difficulty and higher conversion
        if word_count >= 4:
            base_kd = max(15, base_kd - 18)
            est_vol = "Medium (1k - 10k/mo)" if rank_idx < 3 else "Long-Tail (100 - 1k/mo)"
            vol_index = 65 if rank_idx < 3 else 42
        elif word_count == 3:
            est_vol = "High (10k - 50k/mo)" if rank_idx < 3 else "Medium (1k - 10k/mo)"
            vol_index = 85 if rank_idx < 3 else 68
        else:
            base_kd = min(92, base_kd + 22)
            est_vol = "Very High (50k+/mo)" if rank_idx < 2 else "High (10k - 50k/mo)"
            vol_index = 95 if rank_idx < 2 else 80

        # Position ranking tier
        if rank_idx < 3:
            tier = "Top 1-3 (High Demand)"
        elif rank_idx < 6:
            tier = "Top 4-6 (Moderate)"
        else:
            tier = "Long-Tail (Niche)"

        est_cpc = round(base_cpc + (10 - min(rank_idx, 9)) * 1.5, 2)

        return {
            "keyword": kw,
            "channel": channel,
            "intent": intent,
            "vol_index": vol_index,
            "est_volume": est_vol,
            "est_cpc": f"₹{est_cpc:.2f}",
            "kd_pct": f"{base_kd}%",
            "ranking_tier": tier,
            "seed": seed_phrase,
            "source": "Google Live Autocomplete",
        }

    @classmethod
    def optimize_amazon_backend_search_terms(cls, raw_text: str) -> Dict[str, Any]:
        """
        Amazon strictly limits Generic Keywords / Backend Search Terms to 249 UTF-8 bytes.
        Rules:
        - No commas or punctuation.
        - No duplicate words.
        - Space-separated only.
        - Exclude Amazon stop words.
        - Strict cut-off at or under 249 bytes without breaking whole words.
        """
        # 1. Clean punctuation and convert to lowercase
        cleaned = re.sub(r"[^\w\s]", " ", raw_text.lower())
        raw_words = cleaned.split()

        # 2. De-duplicate preserving order and remove stop words
        unique_words = []
        seen = set()
        for w in raw_words:
            w_strip = w.strip()
            if not w_strip or w_strip in seen:
                continue
            if w_strip in cls.AMAZON_STOP_WORDS:
                continue
            seen.add(w_strip)
            unique_words.append(w_strip)

        # 3. Build string within 249 UTF-8 bytes boundary
        final_words = []
        current_bytes = 0

        for w in unique_words:
            word_bytes = len(w.encode("utf-8"))
            extra_bytes = (1 if final_words else 0) + word_bytes  # space separator

            if current_bytes + extra_bytes <= 249:
                final_words.append(w)
                current_bytes += extra_bytes
            else:
                break

        final_str = " ".join(final_words)
        total_bytes = len(final_str.encode("utf-8"))

        return {
            "clean_terms": final_str,
            "byte_count": total_bytes,
            "max_bytes": 249,
            "is_safe": total_bytes <= 249,
            "word_count": len(final_words),
            "removed_duplicates": len(raw_words) - len(unique_words),
        }

    @classmethod
    def generate_negative_keywords(cls, seed: str, candidate_queries: List[str] = None) -> Dict[str, List[str]]:
        """
        Builds negative keyword lists to safeguard Amazon Sponsored Products and Google Ads PPC budgets.
        """
        neg_exact = []
        neg_phrase = list(cls.NEGATIVE_PRESETS)

        clean_seed = seed.strip().lower()
        if clean_seed:
            for term in ["free", "cheap", "repair", "pdf", "used", "diy", "second hand"]:
                neg_exact.append(f"{clean_seed} {term}")
                neg_exact.append(f"{term} {clean_seed}")

        # Scan candidate queries for low-intent words
        if candidate_queries:
            for q in candidate_queries:
                q_low = q.lower()
                for bad in cls.NEGATIVE_PRESETS:
                    if bad in q_low and q_low not in neg_exact:
                        neg_exact.append(q_low)

        return {
            "negative_phrase": sorted(list(set(neg_phrase))),
            "negative_exact": sorted(list(set(neg_exact)))[:50],
        }

    @classmethod
    def analyze_keyword_density(cls, text: str, focus_keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze keyword presence and density percentage in product titles, bullet points, or descriptions.
        """
        clean_text = text.lower()
        words = re.findall(r"\b\w+\b", clean_text)
        total_words = max(len(words), 1)

        results = []
        for kw in focus_keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue

            # Count occurrences of phrase
            occurrences = len(re.findall(r"\b" + re.escape(kw_clean) + r"\b", clean_text))
            kw_words = len(kw_clean.split())
            density = round((occurrences * kw_words / total_words) * 100, 2)

            if density == 0:
                status = "Missing (Add to listing)"
            elif 1.0 <= density <= 3.5:
                status = "Optimal (1% - 3.5%)"
            elif density < 1.0:
                status = "Low (<1%)"
            else:
                status = "Over-optimized / Warning (>3.5%)"

            results.append({
                "keyword": kw_clean,
                "count": occurrences,
                "density_pct": f"{density}%",
                "status": status,
            })

        return results

    @classmethod
    def generate_seo_strategy_with_ai(
        cls,
        seed_query: str,
        discovered_keywords: List[str],
        channel: str = "Amazon India"
    ) -> str:
        """
        Use Google Gemini 2.5 Flash to generate a complete, high-converting listing and PPC structure.
        """
        ai = CommerceCalcAI()
        top_kws = discovered_keywords[:25]
        kw_list_str = "\n".join([f"- {k}" for k in top_kws])

        system_prompt = (
            f"You are the Lead E-Commerce SEO Director & Amazon PPC Architect for {channel}. "
            "Using the provided seed keyword and verified high-ranking search terms, build a production-ready listing copy:\n"
            "1. OPTIMIZED PRODUCT TITLE: 150-180 characters, keyword-dense, including Brand, Seed, Material/Spec, and key benefit.\n"
            "2. 5 HIGH-CONVERTING BULLET POINTS: Each starting with a bold benefit in [CAPS], integrating secondary high-volume keywords naturally.\n"
            "3. BACKEND SEARCH TERMS (EXACTLY UNDER 249 BYTES): Deduplicated, space-separated, no punctuation.\n"
            "4. TARGETED PPC CAMPAIGN ROADMAP: Group keywords into: Exact Match (High Intent), Phrase Match (Category), and Broad Match (Discovery).\n"
            "5. COMPETITOR DEFENSE STRATEGY: Key differentiation points to win the Buy Box against undercutters."
        )

        user_prompt = (
            f"Product Niche / Seed: {seed_query}\n"
            f"Target Channel: {channel}\n"
            f"Verified High-Rank Keywords Found:\n{kw_list_str}\n"
        )

        return ai.generate_response(system_prompt, user_prompt)
