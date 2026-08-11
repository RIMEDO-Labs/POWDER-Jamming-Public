#!/bin/bash

set -e

REPLAY="/usr/libexec/uhd/examples/rfnoc_replay_samples_from_file"

N300_ARGS="addr=192.168.10.2"

NOISE_FILE="${1:-/tmp/noise.sc16}"
FREQ="${2:-3489420000}"
RATE="${3:-92.16e6}"
GAIN="${4:-30}"
BW="${5:-20e6}"

echo "=============================================="
echo "       N300 RFNoC Noise Transmitter"
echo "=============================================="
echo "N300       : $N300_ARGS"
echo "Noise file : $NOISE_FILE"
echo "Frequency  : $FREQ Hz"
echo "Rate       : $RATE S/s"
echo "TX gain    : $GAIN dB"
echo "Bandwidth  : $BW Hz"
echo "=============================================="

if [ ! -f "$NOISE_FILE" ]; then
    echo "ERROR: Noise file does not exist:"
    echo "  $NOISE_FILE"
    exit 1
fi

if [ ! -x "$REPLAY" ]; then
    echo "ERROR: RFNoC Replay program not found:"
    echo "  $REPLAY"
    exit 1
fi

echo
echo "Starting N300 transmission..."
echo "Press Ctrl+C to stop."
echo

exec "$REPLAY" \
    --args "$N300_ARGS" \
    --freq "$FREQ" \
    --rate "$RATE" \
    --gain "$GAIN" \
    --bw "$BW" \
    --radio-id 0 \
    --radio-chan 0 \
    --replay-id 0 \
    --replay-chan 0 \
    --nsamps 0 \
    --file "$NOISE_FILE"