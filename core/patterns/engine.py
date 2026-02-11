import logging
from core.patterns.communication import SSLPinningPattern
from core.patterns.root_detection_audit import RootDetectionAudit
from core.patterns.emulator_detection_audit import EmulatorDetectionAudit
from core.patterns.self_protection_audit import SelfProtectionAudit

class ProtectionPatternEngine:
    def __init__(self, context=None):
        self.context = context
        # Prioritize high-confidence audit patterns over legacy patterns
        self.patterns = [
            SSLPinningPattern(),
            RootDetectionAudit(),           # High-confidence root detection
            EmulatorDetectionAudit(),        # Hard evidence emulator detection
            SelfProtectionAudit()            # Active defense mechanisms
        ]

    def analyze(self, sink_hits):
        candidates = []
        processed_locations = set()  # Track already-processed locations to avoid duplicates
        
        for hit in sink_hits:
            # Create a unique identifier for this hit location
            hit_location_id = f"{hit.class_name}|{hit.method_name}|{hit.line_number}"
            
            # Skip if we've already generated a candidate for this exact location
            if hit_location_id in processed_locations:
                continue
            
            for pattern in self.patterns:
                try:
                    result = pattern.match(hit, context=self.context)
                    if result:
                        candidates.append(result)
                        processed_locations.add(hit_location_id)
                        break  # Only one pattern per hit to avoid duplication
                except Exception as e:
                    logging.error(f"Pattern matching error: {e}")
        
        return candidates