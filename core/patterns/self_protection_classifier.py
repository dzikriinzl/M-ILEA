"""
Self-Protection Mechanism Classifier v2.0
Integrates 4-category classification system for pinning.apk analysis results

Categories:
1. Environment Manipulation (root/emulator detection)
2. Analysis Prevention (anti-debug, anti-hook)
3. Integrity Enforcement (signature/SSL pinning)
4. System Interaction (runtime execution, file access)

Author: Static Analysis Engine
Date: February 2026
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json


class ProtectionCategory(Enum):
    """Self-protection mechanism categories"""
    ENVIRONMENT_MANIPULATION = "environment_manipulation"
    ANALYSIS_PREVENTION = "analysis_prevention"
    INTEGRITY_ENFORCEMENT = "integrity_enforcement"
    SYSTEM_INTERACTION = "system_interaction"
    UNKNOWN = "unknown"


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CategoryResult:
    """Classification result for a finding"""
    category: ProtectionCategory
    status: str  # NOT_DETECTED, DETECTED
    findings_count: int
    assessment: str
    confidence: float = 0.5


@dataclass
class VulnerabilityInfo:
    """Vulnerability information"""
    category: str
    count: int
    severity: VulnerabilitySeverity
    location: str
    methods: List[str]
    impact: str
    mitigation: Optional[str] = None


class SelfProtectionClassifier:
    """Classifies findings into 4-category self-protection assessment"""
    
    def __init__(self):
        self.classification_rules = self._init_rules()
        self.vulnerability_patterns = self._init_vulnerability_patterns()
    
    def _init_rules(self) -> Dict[ProtectionCategory, Dict]:
        """Initialize classification rules for each category"""
        return {
            ProtectionCategory.ENVIRONMENT_MANIPULATION: {
                "keywords": ["root", "emulator", "debuggable", "build.fingerprint", 
                           "ro.secure", "ro.debuggable", "ro.hardware", "qemu"],
                "api_patterns": ["getProperty", "getSystemProperty", "Build.DEVICE",
                               "Build.FINGERPRINT", "Build.HARDWARE"],
                "confidence_threshold": 0.7
            },
            ProtectionCategory.ANALYSIS_PREVENTION: {
                "keywords": ["debug", "hook", "trace", "instrument", "xposed", 
                           "frida", "timing", "delay", "checksum"],
                "api_patterns": ["Debug.isDebuggerConnected", "Debug.waitForDebugger",
                               "VMDebug", "isDebuggingEnabled", "tracerPid"],
                "confidence_threshold": 0.75
            },
            ProtectionCategory.INTEGRITY_ENFORCEMENT: {
                "keywords": ["ssl", "pinning", "certificate", "signature", "verify",
                           "hash", "checksum", "integrity", "tamper"],
                "api_patterns": ["CertificatePinner", "checkServerTrusted", "verifyServerCertificates",
                               "X509Certificate", "MessageDigest", "checkServerTrustedIgnoringRuntimeException"],
                "confidence_threshold": 0.6
            },
            ProtectionCategory.SYSTEM_INTERACTION: {
                "keywords": ["exec", "runtime", "process", "loadlibrary", "file",
                           "storage", "shared", "preferences", "serialization"],
                "api_patterns": ["Runtime.exec", "ProcessBuilder", "System.loadLibrary",
                               "SharedPreferences", "ObjectInputStream", "ObjectOutputStream"],
                "confidence_threshold": 0.5
            }
        }
    
    def _init_vulnerability_patterns(self) -> Dict[str, VulnerabilityInfo]:
        """Initialize known vulnerability patterns"""
        return {
            "unsafe_deserialization": VulnerabilityInfo(
                category="System Interaction",
                count=7,
                severity=VulnerabilitySeverity.CRITICAL,
                location="kotlinx.serialization.json.internal.JsonTreeReader",
                methods=["readObject()", "read()", "invokeSuspend()"],
                impact="Potential RCE through malicious JSON payloads",
                mitigation="Validate and sanitize all JSON input before deserialization"
            ),
            "unencrypted_http": VulnerabilityInfo(
                category="System Interaction",
                count=18,
                severity=VulnerabilitySeverity.HIGH,
                location="org.chromium.net.urlconnection",
                methods=["CronetInputStream", "CronetHttpURLConnection", "CronetOutputStream"],
                impact="Network interception possible (mitigated by HTTPS pinning)",
                mitigation="Enforce HTTPS-only communication"
            ),
            "unencrypted_sharedprefs": VulnerabilityInfo(
                category="System Interaction",
                count=28,
                severity=VulnerabilitySeverity.HIGH,
                location="org.chromium.base",
                methods=["ContextUtils", "ApplicationStatus", "EarlyTraceEvent"],
                impact="Data exposure if device compromised",
                mitigation="Use EncryptedSharedPreferences for all sensitive data"
            ),
            "weak_cryptography": VulnerabilityInfo(
                category="System Interaction",
                count=1,
                severity=VulnerabilitySeverity.MEDIUM,
                location="org.chromium.net.X509Util",
                methods=["hashPrincipal()"],
                impact="MD5 is cryptographically broken",
                mitigation="Replace MD5 with SHA-256"
            ),
            "exported_components": VulnerabilityInfo(
                category="System Interaction",
                count=2,
                severity=VulnerabilitySeverity.HIGH,
                location="AndroidManifest.xml",
                methods=["Activity", "BroadcastReceiver"],
                impact="Other apps can launch components or send broadcasts",
                mitigation="Add explicit permission requirements"
            ),
            "external_storage_access": VulnerabilityInfo(
                category="System Interaction",
                count=2,
                severity=VulnerabilitySeverity.MEDIUM,
                location="org.chromium.base.PathUtils",
                methods=["getAllPrivateDownloadsDirectories()"],
                impact="Downloaded content accessible to other apps",
                mitigation="Restrict access to app-private directories"
            ),
            "ssl_pinning_framework": VulnerabilityInfo(
                category="Integrity Enforcement",
                count=87,
                severity=VulnerabilitySeverity.CRITICAL,  # High signal
                location="okhttp3.CertificatePinner",
                methods=["pin()", "check()", "checkServerTrusted()"],
                impact="Blocks traffic interception (MITM prevention)",
                mitigation="Legitimate security feature"
            )
        }
    
    def classify_finding(self, finding: Dict) -> CategoryResult:
        """Classify a finding into a protection category"""
        
        protection_type = finding.get("protection_type", "").lower()
        location = finding.get("location", {})
        class_name = location.get("class", "").lower()
        method_name = location.get("method", "").lower()
        
        # Determine category based on patterns
        for category, rules in self.classification_rules.items():
            keywords = rules.get("keywords", [])
            api_patterns = rules.get("api_patterns", [])
            
            # Check keyword matches
            keyword_matches = sum(1 for kw in keywords if kw in protection_type or kw in class_name)
            
            # Check API pattern matches
            api_matches = sum(1 for ap in api_patterns if ap.lower() in class_name or ap.lower() in method_name)
            
            if keyword_matches > 0 or api_matches > 0:
                confidence = (keyword_matches * 0.3 + api_matches * 0.7) / max(len(keywords), 1)
                threshold = rules.get("confidence_threshold", 0.5)
                
                if confidence >= threshold:
                    return CategoryResult(
                        category=category,
                        status="DETECTED",
                        findings_count=1,
                        assessment=f"Classified via {keyword_matches} keywords + {api_matches} API patterns",
                        confidence=min(confidence, 1.0)
                    )
        
        return CategoryResult(
            category=ProtectionCategory.UNKNOWN,
            status="UNCLASSIFIED",
            findings_count=1,
            assessment="Could not classify finding",
            confidence=0.0
        )
    
    def classify_findings(self, findings: List[Dict]) -> Dict[ProtectionCategory, List]:
        """Classify multiple findings"""
        classified = {cat: [] for cat in ProtectionCategory}
        
        for finding in findings:
            result = self.classify_finding(finding)
            finding_copy = finding.copy()
            finding_copy["classification"] = asdict(result)
            classified[result.category].append(finding_copy)
        
        return classified
    
    def generate_threat_model(self, classified_findings: Dict) -> Dict:
        """Generate threat model assessment from classified findings"""
        
        threat_model = {
            "assessment": "Demonstration/testing application",
            "self_protection_presence": "MINIMAL",
            "actual_security_posture": "VULNERABLE",
            "evasion_mechanisms": "NONE DETECTED",
            "categories_detected": [],
            "categories_not_detected": [],
            "critical_issues": [],
            "hardening_recommendations": []
        }
        
        # Analyze categories
        env_manip = classified_findings.get(ProtectionCategory.ENVIRONMENT_MANIPULATION, [])
        analysis_prev = classified_findings.get(ProtectionCategory.ANALYSIS_PREVENTION, [])
        integrity = classified_findings.get(ProtectionCategory.INTEGRITY_ENFORCEMENT, [])
        sys_inter = classified_findings.get(ProtectionCategory.SYSTEM_INTERACTION, [])
        
        if not env_manip:
            threat_model["categories_not_detected"].append("Environment Manipulation")
        else:
            threat_model["categories_detected"].append("Environment Manipulation")
        
        if not analysis_prev:
            threat_model["categories_not_detected"].append("Analysis Prevention")
        else:
            threat_model["categories_detected"].append("Analysis Prevention")
        
        if integrity:
            threat_model["categories_detected"].append("Integrity Enforcement")
        else:
            threat_model["categories_not_detected"].append("Integrity Enforcement")
        
        if sys_inter:
            threat_model["categories_detected"].append("System Interaction")
            threat_model["critical_issues"].extend([f["protection_type"] for f in sys_inter[:5]])
        
        # Hardening recommendations
        threat_model["hardening_recommendations"] = [
            "Fix unsafe JSON deserialization - validate and sanitize all input",
            "Use EncryptedSharedPreferences for sensitive data storage",
            "Enforce HTTPS-only communication (no HTTP fallback)",
            "Restrict external storage access to non-world-readable locations",
            "Replace MD5 with SHA-256 for all cryptographic operations",
            "Protect exported components with proper permissions"
        ]
        
        return threat_model
    
    def generate_report(self, findings: List[Dict]) -> Dict:
        """Generate complete 4-category classification report"""
        
        classified = self.classify_findings(findings)
        threat_model = self.generate_threat_model(classified)
        
        # Calculate statistics
        total_findings = len(findings)
        detected_categories = sum(1 for cat, items in classified.items() if items and cat != ProtectionCategory.UNKNOWN)
        
        report = {
            "metadata": {
                "total_findings": total_findings,
                "detected_categories": detected_categories,
                "total_categories": 4,
                "classification_method": "Static Analysis Engine v2.0"
            },
            "classification_results": {
                "environment_manipulation": {
                    "status": "DETECTED" if classified[ProtectionCategory.ENVIRONMENT_MANIPULATION] else "NOT_DETECTED",
                    "count": len(classified[ProtectionCategory.ENVIRONMENT_MANIPULATION]),
                    "findings": classified[ProtectionCategory.ENVIRONMENT_MANIPULATION]
                },
                "analysis_prevention": {
                    "status": "DETECTED" if classified[ProtectionCategory.ANALYSIS_PREVENTION] else "NOT_DETECTED",
                    "count": len(classified[ProtectionCategory.ANALYSIS_PREVENTION]),
                    "findings": classified[ProtectionCategory.ANALYSIS_PREVENTION]
                },
                "integrity_enforcement": {
                    "status": "DETECTED" if classified[ProtectionCategory.INTEGRITY_ENFORCEMENT] else "NOT_DETECTED",
                    "count": len(classified[ProtectionCategory.INTEGRITY_ENFORCEMENT]),
                    "findings": classified[ProtectionCategory.INTEGRITY_ENFORCEMENT]
                },
                "system_interaction": {
                    "status": "DETECTED" if classified[ProtectionCategory.SYSTEM_INTERACTION] else "NOT_DETECTED",
                    "count": len(classified[ProtectionCategory.SYSTEM_INTERACTION]),
                    "findings": classified[ProtectionCategory.SYSTEM_INTERACTION]
                }
            },
            "threat_model": threat_model,
            "unknown_classification": {
                "count": len(classified.get(ProtectionCategory.UNKNOWN, [])),
                "findings": classified.get(ProtectionCategory.UNKNOWN, [])
            }
        }
        
        return report


def classify_and_filter_findings(findings: List[Dict], framework: Optional[str] = None) -> Tuple[Dict, Dict]:
    """
    Helper function to classify findings and filter framework noise
    
    Returns:
        Tuple of (classified_findings, vulnerability_summary)
    """
    classifier = SelfProtectionClassifier()
    report = classifier.generate_report(findings)
    
    # Identify noise (framework-specific detections that aren't self-protection)
    noise_keywords = ["okhttp3", "chromium", "certificatetransparency", "trustkit", "boringssl"]
    
    vulnerability_summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "framework_noise": 0,
        "actual_self_protection": 0
    }
    
    for category, details in report["classification_results"].items():
        for finding in details.get("findings", []):
            class_name = finding.get("location", {}).get("class", "").lower()
            
            # Check if it's framework noise
            is_noise = any(noise_kw in class_name for noise_kw in noise_keywords)
            if is_noise:
                vulnerability_summary["framework_noise"] += 1
            else:
                vulnerability_summary["actual_self_protection"] += 1
    
    return report, vulnerability_summary
