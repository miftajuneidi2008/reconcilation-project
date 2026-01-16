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
  ChevronDown,
} from "lucide-react";
import Navbar from "./Navbar";

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
  mismatches: PreviewRow[];
}

const reconOptions = [
  { value: "atm", label: "ATM Transactions" },
  { value: "tele", label: "Tele Birr Out going" },
  { value: "mpesa", label: "M Pesa Transactions" },
  { value: "tele-incoming", label: "Tele Birr Incoming" },
];
export default function Reconcile() {
  const [ethFile, setEthFile] = useState<File | null>(null);
  const [zzbFile, setZzbFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [reconType, setReconType] = useState<string>("");
  const [result, setResult] = useState<APIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_URL = "http://127.0.0.1:8080/api/v1";
  console.log("Selected Recon Type:", reconType);
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
    formData.append("recon_type", reconType);

    try {
      const response = await axios.post<APIResponse>(
        `${API_URL}/reconcile`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setResult(response.data);
      setReconType("");
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
    formData.append("recon_type", reconType);

    try {
      const response = await axios.post(
        `${API_URL}/reconcile/download`,
        formData,
        {
          responseType: "blob",
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

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
      setReconType("");
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Header */}
     
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* File Upload Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <UploadCloud className="text-teal-600" /> Upload Reconciliation
            Files
          </h2>
          <div className="mb-8 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Step 1: Select Reconciliation Category
            </label>
            <div className="relative">
              <select
                value={reconType}
                onChange={(e) => setReconType(e.target.value)}
                className="w-full appearance-none bg-white border border-slate-300 text-slate-700 py-3 px-4 pr-10 rounded-lg leading-tight focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all cursor-pointer"
              >
                <option value="" disabled>
                  Choose a category...
                </option>
                {reconOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                <ChevronDown className="w-5 h-5" />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* EthSwitch Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Partner File (Excel)
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
                ZamZam File (Excel)
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
              disabled={loading || reconType === ""}
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
              disabled={loading || reconType === ""}
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
                value={result.summary.MISSING_IN_PROVIDER || 0}
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
        {result &&(
          <Mismatched data={result.mismatches} />
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

interface DataRow {
  [key: string]: string | number | null;
}

function Mismatched({ data }: { data: DataRow[] }) {
   if (!data || data.length === 0) return null;

  // 1. Identify which keys have at least one valid value across all rows
  const allKeys = Object.keys(data[0]);
  
  const activeHeaders = allKeys.filter((key) => {
    return data.some((row) => {
      const val = row[key];
      return (
        val !== null && 
        val !== undefined && 
        val !== "" && 
        String(val).toLowerCase() !== "nan"
      );
    });
  });

  
  const formatHeader = (text: string) => {
    return text.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="mt-6 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
        <h3 className="font-semibold text-slate-700">Data Preview (Mismatches)</h3>
        <span className="text-xs font-medium bg-teal-100 text-teal-700 px-2 py-1 rounded">
          {activeHeaders.length} Columns Displayed
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-100 border-b border-slate-200">
              {activeHeaders.map((header) => (
                <th
                  key={header}
                  className="px-4 py-3 text-xs font-bold text-slate-600 uppercase tracking-wider whitespace-nowrap"
                >
                  {formatHeader(header)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.map((row, rowIndex) => (
              <tr 
                key={rowIndex} 
                className="hover:bg-slate-50 transition-colors odd:bg-white even:bg-slate-50/30"
              >
                {activeHeaders.map((header) => {
                  const value = row[header];
                  const isEmpty = value === "" || String(value).toLowerCase() === "nan";
                  
                  return (
                    <td 
                      key={header} 
                      className="px-4 py-3 text-sm text-slate-600 whitespace-nowrap"
                    >
                      {isEmpty ? (
                        <span className="text-slate-300">-</span>
                      ) : (
                        String(value)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}



