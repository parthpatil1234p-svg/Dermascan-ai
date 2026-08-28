import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import {
  archiveFinalReport,
  exportFinalReportPdf,
  generateFinalReport,
  getFinalReport,
  getFinalReportErrorMessage,
  getLatestFinalReport,
  getUserReports,
  regenerateFinalReport,
} from "../services/finalReportService";


const FinalReportContext = createContext(null);


export function FinalReportProvider({ children }) {
  const [finalReport, setFinalReport] = useState(null);
  const [reportHistory, setReportHistory] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");
  const requestRef = useRef(null);

  const generate = useCallback(async (uploadId, force = false) => {
    if (requestRef.current) return requestRef.current;
    setIsGenerating(true);
    setGenerationProgress(10);
    setError("");
    const timer = window.setInterval(() => setGenerationProgress((value) => Math.min(94, value + 9)), 420);
    const request = (force ? regenerateFinalReport(uploadId) : generateFinalReport(uploadId))
      .then((result) => { setGenerationProgress(100); return result; })
      .catch((requestError) => { setError(getFinalReportErrorMessage(requestError)); throw requestError; })
      .finally(() => { window.clearInterval(timer); setIsGenerating(false); requestRef.current = null; });
    requestRef.current = request;
    return request;
  }, []);

  const loadReport = useCallback(async (reportId) => {
    setIsLoading(true); setError("");
    try { const result = await getFinalReport(reportId); setFinalReport(result); return result; }
    catch (requestError) { setError(getFinalReportErrorMessage(requestError)); throw requestError; }
    finally { setIsLoading(false); }
  }, []);
  const loadLatest = useCallback(async (uploadId) => {
    setIsLoading(true); setError("");
    try { const result = await getLatestFinalReport(uploadId); setFinalReport(result); return result; }
    catch (requestError) { setError(getFinalReportErrorMessage(requestError)); throw requestError; }
    finally { setIsLoading(false); }
  }, []);
  const loadHistory = useCallback(async (filters = {}) => {
    setIsLoading(true); setError("");
    try { const result = await getUserReports(filters); setReportHistory(result.reports); setPagination(result.pagination); return result; }
    catch (requestError) { setError(getFinalReportErrorMessage(requestError)); throw requestError; }
    finally { setIsLoading(false); }
  }, []);
  const archive = useCallback(async (reportId) => {
    try { const result = await archiveFinalReport(reportId); setReportHistory((items) => items.filter((item) => item.final_report_id !== reportId)); return result; }
    catch (requestError) { setError(getFinalReportErrorMessage(requestError)); throw requestError; }
  }, []);
  const exportPdf = useCallback(async (reportId, privacyMode) => {
    setIsExporting(true); setError("");
    try { await exportFinalReportPdf(reportId, privacyMode); }
    catch (requestError) { setError(getFinalReportErrorMessage(requestError)); throw requestError; }
    finally { setIsExporting(false); }
  }, []);
  const value = useMemo(() => ({ finalReport, reportHistory, pagination, isGenerating, generationProgress, isLoading, isExporting, error, generate, loadReport, loadLatest, loadHistory, archive, exportPdf }), [finalReport, reportHistory, pagination, isGenerating, generationProgress, isLoading, isExporting, error, generate, loadReport, loadLatest, loadHistory, archive, exportPdf]);
  return <FinalReportContext.Provider value={value}>{children}</FinalReportContext.Provider>;
}


export function useFinalReport() {
  const value = useContext(FinalReportContext);
  if (!value) throw new Error("useFinalReport must be used inside FinalReportProvider");
  return value;
}
