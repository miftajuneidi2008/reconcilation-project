import pandas as pd
import os
import glob

# Install xlsxwriter if it is not already installed
try:
    import xlsxwriter
except ImportError:
    !pip install xlsxwriter
    import xlsxwriter

# Constants for header row numbers
ETH_HEADER_ROW = 3  # 4th row (0-indexed)
ZZB_HEADER_ROW = 8  # 9th row (0-indexed)

# Function to find the file based on the keyword in the filename
def find_file(keyword):
    files = glob.glob(f'*{keyword}*.xls*') # Modified to find both .xls and .xlsx
    if files:
        return files[0]
    else:
        raise FileNotFoundError(f"No file containing '{keyword}' found.")

# Read the data from the Excel files
try:
    eth_file = find_file('ethswitch')
    zzb_file = find_file('zamzam')

    eth_df = pd.read_excel(eth_file, header=ETH_HEADER_ROW)
    zzb_df = pd.read_excel(zzb_file, header=ZZB_HEADER_ROW)
except FileNotFoundError as e:
    print(e)
    raise

# Print column names for debugging
# print("Columns in eth_df:", eth_df.columns)
# print("Columns in zzb_df:", zzb_df.columns)

# Remove any leading or trailing spaces from column names
eth_df.columns = eth_df.columns.str.strip()
zzb_df.columns = zzb_df.columns.str.strip()

# Ensure 'Transaction_Description' is treated as a string and fill NaN values
eth_df['Transaction_Description'] = eth_df['Transaction_Description'].astype(str).fillna('Unknown')

# Function to abbreviate long transaction descriptions
def abbreviate_description(description):
    # Example abbreviations
    abbreviations = {
        'Account2Account': 'A2A',
        'ATM CW Transaction Amount': 'ATM',
        'POS PUR THEM-ON-THEM': 'POS',
        # Add more abbreviations as necessary
    }
    for long, short in abbreviations.items():
        description = description.replace(long, short)
    return description

# Perform the merge (like VLOOKUP)
try:
    merged_df = pd.merge(zzb_df, eth_df, left_on='RRN', right_on='Refnum_F37', how='left', indicator=True)

    # Get unique transaction descriptions
    transaction_descriptions = merged_df['Transaction_Description'].unique()

    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter('reconciliation_output.xlsx', engine='xlsxwriter') as writer:
        for description in transaction_descriptions:
            # Ensure the description is a string (in case there are any non-string values)
            description = str(description)

            # Abbreviate the description if necessary
            short_description = abbreviate_description(description)

            # Ensure sheet name length is within limits
            short_description = short_description[:24]  # Reserve space for suffix

            # Filter the data based on 'Transaction_Description'
            desc_df = merged_df[merged_df['Transaction_Description'] == description]

            # Further filter based on Issuer and Acquirer
            zzb_both = desc_df[(desc_df['Issuer'] == 'ZamZam Bank') & (desc_df['Acquirer'] == 'ZamZam Bank')]
            zzb_issue = desc_df[(desc_df['Issuer'] == 'ZamZam Bank') & (desc_df['Acquirer'] != 'ZamZam Bank')]
            zzb_acquire = desc_df[(desc_df['Acquirer'] == 'ZamZam Bank') & (desc_df['Issuer'] != 'ZamZam Bank')]

            # Check if the DataFrames are not empty before writing to Excel sheets
            if not zzb_issue.empty:
                zzb_issue.to_excel(writer, sheet_name=f'{short_description}-zzb-Issue', index=False)
            if not zzb_acquire.empty:
                zzb_acquire.to_excel(writer, sheet_name=f'{short_description}-zzb-Acquire', index=False)
            if not zzb_both.empty:
                zzb_both.to_excel(writer, sheet_name=f'{short_description}-zzb-Both', index=False)

        # Filter mismatched records
        mismatches_df = merged_df[merged_df['_merge'] == 'left_only']

        # Write mismatches to a separate sheet
        if not mismatches_df.empty:
            mismatches_df.to_excel(writer, sheet_name='Mismatches', index=False)

    print("Reconciliation data has been saved to 'reconciliation_output.xlsx'.")
except KeyError as e:
    print(f"KeyError: {e}. Please check that the specified columns exist in both DataFrames.")
except ValueError as e:
    print(f"ValueError: {e}. Sheet name might be too long or contain invalid characters.")
except AttributeError as e:
    print(f"AttributeError: {e}. Please check that the 'Transaction_Description' column is properly formatted.")