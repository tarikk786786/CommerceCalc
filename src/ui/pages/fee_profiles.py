"""
Marketplace Fee Profiles Editor Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QComboBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, FormFieldRow
)
from ...core.fees import (
    MarketplaceProfile, FeeRule, create_empty_amazon_india_profile,
    create_empty_flipkart_profile, create_empty_meesho_profile, create_custom_profile
)


class FeeProfilesPage(QWidget):
    """Interactive marketplace fee configuration and audit profile editor."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._profiles = {
            "amazon_india": create_empty_amazon_india_profile(),
            "flipkart": create_empty_flipkart_profile(),
            "meesho": create_empty_meesho_profile(),
            "custom": create_custom_profile("custom_1", "Direct Website (Shopify/Woo)"),
        }
        self._current_profile_key = "amazon_india"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(DisclaimerBox(
            "VERIFICATION REQUIREMENT: Marketplace fee schedules change frequently. "
            "CommerceCalc does NOT hardcode assumed fees. Enter verified commission percentages "
            "and closing fees directly from your official seller portal and maintain source URLs."
        ))

        # Top Profile Selector
        top_card, top_layout = make_card()
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        lbl = QLabel("Active Platform Profile:")
        lbl.setStyleSheet("font-weight: bold; color: #f1f5f9; font-size: 13px;")
        top_row.addWidget(lbl)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems([
            "Amazon India (sell.amazon.in)",
            "Flipkart (seller.flipkart.com)",
            "Meesho (supplier.meesho.com)",
            "Direct Website / Shopify / WooCommerce"
        ])
        self.profile_combo.currentIndexChanged.connect(self._on_profile_switch)
        top_row.addWidget(self.profile_combo, 1)

        self.verified_cb = QCheckBox("Mark Profile as Officially Verified")
        self.verified_cb.stateChanged.connect(self._on_verified_toggle)
        top_row.addWidget(self.verified_cb)

        save_btn = QPushButton("💾 Save Profile")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self._save_profile)
        top_row.addWidget(save_btn)

        top_layout.addLayout(top_row)
        layout.addWidget(top_card)

        # Profile Metadata
        meta_card, meta_layout = make_card("Profile Verification & Audit Metadata")
        m_grid = QGridLayout()
        m_grid.setSpacing(12)

        self.source_url = QLineEdit()
        self.source_url.setPlaceholderText("https://sell.amazon.in/fees")
        m_grid.addWidget(QLabel("Official Source URL:"), 0, 0)
        m_grid.addWidget(self.source_url, 0, 1)

        self.category_in = QLineEdit()
        self.category_in.setPlaceholderText("e.g. Apparel / Electronics / Home")
        m_grid.addWidget(QLabel("Target Product Category:"), 0, 2)
        m_grid.addWidget(self.category_in, 0, 3)

        self.notes_in = QLineEdit()
        self.notes_in.setPlaceholderText("Verified on official portal for Q4 2026 fee rate card.")
        m_grid.addWidget(QLabel("Audit Notes:"), 1, 0)
        m_grid.addWidget(self.notes_in, 1, 1, 1, 3)

        meta_layout.addLayout(m_grid)
        layout.addWidget(meta_card)

        # Rules Table
        table_card, table_layout = make_card("Configured Platform Fee Rules")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Fee Rule Name", "Type", "Rate / Amount", "Condition", "Enabled"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_rule_btn = QPushButton("+ Add Fee Rule")
        add_rule_btn.setObjectName("secondary_btn")
        add_rule_btn.clicked.connect(self._add_rule)
        del_rule_btn = QPushButton("Remove Selected Rule")
        del_rule_btn.setObjectName("danger_btn")
        del_rule_btn.clicked.connect(self._remove_rule)
        btn_row.addWidget(add_rule_btn)
        btn_row.addWidget(del_rule_btn)
        btn_row.addStretch()
        table_layout.addLayout(btn_row)
        layout.addWidget(table_card, 1)

        self._load_current_profile()

    def _on_profile_switch(self, idx):
        keys = ["amazon_india", "flipkart", "meesho", "custom"]
        self._current_profile_key = keys[idx]
        self._load_current_profile()

    def _load_current_profile(self):
        p: MarketplaceProfile = self._profiles[self._current_profile_key]
        self.source_url.setText(p.source_url)
        self.category_in.setText(p.category)
        self.notes_in.setText(p.notes)
        self.verified_cb.setChecked(p.is_verified)

        self.table.setRowCount(len(p.fee_rules))
        for r, rule in enumerate(p.fee_rules):
            self.table.setItem(r, 0, QTableWidgetItem(rule.name))
            self.table.setItem(r, 1, QTableWidgetItem(rule.fee_type))
            val_str = f"{rule.amount}%" if rule.fee_type == "percentage" else f"₹{rule.amount}"
            self.table.setItem(r, 2, QTableWidgetItem(val_str))
            self.table.setItem(r, 3, QTableWidgetItem(rule.condition or "All Orders"))
            self.table.setItem(r, 4, QTableWidgetItem("Yes" if rule.enabled else "No"))

    def _on_verified_toggle(self, state):
        p = self._profiles[self._current_profile_key]
        p.is_verified = (state == Qt.Checked)

    def _add_rule(self):
        p = self._profiles[self._current_profile_key]
        new_rule = FeeRule(
            name=f"Custom Rule {len(p.fee_rules)+1}",
            fee_type="percentage",
            amount=Decimal("5.0"),
            enabled=True,
        )
        p.fee_rules.append(new_rule)
        self._load_current_profile()

    def _remove_rule(self):
        cur = self.table.currentRow()
        p = self._profiles[self._current_profile_key]
        if 0 <= cur < len(p.fee_rules):
            p.fee_rules.pop(cur)
            self._load_current_profile()

    def _save_profile(self):
        p = self._profiles[self._current_profile_key]
        p.source_url = self.source_url.text()
        p.category = self.category_in.text()
        p.notes = self.notes_in.text()
        QMessageBox.information(
            self, "Profile Saved",
            f"Marketplace profile '{p.name}' updated.\nVerified Status: {'Verified' if p.is_verified else 'Unverified'}"
        )
