"""
PnL CSV loading and validation module.
"""
from pathlib import Path

import polars as pl


DATE_COLUMN = 'datetime'


def get_return_columns(df: pl.DataFrame) -> list[str]:
    """Return the non-date columns that represent daily return series."""
    return [col for col in df.columns if col != DATE_COLUMN]


def load_pnl_data(file_path: str) -> pl.DataFrame:
    """Load and validate daily return series from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PnL file not found: {file_path}")

    try:
        df = pl.read_csv(file_path, infer_schema_length=0)
    except Exception as exc:
        raise ValueError(f"Unable to read PnL CSV: {exc}") from exc

    if DATE_COLUMN not in df.columns:
        raise ValueError(f"Missing required column: {DATE_COLUMN}")

    return_columns = get_return_columns(df)
    if not return_columns:
        raise ValueError("No return series columns found in pnl.csv")

    try:
        timezone_values = df.filter(
            pl.col(DATE_COLUMN).str.contains(r'(Z|[+-]\d{2}:?\d{2})$')
        )
        if timezone_values.height > 0:
            raise ValueError("Timezone-aware datetime values are not supported")

        df = df.with_columns(
            pl.col(DATE_COLUMN)
            .str.to_datetime(strict=True)
            .dt.date()
            .alias(DATE_COLUMN)
        )
        if df.filter(pl.col(DATE_COLUMN).is_null()).height > 0:
            raise ValueError("Unable to parse datetime column: null values found")
    except Exception as exc:
        message = str(exc)
        if message == "Timezone-aware datetime values are not supported":
            raise ValueError(message) from exc
        if message == "Unable to parse datetime column: null values found":
            raise ValueError(message) from exc
        raise ValueError(f"Unable to parse datetime column: {exc}") from exc

    for col in return_columns:
        try:
            df = df.with_columns(
                pl.col(col).cast(pl.Float64, strict=True).fill_null(0.0).alias(col)
            )
        except Exception as exc:
            raise ValueError(f"Unable to parse numeric return column: {col}") from exc
        if df.filter(~pl.col(col).is_finite()).height > 0:
            raise ValueError(f"Non-finite return values in column: {col}")
        if df.filter(pl.col(col) < -1.0).height > 0:
            raise ValueError(f"Return values below -1.0 in column: {col}")

    duplicate_count = df.group_by(DATE_COLUMN).len().filter(pl.col('len') > 1).height
    if duplicate_count > 0:
        raise ValueError("Duplicate datetime values found in pnl.csv")

    return df.sort(DATE_COLUMN)
