import pandas as pd
import io


def abbreviate_description(description: str) -> str:
    abbreviations = {
        'Account2Account': 'A2A',
        'ATM CW Transaction Amount': 'ATM',
        'POS PUR THEM-ON-THEM': 'POS',
    }
    for long, short in abbreviations.items():
        description = description.replace(long, short)
    return description


def _find_terminal_column(df: pd.DataFrame) -> str | None:
    """Auto-detect a terminal id column name in the DataFrame."""
    for col in df.columns:
        if not isinstance(col, str):
            continue
        n = col.replace('_', '').replace(' ', '').lower()
        if n in ('terminalid', 'termid'):
            return col
    for col in df.columns:
        if not isinstance(col, str):
            continue
        n = col.lower()
        if 'terminal' in n and 'id' in n:
            return col
    return None


def reconcile_dataframes(eth_df: pd.DataFrame, zzb_df: pd.DataFrame) -> dict:
    """Original reconciliation logic preserved: merge on RRN/Refnum_F37 if present.
    Returns categorized transactions and mismatches as dicts (JSON-serializable).
    """
    # Basic cleaning
    eth = eth_df.copy()
    zzb = zzb_df.copy()
    eth.columns = eth.columns.str.strip()
    zzb.columns = zzb.columns.str.strip()

    # Ensure transaction description exists
    if 'Transaction_Description' in eth.columns:
        eth['Transaction_Description'] = eth['Transaction_Description'].astype(str).fillna('Unknown')
    else:
        eth['Transaction_Description'] = 'Unknown'

    # Use RRN/Refnum_F37 merge if columns exist
    if 'RRN' in zzb.columns and 'Refnum_F37' in eth.columns:
        merged_df = pd.merge(zzb, eth, left_on='RRN', right_on='Refnum_F37', how='left', indicator=True)
    else:
        # Fallback: empty result
        return {'categorized_transactions': {}, 'mismatches': []}

    transaction_descriptions = merged_df['Transaction_Description'].unique()
    categorized_transactions = {}
    for description in transaction_descriptions:
        description = str(description)
        desc_df = merged_df[merged_df['Transaction_Description'] == description]
        zzb_both = desc_df[(desc_df.get('Issuer') == 'ZamZam Bank') & (desc_df.get('Acquirer') == 'ZamZam Bank')]
        zzb_issue = desc_df[(desc_df.get('Issuer') == 'ZamZam Bank') & (desc_df.get('Acquirer') != 'ZamZam Bank')]
        zzb_acquire = desc_df[(desc_df.get('Acquirer') == 'ZamZam Bank') & (desc_df.get('Issuer') != 'ZamZam Bank')]

        categorized_transactions[description] = {
            'zzb_issue': zzb_issue.to_dict(orient='records') if not zzb_issue.empty else [],
            'zzb_acquire': zzb_acquire.to_dict(orient='records') if not zzb_acquire.empty else [],
            'zzb_both': zzb_both.to_dict(orient='records') if not zzb_both.empty else []
        }

    mismatches_df = merged_df[merged_df['_merge'] == 'left_only']
    mismatches = mismatches_df.to_dict(orient='records') if not mismatches_df.empty else []

    return {'categorized_transactions': categorized_transactions, 'mismatches': mismatches}


def reconcile_and_get_excel_bytes(eth_df: pd.DataFrame, zzb_df: pd.DataFrame, key: str | None = None) -> bytes:
    """Compare by terminal id (auto-detected) and return Excel workbook bytes.

    Generated workbook contains sheets: only_in_eth, only_in_zzb, matched_eth, matched_zzb.
    """
    try:
        eth = eth_df.copy()
        zzb = zzb_df.copy()
        eth.columns = eth.columns.str.strip()
        zzb.columns = zzb.columns.str.strip()
        print(f"reconcile_and_get_excel_bytes: ETH columns={list(eth.columns)}")
        print(f"reconcile_and_get_excel_bytes: ZZB columns={list(zzb.columns)}")

        # If both RRN and Refnum_F37 exist, prefer them (transaction reference keys)
        if 'RRN' in zzb.columns and 'Refnum_F37' in eth.columns:
            eth['_cmp_key'] = eth['Refnum_F37'].astype(str).str.strip()
            zzb['_cmp_key'] = zzb['RRN'].astype(str).str.strip()
            print('Using RRN <-> Refnum_F37 for comparison')
        else:
            # detect key if not provided
            if key is None:
                key_eth = _find_terminal_column(eth)
                key_zzb = _find_terminal_column(zzb)
            else:
                key_eth = key_zzb = key

            if not key_eth or not key_zzb:
                raise ValueError('Terminal id column not found in one or both files. Provide `key` parameter.')

            if key_eth not in eth.columns:
                raise ValueError(f'ETH file missing key column: {key_eth}')
            if key_zzb not in zzb.columns:
                raise ValueError(f'ZZB file missing key column: {key_zzb}')

            eth['_cmp_key'] = eth[key_eth].astype(str).str.strip()
            zzb['_cmp_key'] = zzb[key_zzb].astype(str).str.strip()
            print(f'Using columns {key_eth} and {key_zzb} for comparison')

        eth_keys = set(eth['_cmp_key'].dropna().unique())
        zzb_keys = set(zzb['_cmp_key'].dropna().unique())

        only_in_eth_keys = eth_keys - zzb_keys
        only_in_zzb_keys = zzb_keys - eth_keys
        matched_keys = eth_keys & zzb_keys

        only_in_eth_df = eth[eth['_cmp_key'].isin(only_in_eth_keys)].drop(columns=['_cmp_key'])
        only_in_zzb_df = zzb[zzb['_cmp_key'].isin(only_in_zzb_keys)].drop(columns=['_cmp_key'])
        matched_eth = eth[eth['_cmp_key'].isin(matched_keys)].drop(columns=['_cmp_key'])
        matched_zzb = zzb[zzb['_cmp_key'].isin(matched_keys)].drop(columns=['_cmp_key'])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            only_in_eth_df.to_excel(writer, sheet_name='only_in_eth', index=False)
            only_in_zzb_df.to_excel(writer, sheet_name='only_in_zzb', index=False)
            matched_eth.to_excel(writer, sheet_name='matched_eth', index=False)
            matched_zzb.to_excel(writer, sheet_name='matched_zzb', index=False)
        print(f"reconcile_and_get_excel_bytes: wrote sheets sizes: only_in_eth={only_in_eth_df.shape}, only_in_zzb={only_in_zzb_df.shape}, matched_eth={matched_eth.shape}, matched_zzb={matched_zzb.shape}")
        return output.getvalue()
    except Exception as e:
        import traceback
        print("Error in reconcile_and_get_excel_bytes:", str(e))
        print(traceback.format_exc())
        raise
