from core.patterns.base import BaseProtectionPattern
# Pastikan import mengarah ke model yang sudah kita seragamkan
from core.analyzer.models import ProtectionCandidate

class SSLPinningPattern(BaseProtectionPattern):
    PATTERN_NAME = "SSL Pinning"
    IMPACT_HINT = "Blocks traffic interception"

    def match(self, sink_hit, context=None):
        # Ambil list framework dari context (misal untuk deteksi Flutter/BoringSSL)
        detected_fw = context.get("frameworks", []) if context else []

        # Sinkronisasi dengan Risk Category di sink_catalog.json
        if sink_hit.sink.get("risk") == "Secure Communication":
            
            current_pattern = self.PATTERN_NAME
            current_impact = self.IMPACT_HINT

            # Logika Context-Aware: Jika Flutter terdeteksi, berikan label lebih spesifik
            if "Flutter" in detected_fw or sink_hit.sink.get("layer") == "Native":
                current_pattern = "Advanced SSL Pinning (Framework-level)"
                current_impact = "Blocks traffic interception (BoringSSL/Flutter/Native)"

            # REVISI: Menggunakan struktur dictionary 'location' dan 'confidence_signal' yang seragam
            return ProtectionCandidate(
                pattern_type=current_pattern,
                location={
                    "class": sink_hit.class_name,
                    "method": sink_hit.method_name,
                    "line": sink_hit.line_number,
                    "layer": getattr(sink_hit, 'layer', 'Java')
                },
                # Evidence berupa string informatif untuk laporan
                evidence=f"Secure channel enforcement via {sink_hit.sink.get('name')}",
                impact_hint=current_impact,
                # Kirim objek hit sebagai signal untuk diproses Scorer.breakdown()
                confidence_signal=sink_hit 
            )
        return None