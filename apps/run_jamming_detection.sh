#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

python3 jamming_detector.py | while read -r line; do

    echo "$line"

    if [[ "$line" == "JAMMING_STATUS=1" ]]; then
        echo "========================================"
        echo "!!! JAMMING DETECTED !!!"
        echo "========================================"

        # Tutaj później możemy zrobić np.:
        # /local/repository/bin/something.sh
    fi

done