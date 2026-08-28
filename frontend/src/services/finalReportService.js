import api from "./api";


export async function generateFinalReport(uploadId) {
  const response = await api.post(`/final-reports/${encodeURIComponent(uploadId)}/generate`);
  return response.data;
}


export async function regenerateFinalReport(uploadId) {
  const response = await api.post(`/final-reports/${encodeURIComponent(uploadId)}/regenerate`);
  return response.data;
}


export async function getFinalReport(finalReportId) {
  const response = await api.get(`/final-reports/${encodeURIComponent(finalReportId)}`);
  return response.data;
}


export async function getLatestFinalReport(uploadId) {
  const response = await api.get(`/final-reports/by-upload/${encodeURIComponent(uploadId)}/latest`);
  return response.data;
}


export async function getUserReports(filters = {}) {
  const response = await api.get("/final-reports", { params: filters });
  return response.data;
}


export async function archiveFinalReport(finalReportId) {
  const response = await api.delete(`/final-reports/${encodeURIComponent(finalReportId)}`);
  return response.data;
}


export async function exportFinalReportPdf(finalReportId, privacyMode) {
  const response = await api.post(
    `/final-reports/${encodeURIComponent(finalReportId)}/export/pdf`,
    { privacy_mode: privacyMode },
    { responseType: "blob" },
  );
  const contentType = response.headers["content-type"] || "";
  if (!contentType.toLowerCase().startsWith("application/pdf")) {
    throw new Error("The server returned an unexpected export format.");
  }
  const objectUrl = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = `DermaScan-${finalReportId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}


export function getFinalReportErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (error instanceof Error && error.message.includes("unexpected export")) return error.message;
  if (!error?.response) return "Unable to reach the final report service. Check the backend connection and try again.";
  return "We could not safely complete this report request.";
}
