#!/usr/bin/env python3
"""Run the Grad Cafe scraper and then standardize the results with the local LLM.

This script is self-contained for module_4.

It produces:
- module_4/src/applicant_data.json
- module_4/src/applicant_data_llm_M4.jsonl

It resumes scraping from module_4/src/checkpoint.json if available.
"""

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent

SCRAPER = SCRIPT_DIR / "scraper.py"
LLM_APP = SCRIPT_DIR / "llm_hosting" / "app.py"

DEFAULT_RAW_OUT = SRC_DIR / "applicant_data.json"
DEFAULT_LLM_OUT = SRC_DIR / "applicant_data_llm_M4.jsonl"
DEFAULT_CHECKPOINT = SRC_DIR / "checkpoint.json"


def run_command(command, cwd):
#    print("Running:", " ".join(map(str, command)), flush=True)

    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, flush=True)

    if result.stderr:
        print(result.stderr, flush=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            + " ".join(map(str, command))
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run scraper.py and then app.py to produce raw and LLM-standardized applicant data."
    )

    parser.add_argument(
        "--raw-out",
        default=str(DEFAULT_RAW_OUT),
        help="Raw scraper output path.",
    )

    parser.add_argument(
        "--llm-out",
        default=str(DEFAULT_LLM_OUT),
        help="LLM-standardized output path.",
    )

    parser.add_argument(
        "--checkpoint",
        default=str(DEFAULT_CHECKPOINT),
        help="Checkpoint file path for scraper resume.",
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=5,
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

    print("=== Scraping new Grad Cafe data ===", flush=True)

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

    run_command(scraper_cmd, cwd=SCRIPT_DIR)

    print("=== Standardizing with the local LLM ===", flush=True)

    llm_cmd = [
        sys.executable,
        str(LLM_APP),
        "--file",
        str(raw_out),
        "--out",
        str(llm_out),
    ]

    run_command(llm_cmd, cwd=LLM_APP.parent)

    print("=== Complete ===", flush=True)
    print(f"Raw scraper data: {raw_out}", flush=True)
    print(f"LLM-standardized data: {llm_out}", flush=True)


if __name__ == "__main__":
    main()
