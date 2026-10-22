#!/usr/bin/env python3

"""
Controlled jamming-scenario signal generator.

Generates complex Gaussian IQ noise with a selectable time-varying
amplitude envelope and stores:
  1. IQ samples in SC16 format
  2. Scenario metadata in JSON

Supported scenarios:
  constant
  pulse
  sawtooth

Examples:
    python jammer.py constant --level 1.0 --duration 0.1

    python jammer.py pulse --level 1.0 --on 100 --off 100 --duration 0.2

    python jammer.py sawtooth --min-level 0.1 --max-level 1.0 \
        --period 2 --duration 0.1
"""

import argparse
import json
from pathlib import Path

import numpy as np


DEFAULT_SAMPLE_RATE = 92.16e6
DEFAULT_SEED = 1234


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate controlled jamming-scenario IQ data."
    )

    parser.add_argument(
        "scenario",
        choices=["constant", "pulse", "sawtooth"],
        help="Jamming scenario type.",
    )

    parser.add_argument(
        "--output",
        default="jammer.sc16",
        help="Output SC16 IQ file.",
    )

    parser.add_argument(
        "--metadata",
        default=None,
        help="Metadata JSON file. Defaults to <output>.json.",
    )

    parser.add_argument(
        "--sample-rate",
        type=float,
        default=DEFAULT_SAMPLE_RATE,
        help=f"Sample rate [samples/s]. Default: {DEFAULT_SAMPLE_RATE}",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Total signal duration [s]. Default: 10.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed. Default: {DEFAULT_SEED}",
    )

    # Common amplitude/level parameter.
    parser.add_argument(
        "--level",
        type=float,
        default=1.0,
        help="Maximum/constant normalized level. Range: 0..1.",
    )

    # Pulse parameters.
    parser.add_argument(
        "--on",
        type=float,
        default=100.0,
        help="Pulse ON time [ms].",
    )

    parser.add_argument(
        "--off",
        type=float,
        default=100.0,
        help="Pulse OFF time [ms].",
    )

    # Sawtooth parameters.
    parser.add_argument(
        "--min-level",
        type=float,
        default=0.0,
        help="Sawtooth minimum normalized level.",
    )

    parser.add_argument(
        "--max-level",
        type=float,
        default=1.0,
        help="Sawtooth maximum normalized level.",
    )

    parser.add_argument(
        "--period",
        type=float,
        default=2.0,
        help="Sawtooth period [s].",
    )

    return parser.parse_args()


def validate_args(args):
    if args.sample_rate <= 0:
        raise ValueError("sample-rate must be > 0.")

    if args.duration <= 0:
        raise ValueError("duration must be > 0.")

    if args.seed < 0:
        raise ValueError("seed must be >= 0.")

    if not 0.0 <= args.level <= 1.0:
        raise ValueError("level must be between 0 and 1.")

    if args.scenario == "pulse":
        if args.on <= 0:
            raise ValueError("--on must be > 0 ms.")

        if args.off <= 0:
            raise ValueError("--off must be > 0 ms.")

    if args.scenario == "sawtooth":
        if args.period <= 0:
            raise ValueError("--period must be > 0 s.")

        if not 0.0 <= args.min_level <= 1.0:
            raise ValueError("--min-level must be between 0 and 1.")

        if not 0.0 <= args.max_level <= 1.0:
            raise ValueError("--max-level must be between 0 and 1.")

        if args.min_level > args.max_level:
            raise ValueError("--min-level cannot be greater than --max-level.")


def make_envelope(args, n_samples):
    """
    Create a normalized amplitude envelope in the range 0..1.
    """

    t = np.arange(n_samples, dtype=np.float64) / args.sample_rate

    if args.scenario == "constant":
        envelope = np.full(n_samples, args.level, dtype=np.float64)

    elif args.scenario == "pulse":
        on_s = args.on / 1000.0
        off_s = args.off / 1000.0
        cycle_s = on_s + off_s

        phase = np.mod(t, cycle_s)
        envelope = np.where(phase < on_s, args.level, 0.0)

    elif args.scenario == "sawtooth":
        phase = np.mod(t, args.period) / args.period

        envelope = (
            args.min_level
            + (args.max_level - args.min_level) * phase
        )

    else:
        raise ValueError(f"Unsupported scenario: {args.scenario}")

    return envelope


def generate_iq(args):
    n_samples = int(args.sample_rate * args.duration)

    print("Generating scenario:")
    print(f"  type        : {args.scenario}")
    print(f"  sample rate : {args.sample_rate / 1e6:.2f} MS/s")
    print(f"  duration    : {args.duration:.3f} s")
    print(f"  samples     : {n_samples}")
    print(f"  seed        : {args.seed}")

    rng = np.random.default_rng(args.seed)

    # Complex Gaussian noise.
    noise = (
        rng.standard_normal(n_samples)
        + 1j * rng.standard_normal(n_samples)
    ) / np.sqrt(2)

    # Normalize base noise.
    peak = np.max(np.abs(noise))
    if peak == 0:
        raise RuntimeError("Generated noise has zero amplitude.")

    noise = noise / peak

    # Apply scenario-specific amplitude envelope.
    envelope = make_envelope(args, n_samples)
    signal = noise * envelope

    # Convert to signed 16-bit IQ.
    scale = 32767

    i = np.real(signal * scale).astype(np.int16)
    q = np.imag(signal * scale).astype(np.int16)

    iq = np.empty(2 * n_samples, dtype=np.int16)
    iq[0::2] = i
    iq[1::2] = q

    return iq, envelope


def build_metadata(args, n_samples, envelope):
    metadata = {
        "scenario": args.scenario,
        "sample_rate_sps": args.sample_rate,
        "duration_s": args.duration,
        "num_samples": n_samples,
        "seed": args.seed,
        "normalized_level_range": [
            float(np.min(envelope)),
            float(np.max(envelope)),
        ],
    }

    if args.scenario == "constant":
        metadata.update({
            "level": args.level,
        })

    elif args.scenario == "pulse":
        metadata.update({
            "level": args.level,
            "on_ms": args.on,
            "off_ms": args.off,
            "duty_cycle": args.on / (args.on + args.off),
        })

    elif args.scenario == "sawtooth":
        metadata.update({
            "min_level": args.min_level,
            "max_level": args.max_level,
            "period_s": args.period,
        })

    return metadata


def main():
    args = parse_args()
    validate_args(args)

    output_path = Path(args.output)

    if args.metadata is None:
        metadata_path = output_path.with_suffix(".json")
    else:
        metadata_path = Path(args.metadata)

    iq, envelope = generate_iq(args)

    iq.tofile(output_path)

    metadata = build_metadata(
        args,
        int(args.sample_rate * args.duration),
        envelope,
    )

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print()
    print("Done.")
    print(f"  IQ       : {output_path}")
    print(f"  metadata : {metadata_path}")


if __name__ == "__main__":
    main()
