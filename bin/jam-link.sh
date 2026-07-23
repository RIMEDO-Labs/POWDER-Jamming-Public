#!/bin/bash

UPDATE_ATTENS_SCRIPT=/local/repository/bin/update-attens

UE=$1
RU=$2
PERIOD_SEC=${3:-0.3}
LOW=0
HIGH=60

usage() {
    echo "Usage:"
    echo "  toggle-atten <ue1|ue2> <ru1|ru2> [period_in_seconds]"
    echo "Example:"
    echo "  toggle-atten ue1 ru1 0.5   # change every 500 ms"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

case "${RU}${UE}" in
    ru1ue1) GROUP="ru1ue1" ;;
    ru2ue1) GROUP="ru2ue1" ;;
    ru1ue2) GROUP="ru1ue2" ;;
    ru2ue2) GROUP="ru2ue2" ;;
    *) echo "Invalid UE or RU"; exit 1 ;;
esac

echo "Toggling $GROUP between ${LOW} dB and ${HIGH} dB every ${PERIOD_SEC} s"
echo "Press Ctrl+C to stop."

while true; do
    $UPDATE_ATTENS_SCRIPT "$GROUP" $LOW
    sleep "$PERIOD_SEC"

    $UPDATE_ATTENS_SCRIPT "$GROUP" $HIGH
    sleep "$PERIOD_SEC"
done