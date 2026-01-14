"use client";

import { useState } from "react";
import axios from "axios";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle,
  AlertTriangle,
  Download,
  BarChart3,
  Loader2,
} from "lucide-react";

// Define Types for the API Response
interface Summary {
  [key: string]: number;
}

interface PreviewRow {
  [key: string]: string | number | null;
}

interface APIResponse {
  status: string;
  summary: Summary;
  preview_data: PreviewRow[];
}

export default function Reconcile() {
  const [ethFile, setEthFile] = useState<File | null>(null);
  const [zzbFile, setZzbFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<APIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_URL = "http://127.0.0.1:8080/api/v1/reconcile";

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    type: "eth" | "zzb"
  ) => {
    if (e.target.files && e.target.files[0]) {
      if (type === "eth") setEthFile(e.target.files[0]);
      else setZzbFile(e.target.files[0]);
    }
  };

  const validateFiles = () => {
    if (!ethFile || !zzbFile) {
      setError("Please select both files before proceeding.");
      return false;
    }
    setError(null);
    return true;
  };

  const handlePreview = async () => {
    if (!validateFiles()) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("eth_file", ethFile as Blob);
    formData.append("zzb_file", zzbFile as Blob);

    try {
      const response = await axios.post<APIResponse>(
        `${API_URL}`, 
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(response.data);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(
          err.response?.data?.detail || "Failed to connect to the server."
        );
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!validateFiles()) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("eth_file", ethFile as Blob);
    formData.append("zzb_file", zzbFile as Blob);

    try {
      const response = await axios.post(`${API_URL}/download`, formData, {
        responseType: "blob",
        headers: { "Content-Type": "multipart/form-data" },
      });

      // Create a link to download the file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `Reconciliation_Report_${new Date().toISOString().slice(0, 10)}.xlsx`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: unknown) {
      console.log(err);
      setError("Failed to download the report. Check the file formats.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Header */}
      <div className="bg-teal-700 text-white py-6 shadow-md">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg">
              {/* Simple Logo Placeholder */}
              <BarChart3 className="text-teal-700 w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">ZamZam Bank ARS</h1>
              <p className="text-teal-100 text-sm">
                Automated Reconciliation System - Phase 1
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* File Upload Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <UploadCloud className="text-teal-600" /> Upload Reconciliation
            Files
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* EthSwitch Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                EthSwitch File (Excel)
              </label>
              <div
                className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-colors ${
                  ethFile
                    ? "border-teal-500 bg-teal-50"
                    : "border-slate-300 hover:border-teal-400"
                }`}
              >
                <input
                  type="file"
                  accept=".xlsx, .xls"
                  onChange={(e) => handleFileChange(e, "eth")}
                  className="hidden"
                  id="ethInput"
                />
                <label
                  htmlFor="ethInput"
                  className="cursor-pointer text-center"
                >
                  <FileSpreadsheet
                    className={`w-10 h-10 mb-2 mx-auto ${
                      ethFile ? "text-teal-600" : "text-slate-400"
                    }`}
                  />
                  <span className="text-sm text-slate-600">
                    {ethFile ? ethFile.name : "Click to browse"}
                  </span>
                </label>
              </div>
            </div>

            {/* ZamZam Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                ZamZam Ledger (Excel)
              </label>
              <div
                className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-colors ${
                  zzbFile
                    ? "border-teal-500 bg-teal-50"
                    : "border-slate-300 hover:border-teal-400"
                }`}
              >
                <input
                  type="file"
                  accept=".xlsx, .xls"
                  onChange={(e) => handleFileChange(e, "zzb")}
                  className="hidden"
                  id="zzbInput"
                />
                <label
                  htmlFor="zzbInput"
                  className="cursor-pointer text-center"
                >
                  <FileSpreadsheet
                    className={`w-10 h-10 mb-2 mx-auto ${
                      zzbFile ? "text-teal-600" : "text-slate-400"
                    }`}
                  />
                  <span className="text-sm text-slate-600">
                    {zzbFile ? zzbFile.name : "Click to browse"}
                  </span>
                </label>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> {error}
            </div>
          )}

          <div className="mt-8 flex gap-4">
            <button
              onClick={handlePreview}
              disabled={loading}
              className="flex-1 bg-teal-600 hover:bg-teal-700 text-white py-3 px-6 rounded-lg font-medium flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="animate-spin" />
              ) : (
                <BarChart3 className="w-5 h-5" />
              )}
              Analyze & Preview
            </button>

            <button
              onClick={handleDownload}
              disabled={loading}
              className="flex-1 bg-slate-800 hover:bg-slate-900 text-white py-3 px-6 rounded-lg font-medium flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="animate-spin" />
              ) : (
                <Download className="w-5 h-5" />
              )}
              Download Report
            </button>
          </div>
        </div>

        {/* Results Section */}
        {result && (
          <div className="mt-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-lg font-semibold mb-4">Analysis Summary</h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <SummaryCard
                title="Total Matched"
                value={result.summary.MATCHED || 0}
                color="bg-green-100 text-green-800 border-green-200"
                icon={<CheckCircle className="w-5 h-5" />}
              />
              <SummaryCard
                title="Missing in Bank"
                value={result.summary.MISSING_IN_BANK || 0}
                color="bg-orange-100 text-orange-800 border-orange-200"
                icon={<AlertTriangle className="w-5 h-5" />}
              />
              <SummaryCard
                title="Missing in Switch"
                value={result.summary.MISSING_IN_SWITCH || 0}
                color="bg-red-100 text-red-800 border-red-200"
                icon={<AlertTriangle className="w-5 h-5" />}
              />
              <SummaryCard
                title="Total Transactions"
                value={Object.values(result.summary).reduce((a, b) => a + b, 0)}
                color="bg-blue-100 text-blue-800 border-blue-200"
                icon={<FileSpreadsheet className="w-5 h-5" />}
              />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

function SummaryCard({
  title,
  value,
  color,
  icon,
}: {
  title: string;
  value: number;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      className={`p-5 rounded-lg border ${color} flex items-center justify-between`}
    >
      <div>
        <p className="text-sm font-medium opacity-80">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </div>
      <div className="opacity-80">{icon}</div>
    </div>
  );
}
