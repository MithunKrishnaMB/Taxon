import csv
import json
from collections.abc import Generator
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import openpyxl

from app.domain.ingestion.schemas import ParsedInvoiceRow


def _map_row_to_invoice(row_dict: dict[str, Any], row_num: int) -> ParsedInvoiceRow:
    """Normalize headers (e.g., matching 'Invoice Number' or 'doc_no' to doc_no)."""
    # Normalize dictionary keys to lowercase for flexible column header matching
    norm_dict = {
        str(k).strip().lower().replace(" ", "_"): v
        for k, v in row_dict.items()
        if k is not None
    }

    doc_no = (
        norm_dict.get("doc_no")
        or norm_dict.get("invoice_no")
        or norm_dict.get("invoice_number")
        or norm_dict.get("irn")
    )
    supplier_gstin = (
        norm_dict.get("supplier_gstin")
        or norm_dict.get("gstin")
        or norm_dict.get("vendor_gstin")
    )
    amount_raw = norm_dict.get("amount") or norm_dict.get("total_amount") or 0
    gst_raw = norm_dict.get("gst_amount") or norm_dict.get("tax_amount") or 0

    if not doc_no or not supplier_gstin:
        raise ValueError(
            f"Row {row_num}: Missing required 'Invoice Number' or 'GSTIN' column."
        )

    try:
        amount = Decimal(str(amount_raw))
        gst_amount = Decimal(str(gst_raw))
    except (InvalidOperation, ValueError) as err:
        raise ValueError(
            f"Row {row_num}: Invalid numeric amount ({amount_raw}, {gst_raw})."
        ) from err

    return ParsedInvoiceRow(
        doc_no=str(doc_no),
        supplier_gstin=str(supplier_gstin),
        amount=amount,
        gst_amount=gst_amount,
    )


def parse_excel_stream(
    file_path: str, batch_size: int = 250
) -> Generator[list[ParsedInvoiceRow], None, None]:
    """Memory-efficient streaming Excel parser using openpyxl read_only=True."""
    workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = workbook.active
    if not sheet:
        return

    headers: list[str] = []
    batch: list[ParsedInvoiceRow] = []

    for row_num, row_cells in enumerate(sheet.iter_rows(values_only=True), start=1):
        if row_num == 1:
            # First row contains headers
            headers = [str(cell).strip() if cell is not None else "" for cell in row_cells]
            continue

        # Skip empty rows
        if all(cell is None for cell in row_cells):
            continue

        row_dict = dict(zip(headers, row_cells, strict=False))
        try:
            parsed_row = _map_row_to_invoice(row_dict, row_num)
            batch.append(parsed_row)
        except (ValueError, KeyError) as e:
            # Log or raise depending on strictness; we raise for clean schema enforcement
            raise ValueError(f"Error parsing Excel row {row_num}: {str(e)}") from e

        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

    workbook.close()


def parse_csv_stream(
    file_path: str, batch_size: int = 250
) -> Generator[list[ParsedInvoiceRow], None, None]:
    """Memory-efficient streaming CSV parser using standard csv.DictReader."""
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch: list[ParsedInvoiceRow] = []

        for row_num, row_dict in enumerate(reader, start=2):
            try:
                parsed_row = _map_row_to_invoice(row_dict, row_num)
                batch.append(parsed_row)
            except (ValueError, KeyError) as e:
                raise ValueError(f"Error parsing CSV row {row_num}: {str(e)}") from e

            if len(batch) == batch_size:
                yield batch
                batch = []

        if batch:
            yield batch


def parse_json_stream(
    file_path: str, batch_size: int = 250
) -> Generator[list[ParsedInvoiceRow], None, None]:
    """Parse JSON array files into batches."""
    with open(file_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON statement file must contain a list of invoice objects.")

    batch: list[ParsedInvoiceRow] = []
    for idx, item in enumerate(data, start=1):
        parsed_row = _map_row_to_invoice(item, idx)
        batch.append(parsed_row)

        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def parse_statement_file(
    file_path: str, batch_size: int = 250
) -> Generator[list[ParsedInvoiceRow], None, None]:
    """Master streaming dispatcher: routes .xlsx, .csv and .json to the right generator."""
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".xlsx":
        yield from parse_excel_stream(file_path, batch_size)
    elif extension == ".csv":
        yield from parse_csv_stream(file_path, batch_size)
    elif extension == ".json":
        yield from parse_json_stream(file_path, batch_size)
    else:
        raise ValueError(
            f"Unsupported file format '{extension}'. Please upload .xlsx, .csv  or .json files."
        )