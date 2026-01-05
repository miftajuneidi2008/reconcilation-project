import pandas as pd
import io
import re
from app.utils.excel_parser import load_excel_dynamic, clean_currency

class ReconciliationService:
    
    def process_files(self, eth_content: bytes, zzb_content: bytes):
        """
        Loads files, standardizes columns, and performs the Left Merge (ZamZam vs EthSwitch).
        """
        # 1. Ingest Data (Dynamic Header Detection)
        print("--- Processing EthSwitch File ---")
        # We look for specific columns to find the header
        df_eth = load_excel_dynamic(eth_content, ['REFNUM', 'AMOUNT', 'PAN'], default_row=3)
        
        print("--- Processing ZamZam File ---")
        # We look for specific columns to find the header
        df_zzb = load_excel_dynamic(zzb_content, ['TRN_REF_NO', 'AMOUNT', 'RRN'], default_row=8)

        # 2. Standardize Columns to match your specific script variables
        self.rename_for_logic(df_eth, is_eth=True)
        self.rename_for_logic(df_zzb, is_eth=False)

        # 3. Data Cleaning (As per your script)
        # Ensure RRN/Refnum are strings and strip spaces
        if 'Refnum_F37' in df_eth.columns:
            df_eth['Refnum_F37'] = df_eth['Refnum_F37'].astype(str).str.strip()
            # Drop duplicates in EthSwitch to prevent explosion during merge
            df_eth = df_eth.drop_duplicates(subset=['Refnum_F37'])
        
        if 'RRN' in df_zzb.columns:
            df_zzb['RRN'] = df_zzb['RRN'].astype(str).str.strip()

        # Ensure 'Transaction_Description' is string and fill NaN
        if 'Transaction_Description' in df_eth.columns:
            df_eth['Transaction_Description'] = df_eth['Transaction_Description'].astype(str).fillna('Unknown')
        else:
            # Create it if it doesn't exist so merge doesn't fail later
            df_eth['Transaction_Description'] = 'Unknown'

        # 4. Perform the Merge (Exact Logic: Left Join on RRN = Refnum_F37)
        # Left Join: Keep all ZamZam rows, find matching EthSwitch rows
        try:
            merged_df = pd.merge(
                df_zzb, 
                df_eth, 
                left_on='RRN', 
                right_on='Refnum_F37', 
                how='left', 
                indicator=True
            )
        except KeyError as e:
            raise KeyError(f"Merge failed. Missing columns. Found: ZZB={df_zzb.columns.tolist()}, ETH={df_eth.columns.tolist()}")

        # 5. Add Recon_Status for the Frontend Dashboard (JSON Preview)
        # We translate the '_merge' indicator to your statuses
        merged_df['Recon_Status'] = merged_df['_merge'].map({
            'both': 'MATCHED',
            'left_only': 'MISSING_IN_SWITCH', # Exists in ZZB (Left), not in ETH
            'right_only': 'MISSING_IN_BANK'   # Should not happen in Left Join
        }).astype(str)

        return merged_df

    def rename_for_logic(self, df, is_eth=False):
        """
        Maps the raw column names from the Excel to the specific variable names 
        used in your provided script (e.g., 'Refnum_F37', 'Issuer', etc.)
        """
        # Create a mapping of UpperCase Raw Name -> Your Script Name
        rename_map = {}
        for col in df.columns:
            upper_col = col.strip().upper()
            
            if is_eth:
                if 'REFNUM' in upper_col: rename_map[col] = 'Refnum_F37'
                elif 'TRANSACTION_DESCRIPTION' in upper_col or 'TRANSACTION DESCRIPTION' in upper_col: rename_map[col] = 'Transaction_Description'
                elif 'ISSUER' in upper_col: rename_map[col] = 'Issuer'
                elif 'ACQUIRER' in upper_col: rename_map[col] = 'Acquirer'
            else:
                if 'RRN' in upper_col: rename_map[col] = 'RRN'
                # Map ZamZam specific if needed
                
        df.rename(columns=rename_map, inplace=True)

    def abbreviate_description(self, description):
        """Your specific abbreviation logic"""
        abbreviations = {
            'Account2Account': 'A2A',
            'ATM CW Transaction Amount': 'ATM',
            'POS PUR THEM-ON-THEM': 'POS',
            'Purchase': 'POS',
            'Cash Withdrawal': 'ATM'
        }
        for long_text, short_text in abbreviations.items():
            if long_text in description:
                description = description.replace(long_text, short_text)
        return description

    def generate_excel_report(self, merged_df):
        output = io.BytesIO()

        # Get unique transaction descriptions (filling NaN for safety)
        if 'Transaction_Description' not in merged_df.columns:
             merged_df['Transaction_Description'] = 'Unknown'
             
        merged_df['Transaction_Description'] = merged_df['Transaction_Description'].fillna('Unknown')
        transaction_descriptions = merged_df['Transaction_Description'].unique()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            
            # --- 1. Dashboard Sheet (Optional, keeping it for summary) ---
            summary_data = {
                'Metric': ['Total ZamZam Transactions', 'Matched with EthSwitch', 'Mismatches (Missing in Switch)'],
                'Count': [
                    len(merged_df),
                    len(merged_df[merged_df['_merge'] == 'both']),
                    len(merged_df[merged_df['_merge'] == 'left_only'])
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Dashboard', index=False)

            # --- 2. The Logic from your script ---
            for description in transaction_descriptions:
                # Ensure string
                description = str(description)

                # Abbreviate
                short_description = self.abbreviate_description(description)

                # Sanitize for Excel (Remove / \ ? * : [ ])
                short_description = re.sub(r'[\\/*?:\[\]]', '', short_description)

                # Limit length (24 chars as per your script)
                short_description = short_description[:24]

                # Filter Data
                desc_df = merged_df[merged_df['Transaction_Description'] == description]

                # Check if Issuer/Acquirer columns exist (if not, we can't categorize)
                if 'Issuer' in desc_df.columns and 'Acquirer' in desc_df.columns:
                    # Logic: ZamZam Bank vs Others
                    # Note: Using str.contains because sometimes it might be "ZamZam Bank " (with space)
                    zzb_both = desc_df[
                        (desc_df['Issuer'].astype(str).str.contains('ZamZam', case=False)) & 
                        (desc_df['Acquirer'].astype(str).str.contains('ZamZam', case=False))
                    ]
                    zzb_issue = desc_df[
                        (desc_df['Issuer'].astype(str).str.contains('ZamZam', case=False)) & 
                        (~desc_df['Acquirer'].astype(str).str.contains('ZamZam', case=False))
                    ]
                    zzb_acquire = desc_df[
                        (desc_df['Acquirer'].astype(str).str.contains('ZamZam', case=False)) & 
                        (~desc_df['Issuer'].astype(str).str.contains('ZamZam', case=False))
                    ]

                    # Write Sheets
                    if not zzb_issue.empty:
                        zzb_issue.to_excel(writer, sheet_name=f'{short_description}-zzb-Issue', index=False)
                    if not zzb_acquire.empty:
                        zzb_acquire.to_excel(writer, sheet_name=f'{short_description}-zzb-Acquire', index=False)
                    if not zzb_both.empty:
                        zzb_both.to_excel(writer, sheet_name=f'{short_description}-zzb-Both', index=False)
                else:
                    # If columns missing, just dump the data
                    sheet_name = f'{short_description}-Data'[:31]
                    desc_df.to_excel(writer, sheet_name=sheet_name, index=False)

            # --- 3. Mismatches Sheet ---
            mismatches_df = merged_df[merged_df['_merge'] == 'left_only']
            if not mismatches_df.empty:
                mismatches_df.to_excel(writer, sheet_name='Mismatches', index=False)

        return output.getvalue()