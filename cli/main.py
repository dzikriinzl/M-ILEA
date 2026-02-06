import logging
from pathlib import Path

# Step 1: Knowledge Base
from core.sinks.registry import SinkRegistry

# Step 2: Static Scanning
from core.analyzer.analyzer import StaticAnalyzer
from core.native.analyzer import NativeAnalyzer
from core.native.elf_loader import find_and_analyze_bins
from core.native.framework_identifier import FrameworkIdentifier

# Step 3: Pattern Recognition
from core.patterns.engine import ProtectionPatternEngine

# Step 4: Localization & Scoring
from core.localization.pipeline import LocalizationPipeline

# Step 5: Evidence Slicing
from core.slicing.slicer import EvidenceSlicer

# Step 6: Reporting & Taxonomy
from core.report.builder import ReportBuilder
from core.report.grouping import FindingGrouper

def run_analysis(decompiled_classes, source_code_map, extracted_apk_dir):
    """
    M-ILEA MAIN PIPELINE (Step 1 - Step 6)
    Orkestrasi seluruh proses analisis dari biner hingga laporan final.
    """
    findings = []
    grouped = {}

    # === STEP 1: LOAD KNOWLEDGE BASE (Sink Registry) ===
    # Memuat katalog target API, String, dan Syscall dari database eksternal.
    try:
        sink_registry = SinkRegistry("data/sink_catalog.json")
        logging.info("Step 1: Sink Registry loaded successfully.")
    except Exception as e:
        logging.error(f"Step 1 Failed: Sink catalog loading error: {e}")
        return [], {}

    # === STEP 2: STATIC SCANNING (Java & Native Layer) ===
    # Proses pencarian titik-titik sensitif (sinks) di berbagai lapisan aplikasi.
    try:
        # 2a. Java Layer Scanning (Level 1 & 2)
        java_analyzer = StaticAnalyzer(sink_registry, decompiled_classes)
        java_hits = java_analyzer.analyze()
        logging.info(f"Step 2a: Detected {len(java_hits)} Java sink hits.")

        # 2b. Native Layer Scanning (Level 3: Entropy, Framework, & Symbols)
        # Mencari file .so, menghitung entropi (packer), dan mendeteksi framework.
        so_files, packing_hits = find_and_analyze_bins(extracted_apk_dir)
        
        fw_ident = FrameworkIdentifier()
        detected_fws = fw_ident.identify([f.name for f in so_files])
        logging.info(f"Step 2b: Frameworks identified: {detected_fws}")
        
        native_analyzer = NativeAnalyzer(sink_registry)
        native_hits = native_analyzer.analyze_files(so_files)
        logging.info(f"Step 2b: Detected {len(native_hits)} Native sink hits.")
        
    except Exception as e:
        logging.error(f"Step 2 Failed: Static scanning error: {e}")
        java_hits, native_hits, packing_hits, detected_fws = [], [], [], []

    # === STEP 3: PROTECTION PATTERN RECOGNITION ===
    # Mengonversi temuan mentah (hits) menjadi kandidat mekanisme proteksi.
    try:
        # Menggabungkan semua sinyal dari berbagai layer
        all_hits = java_hits + native_hits + packing_hits
        
        # Inisialisasi engine dengan konteks framework (misal: Flutter)
        pattern_engine = ProtectionPatternEngine(context={"frameworks": detected_fws})
        candidates = pattern_engine.analyze(all_hits)
        logging.info(f"Step 3: Identified {len(candidates)} protection candidates.")
    except Exception as e:
        logging.error(f"Step 3 Failed: Pattern recognition error: {e}")
        return [], {}

    # === STEP 4: LOCALIZATION & FORMAL SCORING ===
    # Menentukan koordinat presisi dan menghitung skor kepercayaan (Weighted Evidence).
    try:
        localization_pipeline = LocalizationPipeline()
        localized = localization_pipeline.process(candidates)
        logging.info("Step 4: Localization and scoring completed.")
    except Exception as e:
        logging.error(f"Step 4 Failed: Localization error: {e}")
        localized = []

    # === STEP 5: EVIDENCE-BASED CODE SLICING ===
    # Ekstraksi potongan kode (evidence) untuk memvalidasi temuan.
    try:
        slicer = EvidenceSlicer()
        evidence_slices = []
        for lp in localized:
            # Ambil source dari Java Map (Step 2a) atau Native Binary (Step 2b)
            source = source_code_map.get(lp.location.get("class"), [])
            evidence_slices.append(slicer.process(lp, source))
        logging.info(f"Step 5: Generated {len(evidence_slices)} evidence slices.")
    except Exception as e:
        logging.error(f"Step 5 Failed: Evidence slicing error: {e}")
        evidence_slices = []

    # === STEP 6: TAXONOMY MAPPING & REPORT GENERATION ===
    # Pemetaan otomatis ke Taxonomy 4-Dimensi dan grouping hasil.
    try:
        report_builder = ReportBuilder()
        findings = report_builder.build(evidence_slices)

        # Mengelompokkan temuan untuk hasil yang lebih bersih di paper
        grouper = FindingGrouper()
        grouped = grouper.group(findings)
        
        logging.info("Step 6: Final report and taxonomy mapping completed.")
    except Exception as e:
        logging.error(f"Step 6 Failed: Reporting error: {e}")

    return findings, grouped
