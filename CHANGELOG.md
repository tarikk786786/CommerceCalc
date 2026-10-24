# Changelog

All notable changes to **CommerceCalc** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-23

### Added
- **Decimal Monetary Engine (`src/core/money.py`)**: Complete decimal-safe arithmetic supporting INR quantizing, rounding modes (nearest, round up, end in ₹9, ₹49, ₹99), and margin/markup separation.
- **Indian GST Engine (`src/core/tax.py`)**: Full support for tax-inclusive and tax-exclusive pricing, CGST/SGST/IGST breakdown, Input Tax Credit (ITC) tracking, and CBIC preset rates.
- **Universal Product Profit Calculator (`src/core/profit.py`, `src/ui/pages/profit_calc.py`)**: Multi-layer contribution accounting (Acquisition -> Fulfillment -> Platform -> Ads -> Overhead -> Operating Profit).
- **Target Selling Price Solver (`src/core/pricing.py`, `src/ui/pages/target_price.py`)**: Mathematical solver determining required customer price for target profit/margin under circular fees.
- **Advertising & ROAS Suite (`src/core/advertising.py`, `src/ui/pages/advertising_calc.py`)**: CPA, CAC, ROAS, break-even ROAS, ACoS, TACoS, and max allowable CAC.
- **Logistics & Dimensional Weight (`src/core/shipping.py`)**: Volumetric weight, chargeable weight slabs, courier rate-card calculations.
- **Returns & RTO Risk Calculator (`src/core/returns.py`)**: Probabilistic loss modeling for COD vs prepaid returns, damaged goods, and salvage value.
- **Promotion & Discount Engine (`src/core/discounts.py`)**: BOGO, percentage, coupon discounts, seller vs marketplace funding, volume compensation.
- **Multi-SKU Bundle Calculator (`src/core/bundles.py`)**: Cost share, quantity share, and price share allocation for bundles.
- **Dropshipping Financials (`src/core/dropshipping.py`)**: Foreign supplier landed costs, currency conversion markup, COD RTO loss mitigation.
- **Digital Products Suite (`src/core/digital.py`)**: Development amortization, serverless bandwidth costs, and break-even unit sales.
- **Inventory & Reorder Engine (`src/core/inventory.py`)**: Reorder Point (ROP), Safety Stock, EOQ, GMROI, and Days of Inventory Remaining (DIR).
- **Landed Cost & Customs (`src/core/landed_cost.py`)**: Assessable value (CIF), Basic Customs Duty (BCD), Social Welfare Surcharge (SWS), and Import IGST.
- **Marketplace Settlement Reconciliation (`src/core/settlement.py`)**: Realization percentage, GST TCS (Sec 52), Income Tax TDS (Sec 194-O), and reserves.
- **High-throughput Bulk Spreadsheet Service (`src/services/bulk_import.py`)**: CSV and XLSX bulk validation and calculation engine.
- **Local Persistence (`src/db/`)**: SQLite database with SQLAlchemy relational schema and automated migrations.
- **Desktop UI Shell (`src/ui/`)**: Modern PySide6 responsive application with Dark and Light themes, sidebar routing across 21 pages.
- **Comprehensive Automated Test Suite (`tests/`)**: 82 unit and integration tests covering 100% of the mathematical algorithms.
- **One-click Windows Launch Script (`Run-CommerceCalc.bat`)**.
