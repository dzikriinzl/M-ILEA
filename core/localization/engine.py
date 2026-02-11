import logging
import re

class LocalizationEngine:
    def __init__(self, scorer):
        self.scorer = scorer

    def _clean_method_name(self, method):
        # Menghapus descriptor seperti ()Z, ()V, dll menggunakan Regex
        return re.sub(r'\(.*\).*', '()', method)

    def process(self, candidates):
        localized_findings = []
        for candidate in candidates:
            try:
                # 1. Bersihkan Nama Method (isRooted()Z -> isRooted())
                raw_method = candidate.location.get("method", "Unknown")
                clean_method = self._clean_method_name(raw_method)
                
                # 2. Buat File Path (com.app.Test -> com/app/Test.java)
                class_name = candidate.location.get("class", "Unknown")
                file_path = class_name.replace(".", "/") + ".java"

                # Update data lokasi
                candidate.location["method"] = clean_method
                candidate.location["file_path"] = file_path
                candidate.location["full_signature"] = f"{class_name} -> {clean_method}"

                # Skoring tetap sama
                candidate.confidence_score = self.scorer.score(candidate.confidence_signal)
                candidate.score_breakdown = self.scorer.breakdown(candidate.confidence_signal)

                localized_findings.append(candidate)
            except Exception as e:
                logging.error(f"Step 4 Error: {e}")
                
        return localized_findings