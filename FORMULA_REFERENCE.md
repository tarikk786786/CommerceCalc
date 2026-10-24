# CommerceCalc — Master Financial Formula Reference

This document provides transparent, mathematically auditable documentation of every calculation model employed in CommerceCalc.

---

## 1. Accounting Foundation

CommerceCalc employs a strict decimal-based contribution accounting model:

$$\text{Net Sales Revenue} = \text{Taxable Selling Price} - \text{Seller-Funded Discounts} + \text{Customer-Paid Shipping}$$

$$\text{Total Acquisition Cost} = \text{Purchase Cost} + \text{Packaging} + \text{Preparation} + \text{Inbound Freight} + \text{Inspection} + \text{Customs} - \text{Recoverable ITC}$$

$$\text{Total Variable Expenses} = \text{Marketplace Fees} + \text{Payment Gateway} + \text{Forward Delivery} + \text{COD Handling} + \text{Affiliate Fees} + \text{Return/RTO Loss}$$

$$\text{Contribution Profit Before Advertising} = \text{Net Sales Revenue} - \text{Total Acquisition Cost} - \text{Total Variable Expenses}$$

$$\text{Contribution Profit After Advertising} = \text{Contribution Profit Before Advertising} - \text{Attributable Advertising Spend}$$

$$\text{Estimated Operating Profit} = \text{Contribution Profit After Advertising} - \text{Allocated Operating Overhead}$$

---

## 2. Indian Goods and Services Tax (GST)

### Tax-Exclusive Pricing (GST Added to Price)
Given taxable selling price $P_{\text{taxable}}$ and GST rate $R_{\%}$:
$$\text{Output GST} = P_{\text{taxable}} \times \frac{R_{\%}}{100}$$
$$\text{Customer-Facing Price} = P_{\text{taxable}} + \text{Output GST}$$

### Tax-Inclusive Pricing (GST Extracted from Gross Price)
Given customer-facing price $P_{\text{gross}}$ and GST rate $R_{\%}$:
$$P_{\text{taxable}} = \frac{P_{\text{gross}}}{1 + \frac{R_{\%}}{100}}$$
$$\text{Output GST} = P_{\text{gross}} - P_{\text{taxable}}$$

### Intra-State vs Inter-State Apportionment
- **Intra-State**:
  $$\text{CGST} = \frac{\text{Output GST}}{2}, \quad \text{SGST} = \text{Output GST} - \text{CGST}$$
- **Inter-State**:
  $$\text{IGST} = \text{Output GST}$$

---

## 3. Margin vs Markup (The Non-Negotiable Difference)

### Contribution Margin
Percentage of **revenue** that remains as profit:
$$\text{Margin}_{\%} = \frac{\text{Profit}}{\text{Net Sales Revenue}} \times 100$$

### Markup
Percentage by which **cost** is marked up to generate profit:
$$\text{Markup}_{\%} = \frac{\text{Profit}}{\text{Total Cost Base}} \times 100$$

*Example*: If Cost = ₹800 and Selling Price = ₹1,000, Profit = ₹200.
$$\text{Margin} = \frac{200}{1000} \times 100 = 20.0\%$$
$$\text{Markup} = \frac{200}{800} \times 100 = 25.0\%$$

---

## 4. Target Selling Price Mathematical Solver

Let:
- $F$ = Sum of all per-unit fixed costs (acquisition, packaging, fixed courier base, fixed closing fee, target profit).
- $V$ = Sum of all percentage variable fees (marketplace commission %, payment gateway %, affiliate %, ad %).
- $M$ = Target contribution margin fraction ($\frac{\text{Target Margin}_{\%}}{100}$).

### Target Profit Formula
$$P_{\text{taxable}} = \frac{F + \text{Target Profit}}{1 - V}$$

### Target Margin Formula
$$P_{\text{taxable}} = \frac{F}{1 - V - M}$$
*Infeasibility Guard*: If $1 - V - M \le 0$, no finite positive selling price can achieve the target margin.

---

## 5. Advertising, CAC, and ROAS

$$\text{ROAS} = \frac{\text{Attributed Revenue}}{\text{Ad Spend}}$$
$$\text{Break-Even ROAS} = \frac{1}{\text{Contribution Margin Fraction Before Ads}}$$
$$\text{ACoS} = \frac{\text{Ad Spend}}{\text{Attributed Revenue}} \times 100$$
$$\text{TACoS} = \frac{\text{Ad Spend}}{\text{Total Store Net Revenue}} \times 100$$
$$\text{Maximum Allowable CAC} = \text{Average Order Value} \times \text{Contribution Margin Fraction Before Ads}$$

---

## 6. Courier & Volumetric Weight Model

$$\text{Volumetric Weight (kg)} = \frac{\text{Length (cm)} \times \text{Width (cm)} \times \text{Height (cm)}}{\text{Dimensional Divisor (typically 5000)}}$$
$$\text{Chargeable Weight} = \max(\text{Actual Weight}, \text{Volumetric Weight})$$
$$\text{Weight Slabs} = \left\lceil \frac{\text{Chargeable Weight}}{\text{Slab Size (kg)}} \right\rceil$$

---

## 7. Returns and RTO Risk Model

$$\text{Expected Loss} = (\text{Expected Returns} \times \text{Reverse Courier}) + (\text{Expected RTO} \times (\text{Forward Courier} + \text{RTO Charge})) + \text{Damaged Inventory Cost} - \text{Recovered Salvage Value}$$
$$\text{Risk Adjustment per Order} = \frac{\text{Total Expected Loss}}{\text{Total Orders Planned}}$$

---

## 8. Marketplace Cash Settlement Model

$$\text{Net Payout} = \text{Gross Orders} - \text{Marketplace Fees} - \text{GST on Fees (18\%)} - \text{TCS (1\%)} - \text{TDS (0.1\%)} - \text{Refunds} - \text{Rolling Reserve}$$
$$\text{Realization Rate} = \frac{\text{Net Bank Settlement}}{\text{Gross Orders}} \times 100$$
