import pandas as pd
import io
import re
from app.utils.excel_parser import load_excel_dynamic, clean_currency
import datetime

class ReconciliationService:
    
    def process_files(self, eth_content: bytes, zzb_content: bytes, recon_type: str = "atm"):
        recon_type = str(recon_type).lower().strip()

        if recon_type == "mpesa":
            eth_required = ['RECEIPT NO.', 'LINKED TRANSACTION ID', 'REASON TYPE'] 
            zzb_required = ['ZAMZAM_REF_NO', 'AMOUNT', 'CONVERSION_ID']
            left_key = 'Match_Key'
            right_key = 'Match_Key'
        elif recon_type == "tele":
            eth_required = ['ORDER_ID', 'AMOUNT', 'REF_NO'] 
            zzb_required = ['TRN_REF_NO', 'AMOUNT', 'TXNREF']
            left_key = 'Match_Key'
            right_key = 'Match_Key'
        # --- NEW SECTION FOR TELE-INCOMING ---
        elif recon_type == "tele-incoming":
            # Provider (Eth) has ORDER_ID, Bank (ZZB) has TELLEBIRR REF
            eth_required = ['ORDER_ID', 'AMOUNT', 'REF_NO']
            zzb_required = ['TELLEBIRR REF', 'AMOUNT', 'TRN_REF_NO']
            left_key = 'Match_Key'
            right_key = 'Match_Key'
        # --------------------------------------
        else:
            eth_required = ['REFNUM', 'AMOUNT', 'PAN']
            zzb_required = ['TRN_REF_NO', 'AMOUNT', 'RRN']
            left_key = 'RRN'
            right_key = 'Refnum_F37'

        
        df_eth = load_excel_dynamic(eth_content, eth_required, default_row=0)
        df_zzb = load_excel_dynamic(zzb_content, zzb_required, default_row=0)

        # 3. Standardize Columns
        self.rename_for_logic(df_eth, is_eth=True, recon_type=recon_type)
        self.rename_for_logic(df_zzb, is_eth=False, recon_type=recon_type)
 
        # 4. Data Cleaning
        if right_key in df_eth.columns:
            df_eth[right_key] = df_eth[right_key].astype(str).str.strip()
            df_eth = df_eth.drop_duplicates(subset=[right_key])
        
        if left_key in df_zzb.columns:
            df_zzb[left_key] = df_zzb[left_key].astype(str).str.strip()

        desc_col = 'Transaction_Description'
        if desc_col not in df_eth.columns:
            df_eth[desc_col] = recon_type.upper() + " Transaction"

        # 5. Perform the Merge
        try:
            merged_df = pd.merge(
                df_zzb, 
                df_eth, 
                left_on=left_key, 
                right_on=right_key, 
                how='left', 
                indicator=True
            )
        except KeyError as e:
            raise KeyError(f"Merge failed. Missing keys. ZZB: {df_zzb.columns.tolist()}, Provider: {df_eth.columns.tolist()}")

        # 6. Map Statuses
        merged_df['Recon_Status'] = merged_df['_merge'].map({
            'both': 'MATCHED',
            'left_only': 'MISSING_IN_PROVIDER', 
            'right_only': 'MISSING_IN_BANK'   
        }).astype(str)

        return merged_df

    def rename_for_logic(self, df, is_eth=False, recon_type="atm"):
        rename_map = {}
        for col in df.columns:
            upper_col = col.strip().upper()
            
            if recon_type == "mpesa":
                if is_eth:
                    if 'LINKED TRANSACTION ID' in upper_col: rename_map[col] = 'Match_Key'
                    elif 'REASON TYPE' in upper_col: rename_map[col] = 'Transaction_Description'
                    elif 'RECEIPT NO' in upper_col: rename_map[col] = 'Provider_Ref'
                else:
                    if 'CONVERSION_ID' in upper_col: rename_map[col] = 'Match_Key'
                    elif 'TRANSACTION_DESC' in upper_col: rename_map[col] = 'Transaction_Description'
            
            elif recon_type == "tele":
                if is_eth:
                    if 'ORDER_ID' in upper_col: rename_map[col] = 'Match_Key'
                    elif 'TRANSACTION_TYP' in upper_col: rename_map[col] = 'Transaction_Description'
                else:
                    if 'TXNREF' in upper_col: rename_map[col] = 'Match_Key'
                    elif 'TRANSACTION_DESC' in upper_col: rename_map[col] = 'Transaction_Description'

            # --- NEW MAPPING FOR TELE-INCOMING ---
            elif recon_type == "tele-incoming":
                if is_eth: # Telebirr File (Img 3)
                    if 'ORDER_ID' in upper_col: rename_map[col] = 'Match_Key'
                    elif 'TRANSACTION_TYPE' in upper_col: rename_map[col] = 'Transaction_Description'
                else: # Bank File (Img 2)
                    if 'TELLEBIRR REF' in upper_col: rename_map[col] = 'Match_Key'
                    elif 'TRANSACTION DESCRIPTION' in upper_col: rename_map[col] = 'Transaction_Description'
            # --------------------------------------
            
            else:
                if is_eth:
                    if 'REFNUM' in upper_col: rename_map[col] = 'Refnum_F37'
                    elif 'TRANSACTION_DESCRIPTION' in upper_col: rename_map[col] = 'Transaction_Description'
                    elif 'ISSUER' in upper_col: rename_map[col] = 'Issuer'
                    elif 'ACQUIRER' in upper_col: rename_map[col] = 'Acquirer'
                else:
                    if 'RRN' in upper_col: rename_map[col] = 'RRN'
                
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

    def generate_excel_report(self, merged_df, recon_type="atm"):
        output = io.BytesIO()
        
        # --- 1. DATA CLEANUP FOR EXCEL ---
        # Remove "UNNAMED" columns
        cols_to_keep = [c for c in merged_df.columns if "UNNAMED" not in str(c).upper()]
        df_to_export = merged_df[cols_to_keep].copy()

        # FIX: Convert 'category' columns to string first
        # This prevents the "Cannot setitem on a Categorical" error
        for col in df_to_export.select_dtypes(include=['category']).columns:
            df_to_export[col] = df_to_export[col].astype(str)

        # FIX: Convert 'datetime' columns to string
        for col in df_to_export.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df_to_export[col] = df_to_export[col].astype(str)
            
        # Now it is safe to handle NaNs and objects
        df_to_export = df_to_export.fillna("")
        
        # Double check remaining objects (like hidden timestamps in object columns)
        for col in df_to_export.select_dtypes(include=['object']).columns:
            if df_to_export[col].apply(lambda x: isinstance(x, (pd.Timestamp, datetime.date))).any():
                df_to_export[col] = df_to_export[col].astype(str)

        # Identify Provider Name for Labels
        provider_name = "EthSwitch"
        if "tele" in recon_type: provider_name = "Telebirr"
        elif "mpesa" in recon_type: provider_name = "M-Pesa"

        # --- 2. GENERATE WORKBOOK ---
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            
            # Dashboard Sheet
            summary_data = {
                'Metric': [
                    'Total ZamZam Transactions', 
                    f'Matched with {provider_name}', 
                    f'Missing in {provider_name} (Action Required)',
                    'Missing in Bank'
                ],
                'Count': [
                    len(df_to_export),
                    len(df_to_export[df_to_export['_merge'] == 'both']),
                    len(df_to_export[df_to_export['_merge'] == 'left_only']),
                    len(df_to_export[df_to_export['_merge'] == 'right_only'])
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Dashboard', index=False)

            # Dynamic Sheet Splitting
            if 'Transaction_Description' not in df_to_export.columns:
                df_to_export['Transaction_Description'] = recon_type.upper()

            transaction_descriptions = df_to_export['Transaction_Description'].unique()

            for description in transaction_descriptions:
                desc_str = str(description) if description else "General"
                short_description = self.abbreviate_description(desc_str)
                short_description = re.sub(r'[\\/*?:\[\]]', '', short_description)[:24]

                desc_df = df_to_export[df_to_export['Transaction_Description'] == description]

                if recon_type == "atm" and 'Issuer' in desc_df.columns and 'Acquirer' in desc_df.columns:
                    # ATM logic (keep existing split)
                    zzb_both = desc_df[(desc_df['Issuer'].astype(str).str.contains('ZamZam', case=False)) & (desc_df['Acquirer'].astype(str).str.contains('ZamZam', case=False))]
                    zzb_issue = desc_df[(desc_df['Issuer'].astype(str).str.contains('ZamZam', case=False)) & (~desc_df['Acquirer'].astype(str).str.contains('ZamZam', case=False))]
                    zzb_acquire = desc_df[(desc_df['Acquirer'].astype(str).str.contains('ZamZam', case=False)) & (~desc_df['Issuer'].astype(str).str.contains('ZamZam', case=False))]

                    if not zzb_issue.empty: zzb_issue.to_excel(writer, sheet_name=f'{short_description}-Issue', index=False)
                    if not zzb_acquire.empty: zzb_acquire.to_excel(writer, sheet_name=f'{short_description}-Acquire', index=False)
                    if not zzb_both.empty: zzb_both.to_excel(writer, sheet_name=f'{short_description}-Both', index=False)
                else:
                    # Simple sheet for Tele/Mpesa
                    sheet_name = f'{short_description}'[:31]
                    desc_df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Mismatches Sheet
            mismatches_df = df_to_export[df_to_export['_merge'] == 'left_only']
            if not mismatches_df.empty:
                mismatches_df.to_excel(writer, sheet_name='Action_Required', index=False)

        return output.getvalue()