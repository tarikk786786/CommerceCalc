"""
Bulk Spreadsheet Product Calculator Page for CommerceCalc.
"""
from pathlib import Path
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from ..widgets.common import (
    MetricCard, SectionTitle, Divider, ResultRow, InfoBox, make_card, fmt_inr, fmt_pct
)
from ...services.bulk_import import (
    import_from_csv, import_from_xlsx, export_to_csv, generate_import_template, ImportBatchResult
)


class BulkCalcPage(QWidget):
    """High-throughput spreadsheet batch calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._current_batch: ImportBatchResult = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Header card with action buttons
        header_card, h_layout = make_card()
        h_row = QHBoxLayout()
        h_row.setSpacing(12)

        title_layout = QVBoxLayout()
        title_lbl = QLabel("Spreadsheet Batch Calculator")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1f5f9;")
        desc_lbl = QLabel("Import hundreds of products via CSV or XLSX to audit portfolio margins and identify unprofitable SKUs.")
        desc_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(desc_lbl)
        h_row.addLayout(title_layout, 1)

        load_sample_btn = QPushButton("📂 Load Sample Dataset")
        load_sample_btn.setObjectName("secondary_btn")
        load_sample_btn.clicked.connect(self._load_sample_data)
        h_row.addWidget(load_sample_btn)

        import_btn = QPushButton("📥 Import CSV / Excel")
        import_btn.setObjectName("primary_btn")
        import_btn.clicked.connect(self._browse_and_import)
        h_row.addWidget(import_btn)

        template_btn = QPushButton("📄 Download Template")
        template_btn.setObjectName("secondary_btn")
        template_btn.clicked.connect(self._download_template)
        h_row.addWidget(template_btn)

        export_btn = QPushButton("📤 Export Results")
        export_btn.setObjectName("secondary_btn")
        export_btn.clicked.connect(self._export_results)
        h_row.addWidget(export_btn)

        self.btn_ai_audit = QPushButton("✨ AI Portfolio Audit (Gemini 2.5)")
        self.btn_ai_audit.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
            }
        """)
        self.btn_ai_audit.clicked.connect(self._run_ai_portfolio_audit)
        h_row.addWidget(self.btn_ai_audit)

        h_layout.addLayout(h_row)
        layout.addWidget(header_card)

        # Summary KPIs
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        self.card_total_rows = MetricCard("Total Rows Imported", "0", "default")
        self.card_profitable_rows = MetricCard("Profitable SKUs", "0", "success")
        self.card_loss_rows = MetricCard("Loss-Making SKUs", "0", "danger")
        self.card_total_profit = MetricCard("Batch Net Profit", "₹0.00", "success")
        metrics_grid.addWidget(self.card_total_rows, 0, 0)
        metrics_grid.addWidget(self.card_profitable_rows, 0, 1)
        metrics_grid.addWidget(self.card_loss_rows, 0, 2)
        metrics_grid.addWidget(self.card_total_profit, 0, 3)
        layout.addLayout(metrics_grid)

        # Filter row
        filter_row = QHBoxLayout()
        filter_lbl = QLabel("Filter Rows:")
        filter_lbl.setStyleSheet("color: #94a3b8; font-weight: bold;")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Show All Products", "Profitable Only (✓)", "Loss-Making Only (✗)", "Invalid / Error Rows"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(filter_lbl)
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Main Table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Row", "Product Name", "SKU", "Cost (₹)", "Price (₹)",
            "Net Revenue", "Net Profit", "Margin %", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for c in [0, 2, 3, 4, 5, 6, 7, 8]:
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        # Auto-load the sample dataset on first open
        self._load_sample_data()

    def _load_sample_data(self):
        sample_path = Path("c:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/data/sample_products.csv")
        if sample_path.exists():
            batch = import_from_csv(str(sample_path))
            self._display_batch(batch)

    def _browse_and_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Spreadsheet File", "", "Spreadsheets (*.csv *.xlsx)"
        )
        if not file_path:
            return
        if file_path.endswith(".csv"):
            batch = import_from_csv(file_path)
        else:
            batch = import_from_xlsx(file_path)
        self._display_batch(batch)

    def _display_batch(self, batch: ImportBatchResult):
        self._current_batch = batch
        self.card_total_rows.update_value(str(batch.total_rows))
        self.card_profitable_rows.update_value(str(batch.profitable_rows), "success")
        loss_type = "danger" if batch.loss_rows > 0 else "default"
        self.card_loss_rows.update_value(str(batch.loss_rows), loss_type)

        tot_prof = Decimal("0")
        for r in batch.rows:
            if r.result and r.result.estimated_operating_profit:
                tot_prof += r.result.estimated_operating_profit
        p_type = "success" if tot_prof >= 0 else "danger"
        self.card_total_profit.update_value(fmt_inr(tot_prof, show_sign=True), p_type)

        self._apply_filter()

    def _apply_filter(self):
        if not self._current_batch:
            return
        filter_idx = self.filter_combo.currentIndex()
        filtered = []
        for r in self._current_batch.rows:
            if filter_idx == 0:
                filtered.append(r)
            elif filter_idx == 1 and r.result and r.result.is_profitable:
                filtered.append(r)
            elif filter_idx == 2 and r.result and not r.result.is_profitable:
                filtered.append(r)
            elif filter_idx == 3 and not r.is_valid:
                filtered.append(r)

        self.table.setRowCount(len(filtered))
        for row_idx, row in enumerate(filtered):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.row_number)))
            name = row.parsed_data.get("product_name", "–")
            self.table.setItem(row_idx, 1, QTableWidgetItem(name))
            sku = row.parsed_data.get("sku", "–")
            self.table.setItem(row_idx, 2, QTableWidgetItem(sku))
            cost = row.parsed_data.get("purchase_cost", Decimal("0"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"₹{cost:,.2f}"))
            sp = row.parsed_data.get("actual_selling_price", Decimal("0"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"₹{sp:,.2f}"))

            if row.result:
                res = row.result
                self.table.setItem(row_idx, 5, QTableWidgetItem(fmt_inr(res.net_revenue)))
                prof_item = QTableWidgetItem(fmt_inr(res.estimated_operating_profit, show_sign=True))
                prof_item.setForeground(Qt.green if res.is_profitable else Qt.red)
                self.table.setItem(row_idx, 6, prof_item)
                margin_item = QTableWidgetItem(fmt_pct(res.contribution_margin_pct))
                margin_item.setForeground(Qt.green if res.is_profitable else Qt.red)
                self.table.setItem(row_idx, 7, margin_item)
                status_item = QTableWidgetItem("PROFIT" if res.is_profitable else "LOSS")
                status_item.setForeground(Qt.green if res.is_profitable else Qt.red)
                self.table.setItem(row_idx, 8, status_item)
            else:
                self.table.setItem(row_idx, 5, QTableWidgetItem("–"))
                self.table.setItem(row_idx, 6, QTableWidgetItem("–"))
                self.table.setItem(row_idx, 7, QTableWidgetItem("–"))
                err_text = "; ".join(row.errors) if row.errors else "INVALID"
                err_item = QTableWidgetItem(err_text)
                err_item.setForeground(Qt.red)
                self.table.setItem(row_idx, 8, err_item)

    def _export_results(self):
        if not self._current_batch:
            QMessageBox.warning(self, "No Data", "No batch calculations available to export.")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Calculated Audit CSV", "CommerceCalc_Audit_Results.csv", "CSV Files (*.csv)"
        )
        if save_path:
            ok = export_to_csv(self._current_batch, save_path)
            if ok:
                QMessageBox.information(self, "Success", f"Results successfully exported to:\n{save_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to write export file.")

    def _download_template(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel Template", "CommerceCalc_Products_Template.xlsx", "Excel Files (*.xlsx)"
        )
        if save_path:
            ok = generate_import_template(save_path)
            if ok:
                QMessageBox.information(self, "Success", f"Template saved to:\n{save_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to generate template.")

    def _run_ai_portfolio_audit(self):
        """Run cloud LLM review on the imported bulk catalog."""
        from ..widgets.ai_dialog import AIDiagnosticDialog
        from ...services.ai_service import CommerceCalcAI

        if not self._current_batch:
            self._load_sample_data()

        b = self._current_batch
        loss_skus = [r.sku for r in b.rows if r.is_valid and r.result and not r.result.is_profitable]
        loss_examples = ", ".join(loss_skus[:5]) if loss_skus else "None"

        data = {
            "total_rows": b.total_rows,
            "profitable_rows": b.profitable_rows,
            "loss_rows": b.loss_making_rows,
            "total_profit": str(b.total_net_profit),
            "avg_margin": f"{b.average_margin_pct:.1f}",
            "loss_examples": loss_examples,
        }

        ai = CommerceCalcAI()
        dlg = AIDiagnosticDialog(
            "AI Bulk Catalog Portfolio Audit",
            lambda: ai.audit_bulk_portfolio(data),
            parent=self
        )
        dlg.exec()
