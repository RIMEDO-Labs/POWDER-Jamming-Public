#!/bin/bash

set -u

UPDATE_ATTENS="/local/repository/bin/update-attens"

UE="${1:-ue1}"
TOGGLE_PERIOD="${2:-10}"
EPISODES="${3:-3}"
EPISODE_DURATION="${4:-20}"

# update-attens adds 30 dB internally.
# Therefore:
# 60 -> 90 dB actual attenuation
# 30 -> 60 dB actual attenuation

OFF_ATTEN=60
ON_ATTEN=30

case "$UE" in
    ue1)
        GROUP="n300ue1"
        ;;
    ue2)
        GROUP="n300ue2"
        ;;
    *)
        echo "Usage:"
        echo "  $0 <ue1|ue2> [toggle_period] [episodes] [episode_duration]"
        echo
        echo "Example:"
        echo "  $0 ue1 10 3 20"
        exit 1
        ;;
esac


cleanup()
{
    echo
    echo "Restoring N300 path attenuation..."
    "$UPDATE_ATTENS" "$GROUP" "$OFF_ATTEN" 2>/dev/null || true
}

trap cleanup EXIT INT TERM


echo "=============================================="
echo " N300 interference experiment"
echo "=============================================="
echo " UE                : $UE"
echo " Group             : $GROUP"
echo " Toggle period     : ${TOGGLE_PERIOD}s"
echo " Episodes          : $EPISODES"
echo " Episode duration  : ${EPISODE_DURATION}s"
echo " Interference OFF  : ${OFF_ATTEN} -> 90 dB actual"
echo " Interference ON   : ${ON_ATTEN} -> 60 dB actual"
echo "=============================================="


# Start safely with N300 strongly attenuated.
"$UPDATE_ATTENS" "$GROUP" "$OFF_ATTEN"


for ((ep=1; ep<=EPISODES; ep++)); do

    echo
    echo "=============================================="
    echo "Episode $ep/$EPISODES"
    echo "=============================================="

    elapsed=0
    state="OFF"

    while (( elapsed < EPISODE_DURATION )); do

        if [ "$state" = "OFF" ]; then

            echo "[$(date '+%H:%M:%S')] Interference OFF"

            "$UPDATE_ATTENS" "$GROUP" "$OFF_ATTEN"

            state="ON"

        else

            echo "[$(date '+%H:%M:%S')] Interference ON"

            "$UPDATE_ATTENS" "$GROUP" "$ON_ATTEN"

            state="OFF"

        fi

        sleep "$TOGGLE_PERIOD"

        elapsed=$((elapsed + TOGGLE_PERIOD))

    done

    echo "Episode finished."

    "$UPDATE_ATTENS" "$GROUP" "$OFF_ATTEN"

done


echo
echo "All episodes completed."