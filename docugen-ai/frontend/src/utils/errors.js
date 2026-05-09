export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(" ");
  }
  if (typeof detail === "string") {
    return detail;
  }
  return error?.message || fallback;
}
