"""
Tests for bulk import and export service.
"""
from decimal import Decimal
from pathlib import Path
from src.services.bulk_import import import_from_csv, export_to_csv, generate_import_template, import_from_xlsx


def test_import_and_calculate_sample_csv(tmp_path):
    csv_file = Path("c:/Users/tarik/Desktop/MY TOOLS/apps/CommerceCalc/data/sample_products.csv")
    assert csv_file.exists()

    batch = import_from_csv(str(csv_file))
    assert batch.total_rows == 6
    assert batch.valid_rows == 6
    assert batch.calculated_rows == 6
    assert batch.profitable_rows >= 4
    assert batch.loss_rows >= 1  # The intentional loss leader sample

    # Export to CSV
    out_csv = tmp_path / "calculated_results.csv"
    ok = export_to_csv(batch, str(out_csv))
    assert ok is True
    assert out_csv.exists()


def test_import_xlsx_template(tmp_path):
    xlsx_file = tmp_path / "test_template.xlsx"
    gen_ok = generate_import_template(str(xlsx_file))
    assert gen_ok is True
    assert xlsx_file.exists()

    batch = import_from_xlsx(str(xlsx_file))
    # The template has 2 sample rows
    assert batch.total_rows == 2
    assert batch.valid_rows == 2
    assert batch.calculated_rows == 2
