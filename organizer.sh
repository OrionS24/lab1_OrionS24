#!/usr/bin/env bash

set -euo pipefail

GRADES_FILE="grades.csv"
ARCHIVE_DIR="archive"
LOG_FILE="organizer.log"

if [ ! -d "$ARCHIVE_DIR" ]; then
    mkdir -p "$ARCHIVE_DIR"
    echo "[INFO]  Created archive directory: ./${ARCHIVE_DIR}/"
else
    echo "[INFO]  Archive directory already exists: ./${ARCHIVE_DIR}/"
fi

if [ ! -f "$GRADES_FILE" ]; then
    echo "[ERROR] '${GRADES_FILE}' not found in the current directory."
    echo "        Nothing to archive. Exiting."
    exit 1
fi

if [ ! -s "$GRADES_FILE" ]; then
    echo "[WARN]  '${GRADES_FILE}' is empty — nothing meaningful to archive."
    echo "        Skipping archival. The file remains in place."
    exit 0
fi

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
ARCHIVED_NAME="grades_${TIMESTAMP}.csv"

echo "[INFO]  Timestamp generated: ${TIMESTAMP}"

mv "$GRADES_FILE" "${ARCHIVE_DIR}/${ARCHIVED_NAME}"
echo "[INFO]  Archived: '${GRADES_FILE}' → './${ARCHIVE_DIR}/${ARCHIVED_NAME}'"

touch "$GRADES_FILE"
echo "[INFO]  Created fresh '${GRADES_FILE}' — ready for the next batch."

LOG_ENTRY="[${TIMESTAMP}] original=${GRADES_FILE} | archived=${ARCHIVE_DIR}/${ARCHIVED_NAME}"
echo "$LOG_ENTRY" >> "$LOG_FILE"
echo "[INFO]  Log entry written to '${LOG_FILE}'."

echo ""
echo " Archival complete."
echo "   Original file : ${GRADES_FILE} (fresh copy ready)"
echo "   Archived copy : ./${ARCHIVE_DIR}/${ARCHIVED_NAME}"
echo "   Log file      : ./${LOG_FILE}"
