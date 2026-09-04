export const AUTO_JOB_STATE_KEY = "ai_report_studio:auto_job_state";

const IN_FLIGHT_STATUSES = new Set(["queued", "running", "paused"]);

/**
 * @typedef {Object} AutoJobSnapshotInput
 * @property {string} jobId
 * @property {string | null} [reportId]
 * @property {string} projectType
 * @property {string} status
 * @property {number} [progress]
 * @property {string} [statusMessage]
 */

export function isAutoJobInFlight(status) {
  return IN_FLIGHT_STATUSES.has(String(status || "").toLowerCase());
}

export function canSafelySwitchAutoContext(status) {
  return !isAutoJobInFlight(status);
}

export function shouldRestoreAutoJob(value) {
  return Boolean(value?.jobId && isAutoJobInFlight(value.status));
}

/**
 * @param {AutoJobSnapshotInput} input
 */
export function buildAutoJobSnapshot({
  jobId,
  reportId = null,
  projectType,
  status,
  progress = 0,
  statusMessage = "",
}) {
  return {
    storageKey: AUTO_JOB_STATE_KEY,
    value: {
      jobId,
      reportId,
      projectType,
      status,
      progress,
      statusMessage,
    },
  };
}
