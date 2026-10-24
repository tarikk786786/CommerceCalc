"""
Help, Formula Reference, and Documentation Page for CommerceCalc.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QTextBrowser
)
from ..widgets.common import make_card


HELP_TEXT_HTML = """
<style>
    h2 { color: #818cf8; font-size: 16px; margin-top: 16px; margin-bottom: 6px; }
    h3 { color: #a5b4fc; font-size: 14px; margin-top: 12px; margin-bottom: 4px; }
    p, li { color: #cbd5e1; font-size: 13px; line-height: 1.5; }
    code { background-color: #252840; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; }
    .box { background-color: #1e2235; border-left: 3px solid #6366f1; padding: 10px 14px; margin: 10px 0; }
</style>

<h2>1. Financial Accounting Model</h2>
<p>CommerceCalc strictly enforces a multi-layer contribution accounting structure. It never conflates statutory tax with business revenue, nor does it count recoverable tax credits as permanent costs.</p>

<div class="box">
<b>Net Sales Revenue</b> = Taxable Selling Price − Seller-Funded Discounts + Customer-Paid Shipping<br>
<b>Total Acquisition Cost</b> = Purchase Cost + Packaging + Prep + Inbound Freight − Recoverable ITC<br>
<b>Contribution Profit (Before Ads)</b> = Net Sales Revenue − Acquisition Cost − Courier − Platform Fees − Return Losses<br>
<b>Contribution Profit (After Ads)</b> = Contribution Profit (Before Ads) − Attributable Ad Spend (CAC)<br>
<b>Estimated Operating Profit</b> = Contribution Profit (After Ads) − Allocated Fixed Overhead
</div>

<h2>2. Margin vs Markup (Crucial Difference)</h2>
<p>Many online sellers confuse margin with markup, which frequently leads to setting prices too low and burning capital:</p>
<ul>
    <li><b>Contribution Margin %</b>: Profit divided by <i>Selling Price (Revenue)</i> × 100. Measures what portion of incoming revenue is profit.</li>
    <li><b>Markup %</b>: Profit divided by <i>Product Cost</i> × 100. Measures the percentage added on top of cost.</li>
    <li><i>Example</i>: If a product costs ₹800 and sells for ₹1,000, profit is ₹200. The <b>Margin is 20.0%</b> while the <b>Markup is 25.0%</b>.</li>
</ul>

<h2>3. Indian Goods & Services Tax (GST) Calculations</h2>
<p>CommerceCalc supports both tax-exclusive and tax-inclusive retail pricing models:</p>
<ul>
    <li><b>Tax-Inclusive (Reverse Extraction)</b>: <code>Taxable Value = Gross Price / (1 + Rate / 100)</code>. For ₹1,180 at 18% GST, Taxable is ₹1,000 and Output GST is ₹180.</li>
    <li><b>Tax-Exclusive (Forward Application)</b>: <code>Output GST = Taxable Price × (Rate / 100)</code>. For ₹1,000 at 18% GST, Output GST is ₹180 and Total is ₹1,180.</li>
    <li><b>Intra-State vs Inter-State</b>: Intra-state transactions divide output GST equally between <b>CGST</b> (Central) and <b>SGST</b> (State). Inter-state sales attract unified <b>IGST</b>.</li>
    <li><b>Input Tax Credit (ITC)</b>: When eligible, GST paid on product acquisition offsets your output GST tax liability.</li>
</ul>

<h2>4. Target Selling Price Solver Equations</h2>
<p>When selling on platforms like Amazon or Flipkart, commissions and gateway fees are percentage-based deductions taken from the customer's payment. Adding fixed costs to an unadjusted base ignores these circular deductions.</p>
<div class="box">
<b>Target Selling Price</b> = <code>(Fixed Acquisition Costs + Target Profit) / (1 − Sum of Variable % Fees)</code><br>
<b>Target Margin Price</b> = <code>Fixed Acquisition Costs / (1 − Sum of Variable % Fees − Target Margin %)</code>
</div>

<h2>5. Advertising & ROAS Equations</h2>
<ul>
    <li><b>ROAS (Return on Ad Spend)</b> = <code>Attributed Revenue / Ad Spend</code></li>
    <li><b>Break-Even ROAS</b> = <code>1 / (Contribution Margin Fraction Before Ads)</code>. If your pre-ad margin is 40% (0.40), your Break-Even ROAS is <code>1 / 0.40 = 2.50x</code>. Any ROAS below 2.5x burns money.</li>
    <li><b>Maximum Allowable CAC</b> = <code>Average Order Value × Pre-Ad Margin Fraction</code>.</li>
</ul>

<h2>6. Official Data Verification Protocol</h2>
<p>To preserve data integrity, CommerceCalc does not invent or assume marketplace commission rates. Always check your seller central schedules:</p>
<ul>
    <li><b>Amazon India</b>: <a href="https://sell.amazon.in/fees" style="color: #60a5fa;">sell.amazon.in/fees</a></li>
    <li><b>Flipkart</b>: <a href="https://seller.flipkart.com" style="color: #60a5fa;">seller.flipkart.com</a></li>
    <li><b>Meesho</b>: <a href="https://supplier.meesho.com" style="color: #60a5fa;">supplier.meesho.com</a></li>
    <li><b>Indian Customs Tariffs</b>: <a href="https://www.cbic.gov.in" style="color: #60a5fa;">cbic.gov.in</a></li>
</ul>
"""


class HelpPage(QWidget):
    """Formula reference and documentation view."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_TEXT_HTML)
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1a1d27;
                border: 1px solid #2d3248;
                border-radius: 12px;
                padding: 20px;
                color: #cbd5e1;
            }
        """)
        layout.addWidget(browser)
