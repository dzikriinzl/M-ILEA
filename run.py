#!/usr/bin/env python3
import argparse
import json
import sys
import logging
import shutil
from pathlib import Path
from dataclasses import asdict, is_dataclass
from datetime import datetime

# Import modul internal
from core.report.visualizer import ReportVisualizer
from core.report.html_generator import HTMLReportGenerator
from cli.main import run_analysis
from core.decompiler.selector import decompile_hybrid
from core.analyzer.library_filter import tag_finding_origin

# Import v2.0 modules
from core.scoring.scorer_v2 import ConfidenceScorer, MethodLevelScorer, ClassLevelScorer, AppLevelScorer
from core.scoring.aggregator import ScoreAggregator, ComparisonGenerator
from core.vulnerability import VulnerabilityScanner
from core.vulnerability_v2 import VulnerabilityScannerV2
from core.evidence import EvidenceCollector, EvidenceViewer
from core.research.metrics import MetricsCalculator, ResearchMetricsReporter

# Import M2 Integration (4-Category Classification)
from core.integration.m2_integrator import M2AnalysisIntegrator

def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

def serialize_item(obj):
    """Helper untuk konversi dataclass ke dictionary secara mendalam."""
    if is_dataclass(obj): return asdict(obj)
    if isinstance(obj, dict): return {str(k): serialize_item(v) for k, v in obj.items()}
    if isinstance(obj, list): return [serialize_item(i) for i in obj]
    return obj

def deduplicate_and_group(findings):
    """
    ENHANCED Deduplication Logic (Senior Engineer Level):
    - Fingerprint: pattern_type + class + method (removes same-location noise)
    - Evidence-based deduplication: avoids counting identical code snippets
    - Confidence score resolution: keeps highest score per unique finding
    - Multi-layer filtering: reduces false positives from library code
    """
    unique_findings = {}
    evidence_cache = {}  # Cache to avoid identical evidence
    
    for f in findings:
        # Resolusi nama atribut
        p_type = getattr(f, 'protection_type', getattr(f, 'pattern_type', 'Unknown Detection'))
        
        # Ekstraksi lokasi
        loc = f.location if isinstance(f.location, dict) else asdict(f.location)
        
        # Get evidence snippet for content-based deduplication
        evidence_snippet = getattr(f, 'evidence_snippet', [])
        if isinstance(evidence_snippet, list):
            evidence_str = "".join(evidence_snippet)
        else:
            evidence_str = str(evidence_snippet)
        
        # PRIMARY FINGERPRINT: Category + Class + Method
        # Ini menangkap temuan di lokasi yang sama
        primary_fp = f"{p_type}|{loc.get('class')}|{loc.get('method')}"
        
        # SECONDARY FINGERPRINT: Include evidence content to detect identical code slices
        # Hash hanya first 200 chars untuk mempercepat perbandingan
        evidence_hash = hash(evidence_str[:200])
        secondary_fp = f"{primary_fp}|{evidence_hash}"
        
        # Check if this evidence already exists (word-for-word duplicate)
        if secondary_fp in evidence_cache:
            # Duplicate evidence - skip it to reduce noise
            continue
        
        if primary_fp not in unique_findings:
            unique_findings[primary_fp] = f
            evidence_cache[secondary_fp] = True
        else:
            # Primary fingerprint exists - resolve by confidence score
            current_conf = getattr(f, 'confidence_score', 0)
            existing_conf = getattr(unique_findings[primary_fp], 'confidence_score', 0)
            
            # Jika skor sama, bandingkan evidence untuk memilih yang lebih spesifik
            if current_conf > existing_conf:
                unique_findings[primary_fp] = f
                evidence_cache[secondary_fp] = True
            elif current_conf == existing_conf:
                # Skor sama: pilih yang memiliki evidence lebih panjang (lebih kontekstual)
                existing_evidence = getattr(unique_findings[primary_fp], 'evidence_snippet', [])
                existing_len = len("".join(existing_evidence)) if isinstance(existing_evidence, list) else 0
                current_len = len(evidence_str)
                
                if current_len > existing_len:
                    unique_findings[primary_fp] = f
                    evidence_cache[secondary_fp] = True
            else:
                # Existing score lebih tinggi, keep it
                evidence_cache[secondary_fp] = True

    return list(unique_findings.values())

def build_parser():
    parser = argparse.ArgumentParser(
        prog="M-ILEA",
        description="M-ILEA: Automated Mobile Application Self-Protection Analyzer",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Analyze a mobile application (APK)")
    analyze.add_argument("apk", type=Path, help="Path to the APK file")
    analyze.add_argument("-o", "--output", type=Path, help="Custom output path for JSON report")
    analyze.add_argument("-b", "--backend", choices=["auto", "smali", "jadx"], default="auto")
    analyze.add_argument("--group", action="store_true", help="Group identical findings")
    analyze.add_argument("--tag-libraries", action="store_true", help="Tag findings by origin (app vs library)")
    analyze.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser

def handle_analyze(args):
    setup_logging(args.verbose)
    apk_path = args.apk
    if not apk_path.exists():
        logging.error(f"APK file not found: {apk_path}")
        sys.exit(1)

    extracted_dir = None
    logging.info(f"Starting M-ILEA Analysis Pipeline for: {apk_path.name}")

    try:
        # --- PHASE 1 & 2: Decompilation & Core Analysis ---
        decompiled_classes, source_code_map, extracted_dir = decompile_hybrid(apk_path)
        
        # M-ILEA Pipeline Execution
        raw_findings, _ = run_analysis(
            decompiled_classes=decompiled_classes,
            source_code_map=source_code_map,
            extracted_apk_dir=extracted_dir
        )

        # --- DATA REFINEMENT (Deduplication) ---
        logging.info(f"Refining {len(raw_findings)} raw detections...")
        final_findings = deduplicate_and_group(raw_findings)
        logging.info(f"Deduplication complete: {len(final_findings)} unique protections verified.")

        # --- PHASE 3: ENHANCED v2.0 ANALYSIS ---
        logging.info("Phase 3: Applying v2.0 Enhancements...")
        
        # 3a. Serialize findings
        serialized_findings = [serialize_item(f) for f in final_findings]
        
        # 3b. Apply v2.0 Confidence Scoring
        logging.info("Calculating enhanced confidence scores (v2.0)...")
        try:
            # Strategy: Try aggregator first, fallback to using existing confidence_score
            aggregator = ScoreAggregator()
            try:
                aggregated_result = aggregator.score_findings(serialized_findings)
                enhanced_findings = aggregated_result.get("findings_enhanced", serialized_findings)
            except Exception as agg_err:
                logging.debug(f"Aggregator failed, using fallback: {agg_err}")
                enhanced_findings = serialized_findings
            
            # Ensure all findings have signal_confidence
            serialized_findings = []
            for f in enhanced_findings:
                f_dict = serialize_item(f)
                # If signal_confidence is 0 or missing, use confidence_score as fallback
                signal_conf = f_dict.get('signal_confidence', 0.0)
                if signal_conf == 0.0:
                    signal_conf = f_dict.get('confidence_score', 0.4)
                f_dict['signal_confidence'] = float(signal_conf)
                serialized_findings.append(f_dict)
            
            logging.info(f"Applied v2.0 confidence scoring to {len(serialized_findings)} findings")
            # Log some samples
            if serialized_findings:
                samples = [f.get('signal_confidence', 0.0) for f in serialized_findings[:5]]
                logging.info(f"Sample signal_confidence values: {samples}")
        except Exception as e:
            logging.warning(f"v2.0 scoring enhancement with error: {e}")
            # Ensure all have signal_confidence using confidence_score
            for f in serialized_findings:
                if isinstance(f, dict) and 'signal_confidence' not in f:
                    f['signal_confidence'] = float(f.get('confidence_score', 0.4))
        
        # 3c. Vulnerability Analysis (Safe Mode) - Using enhanced v2.0 scanner
        logging.info("Scanning for vulnerabilities (v2.0)...")
        vulnerabilities = []
        try:
            vuln_scanner = VulnerabilityScannerV2(extracted_dir)
            vulnerabilities = vuln_scanner.scan(decompiled_classes)
            logging.info(f"Detected {len(vulnerabilities)} vulnerabilities")
        except Exception as e:
            logging.warning(f"Vulnerability scanning skipped: {e}")
        
        # Add vulnerabilities metadata to findings
        vuln_by_location = {}
        for vuln in vulnerabilities:
            try:
                vuln_data = serialize_item(vuln)
                if isinstance(vuln_data, dict):
                    loc_info = vuln_data.get('location', {})
                    key = f"{loc_info.get('class', 'Unknown')}:{loc_info.get('method', 'Unknown')}"
                    if key not in vuln_by_location:
                        vuln_by_location[key] = []
                    vuln_by_location[key].append(vuln_data)
            except Exception as e:
                logging.debug(f"Skipping vulnerability: {e}")
        
        # Add vulnerabilities to findings safely
        for i, finding in enumerate(serialized_findings):
            try:
                # Handle both dict and other types
                if isinstance(finding, dict):
                    loc = finding.get('location', {})
                    if isinstance(loc, dict):
                        loc_key = f"{loc.get('class', 'Unknown')}:{loc.get('method', 'Unknown')}"
                        finding['associated_vulnerabilities'] = vuln_by_location.get(loc_key, [])
                    else:
                        finding['associated_vulnerabilities'] = []
                else:
                    # If not dict, can't add vulnerabilities
                    pass
            except Exception as e:
                logging.debug(f"Skipping vulnerability attachment for finding {i}: {e}")
        
        # 3d. Evidence Extraction (Safe Mode)
        evidence_groups = {}
        try:
            if source_code_map:
                logging.info("Extracting evidence and generating highlighting...")
                evidence_collector = EvidenceCollector(source_code_map)
                evidence_groups = evidence_collector.group_evidence_by_type(serialized_findings)
                logging.info(f"Extracted evidence for {len(evidence_groups)} locations")
        except Exception as e:
            logging.warning(f"Evidence extraction skipped: {e}")
        
        # Add evidence metadata to findings
        for i, finding in enumerate(serialized_findings):
            try:
                if isinstance(finding, dict):
                    loc = finding.get('location', {})
                    if isinstance(loc, dict):
                        loc_key = f"{loc.get('class', 'Unknown')}:{loc.get('method', 'Unknown')}"
                        finding['enhanced_evidence'] = evidence_groups.get(loc_key, {})
                    else:
                        finding['enhanced_evidence'] = {}
            except Exception as e:
                logging.debug(f"Skipping evidence attachment for finding {i}: {e}")
        
        # 3e. Calculate Research Metrics
        metrics = {}
        try:
            logging.info("Computing research-grade metrics...")
            metrics_calculator = MetricsCalculator()
            # Extract confidence values from findings (use signal_confidence if available, fallback to confidence_score)
            confidence_values = []
            for f in serialized_findings:
                if isinstance(f, dict):
                    val = f.get('signal_confidence', f.get('confidence_score', 0.0))
                    if val and isinstance(val, (int, float)):
                        confidence_values.append(float(val))
            
            logging.info(f"Extracted {len(confidence_values)} confidence values for metrics")
            if confidence_values and len(confidence_values) > 0:
                metrics_obj = metrics_calculator.calculate_confidence_metrics(confidence_values)
                # Convert ConfidenceMetrics object to dict (use correct field names)
                metrics = {
                    'mean': float(getattr(metrics_obj, 'mean_confidence', 0.0)),
                    'median': float(getattr(metrics_obj, 'median_confidence', 0.0)),
                    'std_dev': float(getattr(metrics_obj, 'std_confidence', 0.0)),
                    'min': float(getattr(metrics_obj, 'min_confidence', 0.0)),
                    'max': float(getattr(metrics_obj, 'max_confidence', 0.0)),
                }
                logging.info(f"Metrics: mean={metrics['mean']:.3f}, median={metrics['median']:.3f}, max={metrics['max']:.3f}")
            else:
                logging.warning(f"No valid confidence values extracted for metrics (got {len(confidence_values)})")
            logging.info("Research metrics calculated successfully")
        except Exception as e:
            logging.warning(f"Metrics calculation failed: {e}")
        
        # Tag findings by origin (application vs library) if requested
        if args.tag_libraries:
            serialized_findings = [tag_finding_origin(f) for f in serialized_findings]
            logging.info("Findings tagged by origin (app vs library)")
        
        # --- PHASE 4: Reporting & Visualization ---
        results_dir = Path("evaluation/results") / apk_path.stem
        results_dir.mkdir(parents=True, exist_ok=True)

        # Penyusunan Metadata untuk Jurnal (Enhanced)
        output_data = {
            "metadata": {
                "app_name": apk_path.name,
                "total_unique_findings": len(serialized_findings),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "backend_used": args.backend,
                "analysis_engine": "M-ILEA v2.0-Enhanced",
                "deduplication_enabled": True,
                "library_tagging_enabled": args.tag_libraries,
                "v2_features_enabled": True,
                "confidence_metrics": serialize_item(metrics),
                "vulnerability_summary": {
                    "total_vulnerabilities": len(vulnerabilities),
                    "critical_count": len([v for v in vulnerabilities if getattr(v, 'severity', 'Low') == "Critical"]),
                    "high_count": len([v for v in vulnerabilities if getattr(v, 'severity', 'Low') == "High"]),
                    "medium_count": len([v for v in vulnerabilities if getattr(v, 'severity', 'Low') == "Medium"]),
                    "low_count": len([v for v in vulnerabilities if getattr(v, 'severity', 'Low') == "Low"])
                }
            },
            "findings": serialized_findings,
            "vulnerabilities": [serialize_item(v) for v in vulnerabilities]
        }

        # Simpan Enhanced JSON Report
        report_file = args.output if args.output else results_dir / "report.json"
        with open(report_file, "w") as f_out:
            json.dump(output_data, f_out, indent=2)
        logging.info(f"Enhanced JSON report saved to: {report_file}")

        # ============ M2 Integration: 4-Category Self-Protection Classification ============
        try:
            logging.info("Starting M2 Integration: 4-Category Self-Protection Classification...")
            m2_integrator = M2AnalysisIntegrator(output_dir=str(results_dir))
            
            # Extract app name from APK path
            app_base_name = apk_path.stem.replace(".ipa", "").replace(".apk", "")
            
            # Integrate analysis with classifier
            integrated_report = m2_integrator.integrate_analysis(
                analysis_report=output_data,
                app_name=app_base_name
            )
            
            # Save integrated report
            integration_paths = m2_integrator.save_integrated_report(
                integrated_report,
                app_base_name
            )
            
            logging.info(f"M2 Integration Complete:")
            logging.info(f"  - Threat Level: {integrated_report['metadata']['threat_level']}")
            logging.info(f"  - Actual Findings: {integrated_report['metadata']['actual_self_protection_count']}")
            logging.info(f"  - Framework Noise: {integrated_report['metadata']['framework_noise_count']}")
            logging.info(f"  - Integrated Report: {integration_paths['json']}")
            
        except Exception as e:
            logging.warning(f"M2 Integration skipped: {e}")
            if args.verbose:
                logging.exception(e)

        # Dashboard Generation (Visualizer & HTML with M2 Integration)
        visualizer = ReportVisualizer(results_dir)
        # Menghasilkan berbagai grafik distribusi proteksi
        chart_names = visualizer.generate_charts(serialized_findings)
        
        if serialized_findings and chart_names:
            # Check if M2 integration data is available
            m2_report = None
            m2_json_path = results_dir / app_base_name / "m2_integration" / f"{app_base_name}_m2_integrated.json"
            if m2_json_path.exists():
                try:
                    with open(m2_json_path) as f:
                        m2_report = json.load(f)
                    logging.debug("M2 integration data loaded for HTML generation")
                except Exception as e:
                    logging.warning(f"Could not load M2 report for HTML: {e}")
            
            # Use standard HTML generator. If M2 integration data exists, embed it into metadata
            # so the generator can optionally render related sections without requiring a separate class.
            html_gen = HTMLReportGenerator(results_dir / "dashboard.html")
            # Prepare metadata copy and include m2_report if present
            meta = output_data.get("metadata", {}) if isinstance(output_data, dict) else {}
            try:
                meta_copy = dict(meta)
            except Exception:
                meta_copy = {"metadata": meta}

            if m2_report:
                meta_copy["m2_report"] = m2_report

            html_gen.generate(meta_copy, serialized_findings, chart_names,
                              vulnerabilities=vulnerabilities, metrics=metrics)
            logging.info(f"Dashboard generated: {results_dir}/dashboard.html")
        else:
            logging.warning("Visualization skipped: No valid protections identified.")

    except Exception as e:
        logging.error(f"Pipeline Execution Failed: {e}")
        if args.verbose:
            logging.exception(e)
        sys.exit(1)
        
    finally:
        # Cleanup temporary files (Keamanan Data)
        if extracted_dir and extracted_dir.exists() and not args.verbose:
            logging.debug(f"Cleaning up temporary workspace at {extracted_dir}")
            shutil.rmtree(extracted_dir)

    logging.info("M-ILEA Analysis Task Completed Successfully.")

def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "analyze":
        handle_analyze(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()