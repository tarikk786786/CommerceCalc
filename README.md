# CommerceCalc — All-in-One E-Commerce Profit & Pricing Suite

**CommerceCalc** is a professional, human-designed Windows desktop application, offline-first financial engine, and cloud AI copilot built for Indian and international e-commerce sellers, dropshippers, D2C brands, Amazon/Flipkart/Meesho sellers, digital creators, and wholesalers.

---

## Key Capabilities

1. **Precision Decimal Arithmetic**: Built exclusively with Python's `decimal.Decimal` to guarantee 100% mathematical accuracy and eliminate binary floating-point drift.
2. **Indian GST & Tax Engine**: Complete support for GST-inclusive and GST-exclusive pricing, CGST/SGST/IGST breakdown, Input Tax Credit (ITC) eligibility, Section 52 TCS, and Section 194-O TDS.
3. **Target Price & Margin Solver**: Backward-solves the exact customer-facing price required to reach any target profit, margin, or markup—simultaneously solving circular percentage marketplace fees and taxes.
4. **AI Strategic Copilot (Active Cloud LLM)**: Powered by Google Gemini 2.5 Flash (`google.genai`) with Groq (`llama-3.1-8b-instant`) fallback. Provides real-time financial audits, HSN code & GST classification, competitor price war game-theory simulations, and RTO risk reduction playbooks.
5. **Free Public APIs & Automation Hub**: Integrates verified free public endpoints from:
   - `public-apis/public-apis` & `free-public-apis/apis`: Live real-time currency exchange rates (USD, EUR, GBP, AED, CNY, JPY to INR) and India Post PIN code logistics zone verification.
   - `public-api-lists/public-api-lists` & `APIs-guru/openapi-directory`: Curated e-commerce API directory and machine-readable API inspection.
   - `PipedreamHQ/pipedream`: One-click payload webhook dispatch connecting calculations to Google Sheets, Slack, Shopify, and Zapier.
6. **Google High-Rank Keyword Finder & SEO Suite**: Real-time buyer query discovery via Google Autocomplete live index (`suggestqueries.google.com`), deep A-Z alphabet scanning, and Gemini 2.5 Flash listing copy and PPC strategy generation.
7. **Google Account & Cloud Services Linking**: Direct linking manager for Google AI Studio credentials, Google Trends explorer, Google Search Console, Google Keyword Planner, and Google Merchant Center.
8. **Future Updates & Maintenance**: Built-in update checker verifying remote releases via GitHub Releases API or version manifests, complete with changelogs and channel switching (Stable/Beta).
9. **Offline-First Resilience**: All core financial calculations, scenario saving, and catalog lookups run locally with zero latency in SQLite (`~/.commercecalc/commercecalc.db`).
10. **High-Throughput Bulk Spreadsheet Engine**: Batch audits hundreds of SKUs from CSV or Excel files with auto-validation and export.

---

## 24 Complete Functional Application Pages

| # | Page Name | Category | Description |
|---|---|---|---|
| 1 | **Dashboard** | Overview | Financial summary, portfolio health, margin distributions & quick actions |
| 2 | **AI Strategic Copilot** | Overview | Conversational financial CFO, HSN/GST finder, price war simulator & RTO playbook |
| 3 | **Profit Calculator** | Calculators | Comprehensive product-level contribution accounting with AI audit button |
| 4 | **Target Pricing** | Calculators | Reverse-solves required retail price from desired profit, margin, or markup |
| 5 | **GST & Tax Breakdown** | Calculators | CGST/SGST/IGST breakdown, reverse GST calculation & net tax liability |
| 6 | **Advertising & ROAS** | Calculators | CAC, CPC, CPM, break-even ROAS ($1/\text{margin}$), ACoS, TACoS & AI diagnostic |
| 7 | **Shipping & Logistics** | Calculators | Volumetric weight ($\frac{L \times W \times H}{5000}$), courier slabs & postal zone check |
| 8 | **Returns & RTO Loss** | Calculators | Probabilistic doorstep RTO vs customer return loss modeling |
| 9 | **Discount & Promo** | Calculators | BOGO, percentage discounts, coupons & volume break-even requirements |
| 10 | **Bundle Calculator** | Calculators | Multi-SKU bundling with cost/quantity/price share allocation |
| 11 | **Dropshipping** | Calculators | Live foreign exchange conversion, bank spreads & COD delivery risk |
| 12 | **Digital Products** | Calculators | Upfront creation amortization & zero-marginal-cost software/ebook delivery |
| 13 | **Inventory & Reorder** | Business Ops | Reorder point (ROP), lead time demand, safety stock, EOQ & GMROI |
| 14 | **Landed Cost** | Business Ops | Customs CIF assessable value, BCD, SWS, Import IGST & total landed cost |
| 15 | **Cash Flow & Settlement** | Business Ops | Payout reconciliation, 18% GST on fees, 1% GST TCS (Sec 52), 0.1% TDS (Sec 194-O) |
| 16 | **Bulk Calculator** | Business Ops | CSV/Excel high-throughput batch audit with AI portfolio review |
| 17 | **Public APIs & Pipedream** | Business Ops | Live forex rates, PIN code zone resolver & Pipedream webhook workflows |
| 18 | **Product Catalog** | Management | Local database product catalog with search, filter, and quick calculation |
| 19 | **Fee Profiles** | Management | Configurable fee profiles for Amazon India, Flipkart, Meesho, Shopify, D2C |
| 20 | **Saved Scenarios** | Management | Save and compare pricing scenarios and cost permutations side by side |
| 21 | **Reports & Exports** | Management | Export P&L statements, SKU summaries, and audit reports to CSV and JSON |
| 22 | **Software Updates** | Management | GitHub release checking, version info (v1.0.0), changelog & release channels |
| 23 | **Settings** | Management | Regional preferences, default currency (INR), tax defaults & Google Linking |
| 24 | **Help & Reference** | Management | Financial formula reference, glossary, and data source documentation |
| 25 | **Keyword & SEO Suite** | Calculators | Multi-channel queries (Google, Amazon, Flipkart), SERP preview, Amazon 249-byte terms, Negative keywords, Density & AI Copilot |

---

## Architecture & Directory Layout

```
apps/CommerceCalc/
├── assets/
│   └── app.ico                       # High-resolution 256x256 application icon
├── data/                             # Sample templates and test datasets
│   ├── sample_products.csv           # Representative test products
│   └── sample_products_template.xlsx # Styled Excel import template
├── src/
│   ├── core/                         # Pure financial calculation engine
│   │   ├── money.py                  # Decimal-safe arithmetic, rounding, formatting
│   │   ├── tax.py                    # Indian GST calculation (CGST/SGST/IGST, ITC)
│   │   ├── profit.py                 # Core contribution profit & operating margin model
│   │   ├── pricing.py                # Target selling price mathematical solver
│   │   ├── fees.py                   # Marketplace fee profiles & rules engine
│   │   ├── shipping.py               # Volumetric weight & logistics calculator
│   │   ├── returns.py                # Expected return and RTO loss model
│   │   ├── advertising.py            # CAC, ROAS, ACoS, TACoS & ad break-even
│   │   ├── discounts.py              # Promotion & coupon volume break-even
│   │   ├── bundles.py                # Multi-SKU bundle cost allocation
│   │   ├── dropshipping.py           # Forex, supplier shipping & COD risk
│   │   ├── digital.py                # Content amortization & digital goods
│   │   ├── inventory.py              # Safety stock, ROP, EOQ, GMROI
│   │   ├── landed_cost.py            # Customs BCD, SWS, IGST & CIF landed cost
│   │   └── settlement.py             # TCS, TDS, marketplace deductions & payout
│   ├── db/                           # Persistence layer
│   │   ├── models.py                 # SQLAlchemy relational schema
│   │   └── database.py               # SQLite session factory, migrations & backups
│   ├── services/                     # Business services
│   │   ├── ai_service.py             # Google Gemini 2.5 Flash / Groq LLM engine
│   │   ├── api_directory_service.py  # Public APIs, live forex & Pipedream webhooks
│   │   ├── updater.py                # Release checker & future update service
│   │   └── bulk_import.py            # High-performance CSV & XLSX bulk processor
│   └── ui/                           # Desktop interface
│       ├── styles.py                 # Dark & Light professional theme stylesheets
│       ├── widgets/
│       │   ├── common.py             # MetricCards, FormFieldRows, MoneyInputs
│       │   └── ai_dialog.py          # Asynchronous non-blocking AI audit modal
│       ├── pages/                    # 24 Fully implemented pages
│       └── main_window.py            # Main application shell & sidebar router
├── tests/                            # Automated test suite (92 passing tests)
│   ├── test_core.py                  # Money, GST, Profit, Pricing, Shipping, Returns, Ads
│   ├── test_extended_calculators.py  # Discounts, Bundles, Dropship, Digital, Inventory, etc.
│   ├── test_bulk_import.py           # CSV and XLSX batch import/export tests
│   └── test_services.py              # AI, Updater, Forex, PIN code & Public API tests
├── main.py                           # Application startup entry point
├── pyproject.toml                    # Modern Python package configuration
├── requirements.txt                  # Python dependencies
├── appinfo11.txt                     # Configuration & API credentials record
└── Run-CommerceCalc.bat              # One-click Windows launch script
```

---

## Quick Start & Execution

### 1. Launch via Desktop Shortcut
Double-click the **CommerceCalc** shortcut located on your Windows Desktop (`C:\Users\tarik\Desktop\CommerceCalc.lnk`).

### 2. Launch via Batch File
Double-click `Run-CommerceCalc.bat` in either:
- Root workspace: `c:\Users\tarik\Desktop\MY TOOLS\Run-CommerceCalc.bat`
- Project folder: `c:\Users\tarik\Desktop\MY TOOLS\apps\CommerceCalc\Run-CommerceCalc.bat`

### 3. Launch via Command Line
```cmd
cd "c:\Users\tarik\Desktop\MY TOOLS\apps\CommerceCalc"
python main.py
```

### 4. Run the Test Suite
```cmd
pytest -v
```
*(All 92 unit and integration tests execute and pass in under 3 seconds)*
