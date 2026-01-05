import pandas as pd
import io

def clean_currency(x):
    """Converts string currency (e.g. '1,000.00') to float."""
    if isinstance(x, str):
        # Remove commas and spaces, then convert to float
        clean_str = x.replace(',', '').replace(' ', '')
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return x

def find_header_row(df_raw: pd.DataFrame, target_columns: list) -> int:
    """
    Scans the first 30 rows to find where the actual header matches 
    expected columns.
    """
    for i in range(30):  # Scan first 30 rows
        # Convert row to string, lowercase, and strip spaces
        row_values = [str(val).strip().lower() for val in df_raw.iloc[i].tolist()]
        
        # Check if matched (we look for at least 1 strong match like 'amount' or 'rrn')
        match_count = sum(1 for target in target_columns if target.lower() in row_values)
        
        # If we find at least 2 expected columns, we assume this is the header
        if match_count >= 1: # Lowered threshold to 1 for safety
            return i
    return -1 # Not found

def load_excel_dynamic(file_content: bytes, required_cols: list, default_row: int = 0) -> pd.DataFrame:
    """
    Reads Excel, finds header dynamically, and standardizes column names.
    If dynamic detection fails, falls back to `default_row`.
    """
    try:
        # Read without header first to scan structure
        df_raw = pd.read_excel(io.BytesIO(file_content), header=None)
        
        header_idx = find_header_row(df_raw, required_cols)
        
        if header_idx == -1:
            print(f"Warning: Could not auto-detect header for columns {required_cols}. Using default row {default_row}.")
            header_idx = default_row
        else:
            print(f"Header found at row index: {header_idx}")

        # Reload with correct header
        df = pd.read_excel(io.BytesIO(file_content), header=header_idx)
        
        # Normalize headers: strip whitespace, uppercase
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # Debugging: Print columns found
        print(f"Loaded Columns: {df.columns.tolist()}")
        
        return df
    except Exception as e:
        print(f"Error loading Excel: {str(e)}")
        raise e