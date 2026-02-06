#!/usr/bin/env python3
import argparse
import json
import sys
import logging
from pathlib import Path
from dataclasses import asdict, is_dataclass

from cli.main import run_analysis
from core.decompiler.selector import decompile_hybrid

def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

def build_parser():
    parser = argparse.ArgumentParser(
        prog="M-ILEA",
        description=(
            "M-ILEA: Automated Identification, Localization, and "
            "Evidence-Based Analysis of Mobile Application Self-Protection Mechanisms"
        ),
    )

    subparsers = parser.add_subparsers(
        title="Commands",
        dest="command",
        required=True
    )

    # --------------------------------------------------------------------------
    # Command: analyze
    # --------------------------------------------------------------------------
    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze a mobile application (APK) and detect protections"
    )

    analyze.add_argument(
        "apk",
        type=Path,
        help="Path to the APK file"
    )

    analyze.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("report.json"),
        help="Path to save the JSON report (default: report.json)"
    )

    analyze.add_argument(
        "-b", "--backend",
        choices=["auto", "smali", "jadx"],
        default="auto",
        help="Decompiler backend to use (default: auto)"
    )

    analyze.add_argument(
        "--no-native",
        action="store_true",
        help="Skip Level 3 (Native/ELF) analysis"
    )

    analyze.add_argument(
        "--group",
        action="store_true",
        help="Group identical findings by protection type (recommended)"
    )

    analyze.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug logging"
    )

    return parser

def handle_analyze(args):
    setup_logging(args.verbose)
    apk_path = args.apk
    if not apk_path.exists():
        logging.error(f"APK file not found: {apk_path}")
        sys.exit(1)

    logging.info(f"Starting M-ILEA Analysis Pipeline for: {apk_path.name}")

    try:
        logging.info(f"Initiating Hybrid Decompilation...")
        decompiled_classes, source_code_map, extracted_dir = decompile_hybrid(apk_path)
    except Exception as e:
        logging.error(f"Decompilation failed: {e}")
        sys.exit(1)

    try:
        findings, grouped = run_analysis(
            decompiled_classes=decompiled_classes,
            source_code_map=source_code_map,
            extracted_apk_dir=extracted_dir
        )
    except Exception as e:
        logging.error(f"Analysis pipeline crashed: {e}")
        sys.exit(1)

    # --- PHASE 3: Reporting & Finalization (FIXED) ---
    try:
        # REVISI: Fungsi helper untuk konversi dataclass secara mendalam (deep conversion)
        def serialize_item(obj):
            if is_dataclass(obj):
                return asdict(obj)
            if isinstance(obj, dict):
                return {str(k): serialize_item(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize_item(i) for i in obj]
            return obj

        output_data = {
            "metadata": {
                "app_name": apk_path.name,
                "total_findings": len(findings),
                "backend_used": args.backend,
                "framework_context": True
            },
            "findings": [serialize_item(f) for f in findings],
            "grouped_findings": serialize_item(grouped) if args.group else None
        }

        with open(args.output, "w") as f_out:
            json.dump(output_data, f_out, indent=2)

        logging.info("Analysis successfully completed.")
        logging.info(f"Final report saved to: {args.output}")
    except Exception as e:
        logging.error(f"Failed to write report file: {e}")

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        handle_analyze(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
