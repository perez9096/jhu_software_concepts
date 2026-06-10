#!/usr/bin/env python3
"""Run the Grad Cafe scraper and then standardize the results with the local LLM.

This script produces two files:
- module_2/applicant_data.json
- module_2/applicant_data_llm.json

It resumes scraping from the current checkpoint if available.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRAPER = ROOT / "module_2" / "scraper.py"
LLM_APP = Path(__file__).resolve().parent / "app.py"
DEFAULT_RAW_OUT = ROOT / "module_2" / "applicant_data.json"
DEFAULT_LLM_OUT = ROOT / "module_2" / "applicant_data_llm.json"
DEFAULT_CHECKPOINT = ROOT / "module_2" / "checkpoint.json"


def run_command(command, cwd):
    print("Running:", " ".join(map(str, command)))
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Command failed:", " ".join(map(str, command)))
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run scraper.py and then app.py to produce raw and LLM-standardized applicant JSON.",
    )
    parser.add_argument(
        "--raw-out",
        default=DEFAULT_RAW_OUT,
        help="Raw scraper output path (default: module_2/applicant_data.json)",
    )
    parser.add_argument(
        "--llm-out",
        default=DEFAULT_LLM_OUT,
        help="LLM-standardized output path (default: module_2/applicant_data_llm.json)",
    )
    parser.add_argument(
        "--checkpoint",
        default=DEFAULT_CHECKPOINT,
        help="Checkpoint file path for scraper resume.",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=5000,
        help="Maximum survey pages to scrape.",
    )
    parser.add_argument(
        "--save-every",
        type=int,
        default=5,
        help="Save scraper progress every N pages.",
    )
    args = parser.parse_args()

    raw_out = Path(args.raw_out).resolve()
    llm_out = Path(args.llm_out).resolve()
    checkpoint = Path(args.checkpoint).resolve()

    raw_out.parent.mkdir(parents=True, exist_ok=True)
    llm_out.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)

    print("=== Scraping new Grad Cafe data ===")
    scraper_cmd = [
        sys.executable,
        str(SCRAPER),
        "--resume",
        "--out",
        str(raw_out),
        "--checkpoint",
        str(checkpoint),
        "--pages",
        str(args.pages),
        "--save-every",
        str(args.save_every),
    ]
    run_command(scraper_cmd, cwd=ROOT / "module_2")

    print("=== Standardizing with the local LLM ===")
    llm_cmd = [
        sys.executable,
        str(LLM_APP),
        "--file",
        str(raw_out),
        "--out",
        str(llm_out),
    ]
    run_command(llm_cmd, cwd=LLM_APP.parent)

    print("=== Complete ===")
    print(f"Raw scraper data: {raw_out}")
    print(f"LLM-standardized data: {llm_out}")


if __name__ == "__main__":
    main()
