#!/usr/bin/env python3

import asyncio
import json
import time

import websockets


# ============================================================
# CONFIGURATION
# ============================================================

WS_URL = "ws://127.0.0.1:8001"

# Set to a specific RNTI if you want to monitor only one UE.
# Set to None to process all UEs.
TARGET_RNTI = None


# ============================================================
# METRICS EXTRACTION
# ============================================================

def extract_metrics(message):
    """
    Convert the OCUDU JSON message into a simple dictionary
    used by the jamming detection algorithm.

    TODO:
        Adapt this function to the actual OCUDU JSON format.
    """

    # Example of the format expected by the detector:
    #
    # return {
    #     "rnti": 123,
    #     "cqi": 15,
    #     "mcs": 27,
    #     "rsrp": -76.2,
    #     "snr": 18.4,
    #     "dl_bitrate": 100e6,
    #     "harq_nack_ratio": 0.0,
    # }

    return None


# ============================================================
# JAMMING DETECTION ALGORITHM
# ============================================================

def detect_jamming(metrics):
    """
    Return:

        0 -> no jamming
        1 -> jamming detected

    Replace this function with your own detection algorithm.
    """

    # --------------------------------------------------------
    # Simple example detector
    # --------------------------------------------------------

    score = 0

    if metrics["snr"] < 8:
        score += 1

    if metrics["cqi"] < 10:
        score += 1

    if metrics["harq_nack_ratio"] > 0.20:
        score += 1

    # Jamming is detected when at least
    # two indicators are triggered.
    if score >= 2:
        return 1

    return 0

def handle_detection(metrics, jamming):
    timestamp = time.strftime("%H:%M:%S")

    print(
        f"[{timestamp}] "
        f"RNTI={metrics.get('rnti')} "
        f"CQI={metrics.get('cqi')} "
        f"MCS={metrics.get('mcs')} "
        f"RSRP={metrics.get('rsrp')} dB "
        f"SNR={metrics.get('snr')} dB "
        f"NACK={metrics.get('harq_nack_ratio', 0) * 100:.1f}% "
        f"-> JAMMING={jamming}",
        flush=True
    )

    if jamming == 1:
        print("!!! JAMMING DETECTED !!!", flush=True)


# ============================================================
# WEBSOCKET RECEIVER
# ============================================================

async def receive_metrics():

    print(f"Connecting to OCUDU metrics at {WS_URL}...", flush=True)

    async with websockets.connect(WS_URL) as websocket:

        print("Connected to OCUDU.", flush=True)
        print("Waiting for metrics...\n", flush=True)

        while True:

            try:
                # Receive message from OCUDU.
                raw_message = await websocket.recv()

                # Parse JSON.
                message = json.loads(raw_message)

                # Extract metrics needed by detector.
                metrics = extract_metrics(message)

                if metrics is None:
                    continue

                # Optional UE filtering.
                if (
                    TARGET_RNTI is not None
                    and metrics.get("rnti") != TARGET_RNTI
                ):
                    continue

                # Run jamming detection.
                jamming = detect_jamming(metrics)

                # Handle result.
                handle_detection(metrics, jamming)

            except json.JSONDecodeError:
                print("Received invalid JSON.", flush=True)

            except websockets.ConnectionClosed:
                print("Connection to OCUDU closed.", flush=True)
                break

            except Exception as e:
                print(f"Error: {e}", flush=True)


# ============================================================
# MAIN
# ============================================================

def main():

    try:
        asyncio.run(receive_metrics())

    except KeyboardInterrupt:
        print("\nJamming detector stopped.", flush=True)


if __name__ == "__main__":
    main()