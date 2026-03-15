"""File parser utility - reads products from Excel/CSV files."""

import io
import pandas as pd
from typing import Optional


COLUMN_MAPPING = {
    # Vietnamese column names → standard fields
    "tên sản phẩm": "name",
    "tên": "name",
    "ten san pham": "name",
    "product name": "name",
    "name": "name",
    "sản phẩm": "name",

    "giá": "price",
    "gia": "price",
    "price": "price",
    "giá bán": "price",
    "gia ban": "price",

    "giá gốc": "original_price",
    "gia goc": "original_price",
    "original price": "original_price",
    "giá niêm yết": "original_price",

    "danh mục": "category",
    "danh muc": "category",
    "category": "category",
    "loại": "category",

    "mô tả": "description",
    "mo ta": "description",
    "description": "description",
    "chi tiết": "description",

    "hình ảnh": "images",
    "hinh anh": "images",
    "images": "images",
    "image": "images",
    "ảnh": "images",
}


def parse_file(file_content: bytes, filename: str) -> list[dict]:
    """Parse Excel or CSV file and return list of product dicts.
    
    Supports: .xlsx, .xls, .csv, .tsv
    Auto-detects column names (Vietnamese & English).
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_content))
    elif ext == "csv":
        df = pd.read_csv(io.BytesIO(file_content))
    elif ext == "tsv":
        df = pd.read_csv(io.BytesIO(file_content), sep="\t")
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Use .xlsx, .csv, or .tsv")

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map columns to standard names
    rename_map = {}
    for col in df.columns:
        if col in COLUMN_MAPPING:
            rename_map[col] = COLUMN_MAPPING[col]

    df = df.rename(columns=rename_map)

    # Ensure 'name' column exists
    if "name" not in df.columns:
        # Try first text column
        for col in df.columns:
            if df[col].dtype == "object":
                df = df.rename(columns={col: "name"})
                break

    if "name" not in df.columns:
        raise ValueError("Cannot find product name column. "
                         "Please use column header: 'Tên sản phẩm', 'name', or 'Sản phẩm'")

    products = []
    for _, row in df.iterrows():
        product = {
            "name": str(row.get("name", "")).strip(),
            "price": _parse_price(row.get("price")),
            "original_price": _parse_price(row.get("original_price")),
            "category": str(row.get("category", "")).strip() or None,
            "description": str(row.get("description", "")).strip() or None,
            "images": _parse_images(row.get("images")),
            "source": "import"
        }

        # Skip rows without name
        if product["name"] and product["name"] != "nan":
            products.append(product)

    return products


def _parse_price(value) -> Optional[float]:
    """Parse price from various formats."""
    if pd.isna(value):
        return None
    try:
        # Remove currency symbols and formatting
        cleaned = str(value).replace("đ", "").replace(",", "").replace(".", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_images(value) -> list[str]:
    """Parse image URLs from string (comma or pipe separated)."""
    if pd.isna(value) or not value:
        return []
    text = str(value).strip()
    if "|" in text:
        return [u.strip() for u in text.split("|") if u.strip()]
    elif "," in text:
        return [u.strip() for u in text.split(",") if u.strip()]
    return [text] if text else []
