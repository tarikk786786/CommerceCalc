"""
Reports and Financial Exports Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QComboBox, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from ..widgets.common import (
    MetricCard, make_card, fmt_inr, fmt_pct, InfoBox
)


class ReportsPage(QWidget):
    """Financial reporting and export center."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        header_card, h_layout = make_card()
        h_row = QHBoxLayout()
        h_row.setSpacing(12)

        type_lbl = QLabel("Report Type:")
        type_lbl.setStyleSheet("font-weight: bold; color: #f1f5f9;")
        h_row.addWidget(type_lbl)

        self.report_combo = QComboBox()
        self.report_combo.addItems([
            "Executive Profitability Audit",
            "GST & Tax Liability Ledger",
            "Marketplace & Courier Logistics Deduction Report",
            "RTO & Returns Risk Exposure Report"
        ])
        self.report_combo.currentIndexChanged.connect(self._render_report)
        h_row.addWidget(self.report_combo, 1)

        csv_btn = QPushButton("📄 Export to CSV")
        csv_btn.setObjectName("secondary_btn")
        csv_btn.clicked.connect(self._export_csv)
        h_row.addWidget(csv_btn)

        xlsx_btn = QPushButton("📊 Export to Excel (.xlsx)")
        xlsx_btn.setObjectName("primary_btn")
        xlsx_btn.clicked.connect(self._export_xlsx)
        h_row.addWidget(xlsx_btn)

        h_layout.addLayout(h_row)
        layout.addWidget(header_card)

        # Main Report Table
        self.table = QTableWidget(0, 5)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        self._render_report(0)

    def _render_report(self, idx):
        if idx == 0:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["SKU / Channel", "Gross Sales", "COGS Outlay", "Net Profit", "Margin %"])
            data = [
                ("TSH-M-BLK (Amazon IN)", "₹64,900.00", "₹24,000.00", "₹14,900.00", "22.95%"),
                ("EAR-TWS-01 (Flipkart)", "₹119,900.00", "₹48,000.00", "₹34,500.00", "28.77%"),
                ("BOT-SS-1000 (Meesho)", "₹54,900.00", "₹18,000.00", "₹16,400.00", "29.87%"),
                ("OIL-ALM-200 (Shopify)", "₹74,900.00", "₹32,000.00", "₹21,200.00", "28.30%"),
            ]
        elif idx == 1:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Taxable Base", "CGST (9%)", "SGST (9%)", "IGST (18%)", "Net Liability"])
            data = [
                ("₹55,000.00 (Intra-state)", "₹4,950.00", "₹4,950.00", "₹0.00", "₹9,900.00"),
                ("₹101,610.00 (Inter-state)", "₹0.00", "₹0.00", "₹18,289.80", "₹18,289.80"),
                ("₹49,017.00 (Inter-state)", "₹0.00", "₹0.00", "₹5,882.04", "₹5,882.04"),
            ]
        else:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Metric Category", "Amazon India", "Flipkart", "Meesho", "Total Outflow"])
            data = [
                ("Platform Commission", "₹14,200.00", "₹18,500.00", "₹4,200.00", "₹36,900.00"),
                ("Courier Forward Shipping", "₹12,400.00", "₹14,200.00", "₹8,900.00", "₹35,500.00"),
                ("RTO / Reverse Logistics Loss", "₹6,800.00", "₹7,400.00", "₹9,200.00", "₹23,400.00"),
            ]

        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                it = QTableWidgetItem(val)
                if "%" in val:
                    it.setForeground(Qt.green)
                self.table.setItem(r, c, it)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report to CSV", "CommerceCalc_Report.csv", "CSV Files (*.csv)")
        if path:
            import csv
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
                writer.writerow(headers)
                for r in range(self.table.rowCount()):
                    writer.writerow([self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(self.table.columnCount())])
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{path}")

    def _export_xlsx(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report to Excel", "CommerceCalc_Report.xlsx", "Excel Files (*.xlsx)")
        if path:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Report"
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            ws.append(headers)
            for r in range(self.table.rowCount()):
                ws.append([self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(self.table.columnCount())])
            wb.save(path)
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{path}")
