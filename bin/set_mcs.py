#!/usr/bin/env python3

import sys
from pathlib import Path
import yaml


CONFIG_FILE = Path("local/repository/etc/ocudu/gnb_rf_x310_ho.yml")


def set_mcs(mcs: int):
    if not 0 <= mcs <= 28:
        raise ValueError("MCS must be between 0 and 28")

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)

    # Create pdsch section if it does not exist
    cell_cfg = config.setdefault("cell_cfg", {})
    pdsch = cell_cfg.setdefault("pdsch", {})

    # Set fixed MCS
    pdsch["min_ue_mcs"] = mcs
    pdsch["max_ue_mcs"] = mcs

    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    print(f"MCS set to {mcs}")
    print(f"min_ue_mcs = {mcs}")
    print(f"max_ue_mcs = {mcs}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <MCS>")
        print("Example:")
        print(f"  {sys.argv[0]} 5")
        sys.exit(1)

    try:
        mcs = int(sys.argv[1])
    except ValueError:
        print("Error: MCS must be an integer.")
        sys.exit(1)

    try:
        set_mcs(mcs)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()