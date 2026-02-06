from core.slicing.java_slicer import JavaCodeSlicer
from core.slicing.native_slicer import NativeCodeSlicer
from core.slicing.semantic import SemanticLabeler
from core.slicing.models import EvidenceSlice


class EvidenceSlicer:
    def __init__(self):
        self.java = JavaCodeSlicer()
        self.native = NativeCodeSlicer()
        self.semantic = SemanticLabeler()

    def process(self, localized_protection, source_code):
        # REVISI: Samakan dengan label dari analyzer ("Java" atau "Native")
        layer = localized_protection.location.get("layer", "Java")

        # Pastikan source_code tersedia
        if not source_code:
            snippet, highlight = ["// Source code not available for this component"], 0
        elif layer == "Java" or layer == "Application":
            snippet, highlight = self.java.slice(
                source_code,
                localized_protection.location.get("line", 0)
            )
        else:
            snippet, highlight = self.native.slice(
                source_code,
                localized_protection.location.get("native_offset", 0)
            )

        semantic_label = self.semantic.label(
            localized_protection.pattern_type,
            localized_protection.evidence,
            localized_protection.location
        )

        return EvidenceSlice(
            pattern_type=localized_protection.pattern_type,
            impact_hint=localized_protection.impact_hint,
            location=localized_protection.location,
            code_snippet=snippet,
            highlighted_lines=[highlight],
            semantic_label=semantic_label,
            confidence_score=localized_protection.confidence_score
        )