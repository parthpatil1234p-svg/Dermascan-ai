import api from "./api";


export async function generateSkincareRoutine(uploadId) {
  const response = await api.post(`/skincare-routines/${encodeURIComponent(uploadId)}/generate`);
  return response.data;
}


export async function getSkincareRoutine(uploadId) {
  const response = await api.get(`/skincare-routines/${encodeURIComponent(uploadId)}`);
  return response.data;
}


export function getRoutineErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) return "Unable to reach the routine service. Check the backend connection and try again.";
  return "We could not safely generate the skincare routine.";
}
