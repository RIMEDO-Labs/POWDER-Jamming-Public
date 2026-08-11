#!/bin/bash

UPDATE_ATTENS_SCRIPT=/local/repository/bin/update-attens

UE=$1
RU=$2

TOGGLE_PERIOD=${3:-1}       # zmiana co ile sekund
EPISODES=${4:-3}            # liczba epizodów
EPISODE_DURATION=${5:-20}   # długość jednego epizodu [s]
BREAK_DURATION=${6:-10}     # przerwa między epizodami [s]
MAX_ATTEN=${7:-60}           # maksymalne tłumienie [dB]

LOW=0
HIGH=$MAX_ATTEN

usage() {
    echo "Usage:"
    echo "  toggle-atten <ue1|ue2> <ru1|ru2> [toggle_period] [episodes] [episode_duration] [break_duration] [max_atten]"
    echo
    echo "Example:"
    echo "  toggle-atten ue1 ru1 1 3 20 10 40"
    echo "    -> 3 epizody,"
    echo "       każdy trwa 20 s,"
    echo "       przełączanie co 1 s,"
    echo "       10 s przerwy między epizodami,"
    echo "       maksymalne tłumienie 40 dB."
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

cleanup() {
    echo
    echo "Restoring attenuation to ${LOW} dB..."
    $UPDATE_ATTENS_SCRIPT "$GROUP" $LOW
    exit
}

trap cleanup INT TERM EXIT

echo "==========================================="
echo "Group             : $GROUP"
echo "Episodes          : $EPISODES"
echo "Episode duration  : ${EPISODE_DURATION}s"
echo "Toggle period     : ${TOGGLE_PERIOD}s"
echo "Break duration    : ${BREAK_DURATION}s"
echo "Max attenuation   : ${MAX_ATTEN} dB"
echo "==========================================="

for ((ep=1; ep<=EPISODES; ep++)); do

    echo
    echo "=== Episode $ep/$EPISODES ==="

    elapsed=0
    state=$LOW

    while (( $(echo "$elapsed < $EPISODE_DURATION" | bc -l) )); do

        $UPDATE_ATTENS_SCRIPT "$GROUP" $state

        if [ "$state" -eq "$LOW" ]; then
            state=$HIGH
        else
            state=$LOW
        fi

        sleep "$TOGGLE_PERIOD"

        elapsed=$(echo "$elapsed + $TOGGLE_PERIOD" | bc)
    done

    $UPDATE_ATTENS_SCRIPT "$GROUP" $LOW

    if [ "$ep" -lt "$EPISODES" ]; then
        echo "Waiting ${BREAK_DURATION}s before next episode..."
        sleep "$BREAK_DURATION"
    fi

done

echo
echo "All episodes completed."

cleanup