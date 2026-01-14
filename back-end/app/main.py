from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.services.reconciliation import ReconciliationService
import io
import pandas as pd
import traceback 
import json

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
    zzb_file: UploadFile = File(...)
):
    try:
        eth_content = await eth_file.read()
        zzb_content = await zzb_file.read()

        result_df = recon_service.process_files(eth_content, zzb_content)  

        # Categorical and NaN Fix
        for col in result_df.select_dtypes(include=['category']).columns:
            result_df[col] = result_df[col].astype(str)
        
        for col in result_df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            result_df[col] = result_df[col].astype(str) 

        result_df_clean = result_df.fillna("")
        
        summary = result_df_clean['Recon_Status'].value_counts().to_dict()
        preview = result_df_clean.head(10).to_dict(orient='records')

        return JSONResponse(content={
            "status": "success",
            "summary": summary,
            "preview_data": preview
           
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reconcile/download")
async def reconcile_download(
    eth_file: UploadFile = File(...),
    zzb_file: UploadFile = File(...)
): 
    try:
        eth_content = await eth_file.read()
        zzb_content = await zzb_file.read()

        result_df = recon_service.process_files(eth_content, zzb_content)
        excel_data = recon_service.generate_excel_report(result_df)

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=reconciliation_report.xlsx"} 
        )

    except Exception as e:
        # This will now show the REAL error in your terminal
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))