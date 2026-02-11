from core.slicing.java_slicer import JavaCodeSlicer
from core.slicing.native_slicer import NativeCodeSlicer
from core.slicing.semantic import SemanticLabeler
from core.slicing.models import EvidenceSlice

class EvidenceSlicer:
    def __init__(self):
        self.java = JavaCodeSlicer()
        self.native = NativeCodeSlicer()
        self.semantic = SemanticLabeler()
        self.processed_evidence = set()  # Cache to track processed evidence

    def process(self, localized_protection, source_code):
        layer = localized_protection.location.get("layer", "Java")

        if not source_code:
            snippet, highlights = ["// [!] Source code unavailable for context analysis"], []
        elif layer in ["Java", "Application"]:
            snippet, highlights = self.java.slice(
                source_code,
                localized_protection.location.get("line", 0)
            )
        else:
            snippet, highlights = self.native.slice(
                source_code,
                localized_protection.location.get("native_offset", 0)
            )

        # Generate label yang lebih "berbobot" ilmiah
        semantic_label = self.semantic.label(
            localized_protection.pattern_type,
            localized_protection.evidence,
            localized_protection.location
        )
        
        # Create evidence fingerprint to detect duplicates
        evidence_content = "".join(snippet)
        evidence_fingerprint = (
            localized_protection.location.get("class"),
            localized_protection.location.get("method"),
            hash(evidence_content[:200])
        )
        
        # NOISE REDUCTION: Filter out duplicate evidence within same method
        if evidence_fingerprint in self.processed_evidence:
            # Mark snippet as filtered to indicate this is a duplicate
            snippet = ["// [FILTERED] Duplicate evidence in same method"]
            highlights = []
        else:
            self.processed_evidence.add(evidence_fingerprint)

        return EvidenceSlice(
            pattern_type=localized_protection.pattern_type,
            impact_hint=localized_protection.impact_hint,
            location=localized_protection.location,
            code_snippet=snippet,
            highlighted_lines=highlights,
            semantic_label=semantic_label,
            confidence_score=localized_protection.confidence_score
        )