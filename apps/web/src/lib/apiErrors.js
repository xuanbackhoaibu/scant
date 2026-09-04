function formatPath(loc) {
  return Array.isArray(loc) ? loc.filter((item) => item !== "body").join(".") : "";
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);

  if (Array.isArray(value)) {
    return value.map(formatValue).filter(Boolean).join("; ");
  }

  if (typeof value === "object") {
    if (typeof value.message === "string") {
      const rest = Object.entries(value)
        .filter(([key]) => key !== "message")
        .map(([key, nestedValue]) => `${key}: ${formatValue(nestedValue)}`)
        .filter(Boolean)
        .join("; ");
      return rest ? `${value.message}; ${rest}` : value.message;
    }

    if (typeof value.msg === "string") {
      const path = formatPath(value.loc);
      return path ? `${path}: ${value.msg}` : value.msg;
    }

    return Object.entries(value)
      .map(([key, nestedValue]) => `${key}: ${formatValue(nestedValue)}`)
      .filter(Boolean)
      .join("; ");
  }

  return String(value);
}

export function formatApiErrorMessage(data, fallback = "An error occurred") {
  const detail = data && typeof data === "object" && "detail" in data ? data.detail : data;
  return formatValue(detail) || fallback;
}

export function formatUnknownError(error, fallback = "An error occurred") {
  if (!error) return fallback;
  if (typeof error === "string") return error;

  if (error instanceof Error) {
    return formatValue(error.message) || fallback;
  }

  if (typeof error === "object" && "message" in error) {
    return formatValue(error.message) || formatApiErrorMessage(error, fallback);
  }

  return formatApiErrorMessage(error, fallback);
}
