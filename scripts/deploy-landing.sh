#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-mission-control-v2-aivira}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-clawmetry-landing}"
SOURCE_DIR="${SOURCE_DIR:-clawmetry-landing}"

echo "Deploying ${SERVICE_NAME} from ${SOURCE_DIR}"
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud is not installed or not in PATH" >&2
  exit 1
fi

if [ ! -d "${SOURCE_DIR}" ]; then
  echo "ERROR: source directory '${SOURCE_DIR}' not found" >&2
  exit 1
fi

gcloud run deploy "${SERVICE_NAME}" \
  --source "${SOURCE_DIR}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated

# Org-policy friendly public mode (works when allUsers IAM binding is blocked).
gcloud run services update "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --platform managed \
  --no-invoker-iam-check

URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --format='value(status.url)')"

echo ""
echo "Deploy complete."
echo "Service URL: ${URL}"
