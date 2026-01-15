from fastapi import FastAPI, UploadFile, File, HTTPException,Form 
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.services.reconciliation import ReconciliationService
import io
import pandas as pd
import traceback 
import json
import datetime

app = FastAPI(title="ZamZam Bank ARS Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

recon_service = ReconciliationService()

@app.post("/api/v1/reconcile") 
async def reconcile_process(
    eth_file: UploadFile = File(...),
    zzb_file: UploadFile = File(...),
    recon_type: str = Form("atm")              
):
    try:
        recon_type = recon_type.lower().strip()
        eth_content = await eth_file.read()
        zzb_content = await zzb_file.read()

        result_df = recon_service.process_files(eth_content, zzb_content, recon_type)  

        # --- UPDATED ROBUST CLEANUP START ---
        
        # 1. Convert specific date/category dtypes to string
        date_cols = result_df.select_dtypes(include=['datetime', 'datetimetz', 'timedelta', 'category']).columns
        for col in date_cols:
            result_df[col] = result_df[col].astype(str)
            
        # 2. Fix 'Object' columns that might contain hidden datetime objects
        # This is common in M-Pesa files where some cells are empty and others are dates
        for col in result_df.select_dtypes(include=['object']).columns:
            if result_df[col].apply(lambda x: isinstance(x, (pd.Timestamp, datetime.date))).any():
                result_df[col] = result_df[col].astype(str)

        # 3. Handle NaN and Infinite values
        result_df_clean = result_df.fillna("").replace([float('inf'), float('-inf')], "")
        
        # 4. Filter for mismatches list (as we discussed before)
        mismatches_df = result_df_clean[result_df_clean['Recon_Status'] != 'MATCHED']
        mismatches_list = mismatches_df.to_dict(orient='records')

        summary = result_df_clean['Recon_Status'].value_counts().to_dict()
        preview = result_df_clean.head(10).to_dict(orient='records')
        # --- UPDATED ROBUST CLEANUP END ---

        return JSONResponse(content={
            "status": "success",
            "summary": summary,
            "preview_data": preview,
            "mismatches": mismatches_list
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reconcile/download")
async def reconcile_download(
    eth_file: UploadFile = File(...),
    zzb_file: UploadFile = File(...),
    recon_type: str = Form("atm") 
): 
    try:
        recon_type = recon_type.lower().strip()
        eth_content = await eth_file.read()
        zzb_content = await zzb_file.read()

        # Pass recon_type to process_files
        result_df = recon_service.process_files(eth_content, zzb_content, recon_type)
        
        # Pass recon_type to generate_excel_report for dynamic labeling
        excel_data = recon_service.generate_excel_report(result_df, recon_type)

        filename = f"{recon_type}_reconciliation_report.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"} 
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))