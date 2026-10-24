"""
Product Catalog Management Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QFormLayout
)
from PySide6.QtCore import Qt
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, make_card, fmt_inr
)


class CatalogPage(QWidget):
    """Local product catalog management."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._products = [
            {"name": "Cotton Crewneck T-Shirt", "sku": "TSH-COT-01", "category": "Apparel", "cost": Decimal("240"), "price": Decimal("649"), "gst": Decimal("5")},
            {"name": "Wireless Noise Cancelling Earbuds", "sku": "TWS-ANC-02", "category": "Electronics", "cost": Decimal("550"), "price": Decimal("1299"), "gst": Decimal("18")},
            {"name": "Stainless Steel Thermal Bottle", "sku": "BOT-SS-03", "category": "Home", "cost": Decimal("180"), "price": Decimal("549"), "gst": Decimal("12")},
            {"name": "Ceramic Coffee Mug Set (4pc)", "sku": "MUG-CRM-04", "category": "Kitchen", "cost": Decimal("220"), "price": Decimal("699"), "gst": Decimal("12")},
        ]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        header_card, h_layout = make_card()
        h_row = QHBoxLayout()
        h_row.setSpacing(12)

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍 Search products by name, SKU, or category...")
        self.search_in.textChanged.connect(self._filter_table)
        h_row.addWidget(self.search_in, 1)

        add_btn = QPushButton("+ New Product")
        add_btn.setObjectName("primary_btn")
        add_btn.clicked.connect(self._add_product)
        h_row.addWidget(add_btn)

        del_btn = QPushButton("Delete Selected")
        del_btn.setObjectName("danger_btn")
        del_btn.clicked.connect(self._delete_product)
        h_row.addWidget(del_btn)

        h_layout.addLayout(h_row)
        layout.addWidget(header_card)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Product Name", "SKU", "Category", "Purchase Cost", "Selling Price", "GST Rate"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in [1, 2, 3, 4, 5]:
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        self._populate_table()

    def _populate_table(self):
        q = self.search_in.text().lower()
        filtered = [p for p in self._products if q in p["name"].lower() or q in p["sku"].lower() or q in p["category"].lower()]
        self.table.setRowCount(len(filtered))
        for r, p in enumerate(filtered):
            self.table.setItem(r, 0, QTableWidgetItem(p["name"]))
            self.table.setItem(r, 1, QTableWidgetItem(p["sku"]))
            self.table.setItem(r, 2, QTableWidgetItem(p["category"]))
            self.table.setItem(r, 3, QTableWidgetItem(fmt_inr(p["cost"])))
            self.table.setItem(r, 4, QTableWidgetItem(fmt_inr(p["price"])))
            self.table.setItem(r, 5, QTableWidgetItem(f"{p['gst']}%"))

    def _filter_table(self):
        self._populate_table()

    def _add_product(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add New Product to Catalog")
        dlg.setMinimumWidth(360)
        d_layout = QFormLayout(dlg)

        name_in = QLineEdit()
        sku_in = QLineEdit()
        cat_in = QLineEdit()
        cost_in = MoneyInput()
        price_in = MoneyInput()

        d_layout.addRow("Product Name*:", name_in)
        d_layout.addRow("SKU Code:", sku_in)
        d_layout.addRow("Category:", cat_in)
        d_layout.addRow("Purchase Cost (₹):", cost_in)
        d_layout.addRow("Selling Price (₹):", price_in)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("Save Product")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(dlg.accept)
        btn_box.addWidget(save_btn)
        d_layout.addRow(btn_box)

        if dlg.exec() == QDialog.Accepted and name_in.text():
            self._products.append({
                "name": name_in.text(),
                "sku": sku_in.text() or f"SKU-{len(self._products)+1}",
                "category": cat_in.text() or "General",
                "cost": cost_in.get_decimal(),
                "price": price_in.get_decimal(),
                "gst": Decimal("18"),
            })
            self._populate_table()

    def _delete_product(self):
        cur = self.table.currentRow()
        if 0 <= cur < len(self._products):
            self._products.pop(cur)
            self._populate_table()
