from core.patterns.base import BaseProtectionPattern
from core.patterns.models import ProtectionCandidate, ConfidenceSignal

class SSLPinningPattern(BaseProtectionPattern):
    PATTERN_NAME = "SSL Pinning"
    IMPACT_HINT = "Blocks traffic interception"

    def match(self, sink_hit, context=None):
        # Ambil list framework dari context (jika ada)
        detected_fw = context.get("frameworks", []) if context else []

        if sink_hit.sink["risk"] == "Secure Communication":
            # LOGIKA REFINEMENT: Jika Flutter terdeteksi, naikkan status proteksi
            current_pattern = self.PATTERN_NAME
            current_impact = self.IMPACT_HINT

            if "Flutter" in detected_fw:
                current_pattern = "Advanced SSL Pinning (Framework-level)"
                current_impact = "Blocks traffic interception (BoringSSL/Flutter)"

            return ProtectionCandidate(
                pattern_type=current_pattern,
                sink=sink_hit.sink,
                class_name=getattr(sink_hit, 'class_name', 'Unknown'),
                method_name=getattr(sink_hit, 'method_name', 'Unknown'),
                line_number=getattr(sink_hit, 'line_number', 0),
                evidence={
                    "api": sink_hit.sink["name"],
                    "location": getattr(sink_hit, 'library', 'JavaLayer'),
                    "snippet": getattr(sink_hit, 'context_snippet', [])
                },
                impact_hint=current_impact,
                confidence_signal=ConfidenceSignal(
                    has_string_match=getattr(sink_hit, 'is_string_based', False),
                    has_api_match=True,
                    has_control_flow_logic=getattr(sink_hit, 'conditional', False),
                    is_native_implementation=sink_hit.sink["layer"] == "Native"
                )
            )
        return None
