"""
Deep Audit Pattern for Self-Protection & Anti-Analysis (Active Defense)

Focuses on active protection mechanisms only.
Criteria:
1. Anti-Debugging: isDebuggerConnected(), ApplicationInfo.flags & FLAG_DEBUGGABLE
2. Anti-Instrumentation (Frida/Xposed): String detection, StackTrace inspection
3. Signature Verification: getPackageInfo with GET_SIGNATURES, hash comparison
"""

import json
import logging
import re
from typing import List, Optional, Tuple
from core.patterns.base import BaseProtectionPattern
from core.analyzer.models import ProtectionCandidate


class SelfProtectionAudit(BaseProtectionPattern):
    PATTERN_NAME = "Self-Protection & Anti-Analysis (Active Defense)"
    IMPACT_HINT = "Active defense mechanism against debugging, instrumentation, or modification"

    def __init__(self):
        self.confidence_levels = {
            "HIGH": 0.85,       # Direct API checks (isDebuggerConnected, getPackageInfo)
            "STRONG": 0.75,     # Signature verification or StackTrace analysis
            "MEDIUM": 0.65      # Indirect checks (property verification)
        }
        
        try:
            with open("data/indicators.json") as f:
                self.indicators = json.load(f)
                self.anti_analysis = self.indicators.get("anti_analysis", {})
                self.utility_ignore = self.indicators.get("utility_methods_to_ignore", [])
        except Exception as e:
            logging.error(f"Failed to load indicators: {e}")
            self.anti_analysis = {}
            self.utility_ignore = []

    def match(self, sink_hit, context=None) -> Optional[ProtectionCandidate]:
        """
        Match self-protection/anti-analysis logic.
        Focuses on active defense mechanisms.
        """
        if sink_hit.sink.get("risk") not in ["Anti-Debugging", "Anti-Debugging Logic", "Anti-Analysis"]:
            return None

        # Filter: Ignore utility functions
        if self._is_utility_function(sink_hit):
            return None

        # Evaluate protection mechanism
        confidence, evidence = self._evaluate_protection_logic(sink_hit)

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

    def _evaluate_protection_logic(self, sink_hit) -> Tuple[Optional[float], str]:
        """
        Evaluate the actual protection logic.
        Returns (confidence_score, evidence_text) or (None, "") if not protection logic.
        """
        all_args = getattr(sink_hit, 'arguments', [])
        sink_name = sink_hit.sink.get('name', '')
        is_conditional = getattr(sink_hit, 'conditional', False)

        # HIGH: Anti-Debugging Check (isDebuggerConnected, FLAG_DEBUGGABLE)
        confidence, evidence = self._check_anti_debugging(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # HIGH: Anti-Instrumentation Detection (Frida, Xposed)
        confidence, evidence = self._check_anti_instrumentation(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        # STRONG: Signature Verification (getPackageInfo, SHA hash comparison)
        confidence, evidence = self._check_signature_verification(all_args, sink_name, is_conditional)
        if confidence:
            return confidence, evidence

        return None, ""

    def _check_anti_debugging(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        HIGH: Anti-debugging mechanisms
        isDebuggerConnected(), ApplicationInfo.flags & FLAG_DEBUGGABLE
        """
        anti_debug = self.anti_analysis.get("anti_debugging", [])
        
        for api in anti_debug:
            if api.lower() in sink_name.lower():
                confidence = self.confidence_levels["HIGH"]
                if is_conditional:
                    confidence = min(confidence + 0.05, 1.0)
                
                # Determine specific type
                if "isDebuggerConnected" in api:
                    evidence = f"Anti-debugging: Direct debugger connection check via {api}"
                elif "FLAG_DEBUGGABLE" in api or "debuggable" in api.lower():
                    evidence = f"Anti-debugging: Debuggable flag verification via {api}"
                else:
                    evidence = f"Anti-debugging: Debug mode detection via {api}"
                
                return confidence, evidence
        
        # Also check arguments
        for arg in args:
            for api in anti_debug:
                if api.lower() in arg.lower():
                    confidence = self.confidence_levels["HIGH"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Anti-debugging: {api} detected in decision logic"
                    return confidence, evidence
        
        return None, ""

    def _check_anti_instrumentation(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        HIGH: Anti-instrumentation/Anti-tampering mechanisms
        Detects frameworks like Frida, Xposed, or LD_PRELOAD tricks
        """
        anti_instr = self.anti_analysis.get("anti_instrumentation", [])
        
        for framework in anti_instr:
            # Check in method name
            if framework.lower() in sink_name.lower():
                confidence = self.confidence_levels["HIGH"]
                if is_conditional:
                    confidence = min(confidence + 0.05, 1.0)
                
                if "frida" in framework.lower():
                    evidence = f"Anti-instrumentation: Frida/GumJS detection mechanism"
                elif "xposed" in framework.lower():
                    evidence = f"Anti-instrumentation: Xposed framework detection"
                elif "LD_PRELOAD" in framework:
                    evidence = f"Anti-instrumentation: LD_PRELOAD hook detection"
                else:
                    evidence = f"Anti-instrumentation: {framework} detection mechanism"
                
                return confidence, evidence
            
            # Check in arguments
            for arg in args:
                if framework.lower() in arg.lower():
                    confidence = self.confidence_levels["HIGH"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Anti-instrumentation: String literal '{framework}' indicates {framework} detection"
                    return confidence, evidence
        
        # Also check for StackTrace analysis (common in anti-instrumentation)
        if "StackTrace" in sink_name or "getStackTrace" in sink_name:
            for arg in args:
                if "xposed" in arg.lower() or "frida" in arg.lower():
                    confidence = self.confidence_levels["STRONG"]
                    evidence = f"Anti-instrumentation: StackTrace inspection for framework detection"
                    return confidence, evidence
        
        return None, ""

    def _check_signature_verification(self, args: List[str], sink_name: str, is_conditional: bool) -> Tuple[Optional[float], str]:
        """
        STRONG: Signature verification and tampering detection
        getPackageInfo with GET_SIGNATURES, hash comparison (SHA1/SHA256)
        """
        sig_verification = self.anti_analysis.get("signature_verification", [])
        
        # Check for getPackageInfo API
        if "getPackageInfo" in sink_name or "PackageManager" in sink_name:
            for arg in args:
                if "GET_SIGNATURES" in arg or "SIGNATURES" in arg:
                    confidence = self.confidence_levels["STRONG"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Signature verification: Package signature retrieval for integrity check"
                    return confidence, evidence
        
        # Check for hash algorithms (SHA1, SHA256)
        hash_patterns = [r"MessageDigest", r"SHA1", r"SHA256", r"SHA-1", r"SHA-256"]
        
        for arg in args:
            for pattern in hash_patterns:
                if pattern in arg:
                    confidence = self.confidence_levels["STRONG"]
                    if is_conditional:
                        confidence = min(confidence + 0.05, 1.0)
                    
                    evidence = f"Signature verification: Hash algorithm '{pattern}' for certificate validation"
                    return confidence, evidence
        
        # Check method names for signature/hash comparison
        sig_methods = ["verifySig", "checkSignature", "compareHash", "validateCert"]
        
        for method in sig_methods:
            if method.lower() in sink_name.lower():
                confidence = self.confidence_levels["STRONG"]
                if is_conditional:
                    confidence = min(confidence + 0.05, 1.0)
                
                evidence = f"Signature verification: Certificate/signature validation via {method}"
                return confidence, evidence
        
        return None, ""

    def is_false_positive(self, sink_hit) -> bool:
        """
        Mark as false positive if it's a utility function or generic logging.
        """
        return self._is_utility_function(sink_hit)
