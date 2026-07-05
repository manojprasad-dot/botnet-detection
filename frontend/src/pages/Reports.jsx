import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import {
  FileText,
  Download,
  Plus,
  RefreshCw,
  Clock,
  FileSpreadsheet,
} from "lucide-react";
import { generateReport, getReports, downloadReport } from "../services/api";

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [reportType, setReportType] = useState("summary");
  const [reportFormat, setReportFormat] = useState("pdf");
  const [reportsLoading, setReportsLoading] = useState(false);

  const loadReportsList = async () => {
    try {
      const list = await getReports();
      setReports(list.reports || []);
    } catch (err) {
      console.error("Failed to load reports:", err);
    }
  };

  useEffect(() => {
    loadReportsList();
  }, []);

  const handleGenerateReport = async () => {
    setReportsLoading(true);
    try {
      await generateReport(reportType, reportFormat);
      await loadReportsList();
    } catch (err) {
      alert("Report generation failed: " + err.message);
    } finally {
      setReportsLoading(false);
    }
  };

  const handleDownloadReport = async (reportId, filename) => {
    try {
      const blob = await downloadReport(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Download failed: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">XDR EXECUTIVE REPORTING DESK</h2>
          <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">COMPLIANCE & AUDIT SHIELD</p>
        </div>
        <button
          onClick={loadReportsList}
          className="p-2 border border-[#1E293B] rounded-lg bg-[#0C1426] hover:bg-[#1E293B] text-white cursor-pointer transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Generation Controls */}
        <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 shadow-lg space-y-4">
          <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-4 block">
            GENERATE COMPLIANCE REPORT
          </span>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">REPORT SCOPE</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-white focus:outline-none"
              >
                <option value="summary">Network Threat Summary (Executive)</option>
                <option value="incidents">Alert Logs & Incident Details</option>
                <option value="devices">Device Inventory & Integrity status</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">OUTPUT FORMAT</label>
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value)}
                className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-white focus:outline-none"
              >
                <option value="pdf">PDF Document (Vector-styled)</option>
                <option value="csv">CSV Spreadsheet (Plain-text data)</option>
              </select>
            </div>

            <button
              onClick={handleGenerateReport}
              disabled={reportsLoading}
              className={`w-full py-2.5 rounded-lg font-orbitron font-bold text-xs tracking-wider transition-all flex items-center justify-center gap-2 ${
                reportsLoading
                  ? "bg-[#1E293B]/50 border border-[#1E293B] text-[#5A7090] cursor-not-allowed"
                  : "bg-[#FFB400] text-black hover:bg-[#FFB400]/80 cursor-pointer shadow-lg shadow-amber-500/10"
              }`}
            >
              <Plus className="h-4 w-4" />
              {reportsLoading ? "COMPILING REPORT..." : "RUN GENERATOR"}
            </button>
          </div>
        </div>

        {/* Generated Reports list */}
        <div className="lg:col-span-2 bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 shadow-lg">
          <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-4 block">
            EXPORTS ARCHIVE & HISTORY
          </span>

          <div className="divide-y divide-[#1E293B]/50 space-y-4 max-h-[400px] overflow-y-auto pr-1">
            {reports.length > 0 ? (
              reports.map((rep) => {
                const isPdf = (rep.format || "").toLowerCase() === "pdf";
                return (
                  <div key={rep.id} className="flex justify-between items-center text-xs pt-3">
                    <div className="flex gap-3">
                      <div className={`h-8 w-8 rounded flex items-center justify-center ${
                        isPdf ? "bg-[#FF355E]/10 text-[#FF355E]" : "bg-[#00E676]/10 text-[#00E676]"
                      }`}>
                        {isPdf ? <FileText className="h-4.5 w-4.5" /> : <FileSpreadsheet className="h-4.5 w-4.5" />}
                      </div>
                      <div>
                        <span className="font-bold text-white block truncate max-w-[250px]">{rep.filename}</span>
                        <div className="flex gap-2 text-[10px] text-[#5A7090] mt-0.5">
                          <span className="uppercase">{rep.report_type}</span>
                          <span>•</span>
                          <span>{new Date(rep.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDownloadReport(rep.id, rep.filename)}
                      className="p-2 border border-[#1E293B] hover:bg-[#1E293B] rounded text-white flex items-center gap-1.5 cursor-pointer font-orbitron text-[9px] font-bold tracking-wider transition-all"
                    >
                      <Download className="h-3.5 w-3.5" />
                      FETCH
                    </button>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-[#5A7090] py-20 text-xs">
                No reports compiled. Use the control panel to generate compliance archives.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
