"""
Deep Audit Pattern for Root Detection (High Confidence)

Focuses on Final Decision Logic only, filtering out utility functions.
Criteria:
1. File Existence Checks: /system/bin/su, /sbin/su, /system/app/Superuser.apk
2. Package Manager Checks: com.noshufou.android.su, eu.chainfire.supersu, com.topjohnwu.magisk
3. Execution Checks: Runtime.exec() with su/which su/id commands
4. Read-Only File System Checks: mount -o rw attempts
"""

import json
import logging
import re
from typing import List, Optional, Tuple
from core.patterns.base import BaseProtectionPattern
from core.analyzer.models import ProtectionCandidate


class RootDetectionAudit(BaseProtectionPattern):
    PATTERN_NAME = "Root Detection (High Confidence)"
    IMPACT_HINT = "Detects device root status with high confidence decision logic"

    def __init__(self):
        self.confidence_levels = {
            "HIGH": 0.9,      # Explicit root-check package or su command execution
            "MEDIUM": 0.7,    # File existence checks in decision logic
            "LOW": 0.4        # Utility functions or indirect checks
        }
        
        try:
            with open("data/indicators.json") as f:
                self.indicators = json.load(f)
                self.root_indicators = self.indicators.get("root_indicators", {})
                self.utility_ignore = self.indicators.get("utility_methods_to_ignore", [])
        except Exception as e:
            logging.error(f"Failed to load indicators: {e}")
            self.root_indicators = {}
            self.utility_ignore = []

    def match(self, sink_hit, context=None) -> Optional[ProtectionCandidate]:
        """
        Match root detection logic with confidence scoring.
        Filters out noise by ignoring utility functions.
        """
        if sink_hit.sink.get("risk") not in ["Root Detection", "Environment Verification"]:
            return None

        # Filter 1: Ignore utility functions
        if self._is_utility_function(sink_hit):
            return None

        # Filter 2: Check for final decision logic (not just utility calls)
        confidence, evidence = self._evaluate_decision_logic(sink_hit)

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
        Filter out utility functions like hex conversion, list processing, etc.
        """
        method_name = sink_hit.method_name.lower()
        
        # Utility function patterns
        utility_patterns = [
            r"tohex",
            r"hexto",
            r"byte.*array",
            r"encode",
            r"decode",
            r"format.*string",
            r"serialize",
            r"deserialize",
            r"parse.*json",
            r".*_utils$",
            r"^get[a-z]*$",
            r"init.*array",
            r"fill.*array"
        ]
        
        for pattern in utility_patterns:
            if re.search(pattern, method_name):
                return True
        
        # Check if method name is in the ignore list
        for utility_method in self.utility_ignore:
            if utility_method.lower() in method_name:
                return True
        
        return False

    def _evaluate_decision_logic(self, sink_hit) -> Tuple[Optional[float], str]:
        """
        Evaluate the actual decision logic for root detection.
        Returns (confidence_score, evidence_text) or (None, "") if not root detection.
        """
        all_args = getattr(sink_hit, 'arguments', [])
        context_snippet = getattr(sink_hit, 'context_snippet', [])
        sink_name = sink_hit.sink.get('name', '')
        is_conditional = getattr(sink_hit, 'conditional', False)

        # HIGH CONFIDENCE: Package Manager Root Checks
        confidence, evidence = self._check_package_manager_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # HIGH CONFIDENCE: Execution Command Detection (su, which su, id)
        confidence, evidence = self._check_execution_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # MEDIUM CONFIDENCE: File Existence Checks
        confidence, evidence = self._check_file_existence_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # MEDIUM CONFIDENCE: Mount/Read-Only FS Checks
        confidence, evidence = self._check_mount_detection(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        return None, ""

    def _check_package_manager_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        HIGH CONFIDENCE: Package manager checks for root apps
        (com.topjohnwu.magisk, eu.chainfire.supersu, etc.)
        """
        package_checks = self.root_indicators.get("package_checks", [])
        
        for arg in args:
            for package in package_checks:
                if package.lower() in arg.lower():
                    confidence = self.confidence_levels["HIGH"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Root app package check: {package} detected in {sink_name}"
                    return confidence, evidence
        
        return None, ""

    def _check_execution_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        HIGH CONFIDENCE: Execution of su, which su, id commands
        These are definitive root-check commands.
        """
        execution_commands = self.root_indicators.get("execution_commands", [])
        
        # Look for Runtime.exec pattern
        if "exec" in sink_name.lower() or "Runtime" in sink_name:
            for arg in args:
                for cmd in execution_commands:
                    # Exact match or command at word boundary
                    if cmd.lower() == arg.lower() or f" {cmd}" in f" {arg}".lower():
                        confidence = self.confidence_levels["HIGH"]
                        if is_conditional:
                            confidence = min(confidence + 0.05, 1.0)
                        
                        evidence = f"Root execution check: '{cmd}' command via {sink_name}"
                        return confidence, evidence
        
        return None, ""

    def _check_file_existence_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        MEDIUM CONFIDENCE: File existence checks for su binaries
        Only confidence if in conditional context (decision logic).
        """
        if not is_conditional:
            return None, ""  # Ignore file checks outside decision logic

        file_checks = self.root_indicators.get("file_existence_checks", [])
        
        for arg in args:
            for file_path in file_checks:
                if file_path.lower() in arg.lower():
                    confidence = self.confidence_levels["MEDIUM"]
                    evidence = f"Root file check: {file_path} in decision logic"
                    return confidence, evidence
        
        return None, ""

    def _check_mount_detection(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        MEDIUM CONFIDENCE: Read-only filesystem mount checks
        Attempts to remount /system as rw.
        """
        mount_patterns = [r"mount.*-o.*rw", r"mount.*system", r"ro\.secure"]
        
        for arg in args:
            for pattern in mount_patterns:
                if re.search(pattern, arg.lower()):
                    confidence = self.confidence_levels["MEDIUM"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Mount/RO-FS check: {arg} detected in {sink_name}"
                    return confidence, evidence
        
        return None, ""

    def is_false_positive(self, sink_hit) -> bool:
        """
        Mark as false positive if it's a utility function or benign check.
        """
        return self._is_utility_function(sink_hit)
