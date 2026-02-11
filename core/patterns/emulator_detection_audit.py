"""
Deep Audit Pattern for Emulator Detection (Hard Evidence)

Focuses on hardware/property verification only, filtering utility functions.
Criteria:
1. Build Properties: FINGERPRINT="generic", HARDWARE="goldfish"/"ranchu", DEVICE="generic"
2. Sensor Count: Checking for few/no sensors (emulators have minimal sensors)
3. Telephony: Operator name="Android" (clear emulator indicator)
4. Kernel Properties: ro.kernel.qemu, ro.hardware.virtual_device
"""

import json
import logging
import re
from typing import List, Optional, Tuple
from core.patterns.base import BaseProtectionPattern
from core.analyzer.models import ProtectionCandidate


class EmulatorDetectionAudit(BaseProtectionPattern):
    PATTERN_NAME = "Emulator Detection (Hard Evidence)"
    IMPACT_HINT = "Detects emulator/virtualized environment using hardware properties"

    def __init__(self):
        self.confidence_levels = {
            "HARD_EVIDENCE": 0.95,   # Multiple property checks or telephony="Android"
            "STRONG": 0.8,           # Specific hardware string (goldfish, ranchu)
            "MEDIUM": 0.65           # Generic property checks (fingerprint contains "generic")
        }
        
        try:
            with open("data/indicators.json") as f:
                self.indicators = json.load(f)
                self.emulator_indicators = self.indicators.get("emulator_indicators", {})
                self.utility_ignore = self.indicators.get("utility_methods_to_ignore", [])
        except Exception as e:
            logging.error(f"Failed to load indicators: {e}")
            self.emulator_indicators = {}
            self.utility_ignore = []

    def match(self, sink_hit, context=None) -> Optional[ProtectionCandidate]:
        """
        Match emulator detection logic with hard evidence scoring.
        Filters out noise by ignoring utility functions.
        """
        if sink_hit.sink.get("risk") not in ["Emulator Detection", "Environment Verification"]:
            return None

        # Filter 1: Ignore utility functions
        if self._is_utility_function(sink_hit):
            return None

        # Filter 2: Check for hardware/property verification (not generic utility)
        confidence, evidence = self._evaluate_hardware_logic(sink_hit)

        if confidence is None:
            return None

        return ProtectionCandidate(
            pattern_type=self.PATTERN_NAME,
            location={
                "class": sink_hit.class_name,
                "method": sink_hit.method_name,
                "line": sink_hit.line_number,
                "layer": getattr(sink_hit, 'layer', 'Java')
            },
            evidence=evidence,
            impact_hint=self.IMPACT_HINT,
            confidence_signal=sink_hit,
            confidence_level=confidence
        )

    def _is_utility_function(self, sink_hit) -> bool:
        """
        Filter out utility functions.
        """
        method_name = sink_hit.method_name.lower()
        
        utility_patterns = [
            r"tohex", r"hexto", r"encode", r"decode", r"format.*string",
            r"serialize", r"parse.*json", r".*_utils$", r"^get[a-z]*$",
            r"init.*array", r"fill.*array"
        ]
        
        for pattern in utility_patterns:
            if re.search(pattern, method_name):
                return True
        
        for utility_method in self.utility_ignore:
            if utility_method.lower() in method_name:
                return True
        
        return False

    def _evaluate_hardware_logic(self, sink_hit) -> Tuple[Optional[float], str]:
        """
        Evaluate the actual hardware verification logic for emulator detection.
        Returns (confidence_score, evidence_text) or (None, "") if not emulator detection.
        """
        all_args = getattr(sink_hit, 'arguments', [])
        sink_name = sink_hit.sink.get('name', '')
        is_conditional = getattr(sink_hit, 'conditional', False)

        # HARD EVIDENCE: Telephony check (getNetworkOperatorName="Android")
        confidence, evidence = self._check_telephony_detection(all_args, sink_name)
        if confidence:
            return confidence, evidence

        # STRONG: Hardware string verification (goldfish, ranchu, vbox86)
        confidence, evidence = self._check_hardware_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # STRONG: Build property checks (FINGERPRINT="generic", HARDWARE="generic")
        confidence, evidence = self._check_build_property_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # MEDIUM: Kernel properties (ro.kernel.qemu, ro.hardware.virtual_device)
        confidence, evidence = self._check_kernel_property_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # MEDIUM: Sensor count verification
        confidence, evidence = self._check_sensor_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        return None, ""

    def _check_telephony_detection(self, args: List[str], sink_name: str) -> Tuple[Optional[float], str]:
        """
        HARD EVIDENCE: Telephony operator name check
        getNetworkOperatorName returning "Android" is a definitive emulator indicator.
        """
        telephony_indicators = self.emulator_indicators.get("telephony", [])
        
        # Look for telephony-related method calls
        if "getNetworkOperatorName" in sink_name or "getNetworkOperator" in sink_name:
            for arg in args:
                for indicator in telephony_indicators:
                    if indicator.lower() in arg.lower():
                        confidence = self.confidence_levels["HARD_EVIDENCE"]
                        evidence = f"Emulator telephony check: NetworkOperator='{indicator}' is definitive emulator indicator"
                        return confidence, evidence
        
        # Also check arguments directly
        for arg in args:
            for indicator in telephony_indicators:
                if indicator.lower() == arg.lower():
                    confidence = self.confidence_levels["HARD_EVIDENCE"]
                    evidence = f"Emulator telephony check: Operator name '{indicator}' detected"
                    return confidence, evidence
        
        return None, ""

    def _check_hardware_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        STRONG: Hardware string checks (goldfish, ranchu, vbox86, etc.)
        These are specific emulator hardware identifiers.
        """
        hardware_strings = self.emulator_indicators.get("hardware_strings", [])
        
        # Look for Build.HARDWARE or similar property access
        if "HARDWARE" in sink_name or "getProperty" in sink_name or "build" in sink_name.lower():
            for arg in args:
                for hw_string in hardware_strings:
                    if hw_string.lower() in arg.lower():
                        confidence = self.confidence_levels["STRONG"]
                        if is_conditional:
                            confidence = min(confidence + 0.05, 1.0)
                        
                        evidence = f"Emulator hardware check: '{hw_string}' is known emulator hardware identifier"
                        return confidence, evidence
        
        return None, ""

    def _check_build_property_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        STRONG: Build property verification (FINGERPRINT, MODEL, DEVICE)
        Checks for "generic" or "sdk" patterns which indicate emulator.
        """
        build_props = self.emulator_indicators.get("build_properties", {})
        
        # Check fingerprint
        for arg in args:
            for fingerprint_indicator in build_props.get("fingerprint", []):
                if fingerprint_indicator.lower() in arg.lower():
                    confidence = self.confidence_levels["STRONG"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Emulator build property: FINGERPRINT contains '{fingerprint_indicator}'"
                    return confidence, evidence
            
            # Check model
            for model_indicator in build_props.get("model", []):
                if model_indicator.lower() in arg.lower():
                    confidence = self.confidence_levels["STRONG"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Emulator build property: MODEL contains '{model_indicator}'"
                    return confidence, evidence
            
            # Check device
            for device_indicator in build_props.get("device", []):
                if device_indicator.lower() in arg.lower():
                    confidence = self.confidence_levels["STRONG"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Emulator build property: DEVICE contains '{device_indicator}'"
                    return confidence, evidence
        
        return None, ""

    def _check_kernel_property_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        MEDIUM: Kernel property checks (ro.kernel.qemu, ro.hardware.virtual_device)
        """
        kernel_props = self.emulator_indicators.get("properties", [])
        
        for arg in args:
            for prop in kernel_props:
                if prop.lower() in arg.lower():
                    confidence = self.confidence_levels["MEDIUM"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Emulator kernel property: '{prop}' indicates virtual environment"
                    return confidence, evidence
        
        return None, ""

    def _check_sensor_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        MEDIUM: Sensor count verification
        Emulators typically have very few or no sensors.
        Look for sensor manager queries and count checks.
        """
        if "sensor" in sink_name.lower() or "SensorManager" in sink_name:
            # Look for patterns indicating sensor list retrieval and verification
            for arg in args:
                # Check for specific counts (emulators often have 0-2 sensors)
                if re.search(r'(sensor.*count|size.*<\s*[0-3]|getSensorList)', arg, re.IGNORECASE):
                    confidence = self.confidence_levels["MEDIUM"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Emulator sensor check: Limited sensor count detected (typical of emulator)"
                    return confidence, evidence
        
        return None, ""

    def is_false_positive(self, sink_hit) -> bool:
        """
        Mark as false positive if it's a utility function.
        """
        return self._is_utility_function(sink_hit)
