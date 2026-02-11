"""
M-ILEA Integration Module v2.0
Hooks the 4-category self-protection classifier into the main analysis pipeline

This module integrates:
1. Self-protection classification (4 categories)
2. Framework noise filtering
3. Threat level assessment
4. Enhanced reporting

Integration points:
- After deduplication in analyze.py
- Before report generation
- As post-processing step
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

from core.patterns.self_protection_classifier import (
    SelfProtectionClassifier,
    ProtectionCategory,
    classify_and_filter_findings
)
from core.report.category_reporter import (
    CategoryReportGenerator,
    process_analysis_results,
    export_categorized_results
)


class M2AnalysisIntegrator:
    """
    Integrates 4-category classification into M-ILEA analysis pipeline
    
    Workflow:
    1. Takes deduplicated findings from analyzer
    2. Classifies into 4 protection categories
    3. Filters framework noise
    4. Generates threat assessment
    5. Produces enhanced reports
    """
    
    def __init__(self, output_dir: str = "evaluation/results"):
        self.classifier = SelfProtectionClassifier()
        self.report_generator = CategoryReportGenerator(output_dir)
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger("M2Integration")
    
    def enrich_findings(self, findings: List[Dict], 
                       app_name: str,
                       framework: Optional[str] = None) -> List[Dict]:
        """
        Enrich findings with classification information
        
        Args:
            findings: List of deduplicated findings from analyzer
            app_name: Application name
            framework: Detected framework (e.g., Flutter)
        
        Returns:
            Enriched findings with category information
        """
        
        enriched = []
        
        for finding in findings:
            # Classify the finding
            category_result = self.classifier.classify_finding(finding)
            
            # Add classification to finding
            finding_enriched = finding.copy()
            finding_enriched["classification"] = {
                "category": category_result.category.value,
                "status": category_result.status,
                "confidence": category_result.confidence,
                "assessment": category_result.assessment
            }
            
            # Tag framework noise
            class_name = finding.get("location", {}).get("class", "").lower()
            noise_keywords = ["okhttp3", "chromium", "certificatetransparency", 
                            "trustkit", "boringssl", "android.webkit"]
            is_framework_noise = any(kw in class_name for kw in noise_keywords)
            finding_enriched["is_framework_noise"] = is_framework_noise
            
            enriched.append(finding_enriched)
        
        self.logger.info(f"Enriched {len(enriched)} findings with classification")
        return enriched
    
    def filter_framework_noise(self, findings: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Separate framework noise from actual self-protection mechanisms
        
        Returns:
            Tuple of (actual_findings, framework_noise)
        """
        
        actual_findings = []
        framework_noise = []
        
        for finding in findings:
            if finding.get("is_framework_noise", False):
                framework_noise.append(finding)
            else:
                actual_findings.append(finding)
        
        self.logger.info(f"Filtered: {len(actual_findings)} actual + {len(framework_noise)} noise")
        return actual_findings, framework_noise
    
    def generate_threat_assessment(self, findings: List[Dict]) -> Dict:
        """
        Generate threat level assessment from classified findings
        
        Returns:
            Threat assessment with level, mechanisms, and recommendations
        """
        
        # Count by category
        categories_found = {
            "environment_manipulation": 0,
            "analysis_prevention": 0,
            "integrity_enforcement": 0,
            "system_interaction": 0
        }
        
        for finding in findings:
            cat = finding.get("classification", {}).get("category", "unknown")
            if cat in categories_found:
                categories_found[cat] += 1
        
        # Determine threat level
        env_found = categories_found["environment_manipulation"] > 0
        analysis_found = categories_found["analysis_prevention"] > 0
        integrity_found = categories_found["integrity_enforcement"] > 0
        system_found = categories_found["system_interaction"] > 0
        
        if env_found or analysis_found:
            threat_level = "HIGH"
            assessment = "Application implements active anti-analysis mechanisms"
        elif integrity_found and system_found:
            threat_level = "MEDIUM"
            assessment = "Mixed security posture with both protections and vulnerabilities"
        elif integrity_found:
            threat_level = "LOW"
            assessment = "Legitimate security features without evasion"
        else:
            threat_level = "INFO"
            assessment = "No significant self-protection mechanisms"
        
        threat_model = {
            "threat_level": threat_level,
            "assessment": assessment,
            "categories_detected": [cat.replace("_", " ").title() for cat, count in categories_found.items() if count > 0],
            "categories_not_detected": [cat.replace("_", " ").title() for cat, count in categories_found.items() if count == 0],
            "environment_manipulation": categories_found["environment_manipulation"],
            "analysis_prevention": categories_found["analysis_prevention"],
            "integrity_enforcement": categories_found["integrity_enforcement"],
            "system_interaction": categories_found["system_interaction"],
            "evasion_tactics_found": env_found or analysis_found,
            "protection_mechanisms_found": integrity_found,
            "vulnerability_exposure": system_found,
            "hardening_recommendations": [
                "Validate all input data before processing",
                "Use EncryptedSharedPreferences for sensitive data",
                "Enforce HTTPS-only communication",
                "Remove world-readable file permissions",
                "Use strong cryptography (SHA-256+)",
                "Protect exported components"
            ]
        }
        
        self.logger.info(f"Threat level: {threat_level}")
        return threat_model
    
    def integrate_analysis(self, analysis_report: Dict, app_name: str) -> Dict:
        """
        Complete integration: classify, filter, assess, and generate reports
        
        Args:
            analysis_report: Original M-ILEA analysis report
            app_name: Application name (without extension)
        
        Returns:
            Enhanced report with 4-category classification
        """
        
        self.logger.info(f"Starting M2 integration for {app_name}")
        
        # Extract findings and metadata
        findings = analysis_report.get("findings", [])
        framework = analysis_report.get("metadata", {}).get("framework", None)
        
        # Step 1: Enrich findings with classification
        enriched_findings = self.enrich_findings(findings, app_name, framework)
        
        # Step 2: Filter framework noise
        actual_findings, noise = self.filter_framework_noise(enriched_findings)
        
        # Step 3: Generate threat assessment
        threat_assessment = self.generate_threat_assessment(actual_findings)
        
        # Step 4: Create integrated report
        integrated_report = {
            "metadata": {
                "app_name": app_name,
                "framework": framework,
                "original_findings_count": len(findings),
                "enriched_findings_count": len(enriched_findings),
                "actual_self_protection_count": len(actual_findings),
                "framework_noise_count": len(noise),
                "integration_engine": "M-ILEA v2.0 with 4-Category Classifier",
                "threat_level": threat_assessment["threat_level"]
            },
            "original_findings": analysis_report.get("findings", []),
            "enriched_findings": enriched_findings,
            "actual_findings": actual_findings,
            "framework_noise": noise,
            "threat_assessment": threat_assessment,
            "category_summary": {
                "environment_manipulation": threat_assessment["environment_manipulation"],
                "analysis_prevention": threat_assessment["analysis_prevention"],
                "integrity_enforcement": threat_assessment["integrity_enforcement"],
                "system_interaction": threat_assessment["system_interaction"]
            }
        }
        
        self.logger.info(f"Integration complete: {threat_assessment['threat_level']} threat level")
        return integrated_report
    
    def save_integrated_report(self, report: Dict, app_name: str) -> Dict[str, str]:
        """
        Save integrated report in multiple formats
        
        Returns:
            Dictionary with paths to generated files
        """
        
        output_paths = {}
        app_dir = self.output_dir / app_name / "m2_integration"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        json_path = app_dir / f"{app_name}_m2_integrated.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        output_paths["json"] = str(json_path)
        
        self.logger.info(f"Saved integrated report: {json_path}")
        
        # Save summary markdown
        md_path = app_dir / f"{app_name}_m2_summary.md"
        markdown = self._generate_summary_markdown(report)
        with open(md_path, 'w') as f:
            f.write(markdown)
        output_paths["markdown"] = str(md_path)
        
        self.logger.info(f"Saved summary: {md_path}")
        
        return output_paths
    
    def _generate_summary_markdown(self, report: Dict) -> str:
        """Generate summary markdown"""
        
        meta = report["metadata"]
        threat = report["threat_assessment"]
        cat_sum = report["category_summary"]
        
        md = f"""# M2 Integration Report - {meta['app_name']}

## Analysis Summary

- **Framework:** {meta['framework']}
- **Original Findings:** {meta['original_findings_count']}
- **After Enrichment:** {meta['enriched_findings_count']}
- **Actual Self-Protection:** {meta['actual_self_protection_count']}
- **Framework Noise:** {meta['framework_noise_count']}
- **Integration Engine:** {meta['integration_engine']}

## Threat Assessment

**Level:** {threat['threat_level']}  
**Assessment:** {threat['assessment']}

### Detection Results

- Environment Manipulation: {cat_sum['environment_manipulation']} findings
- Analysis Prevention: {cat_sum['analysis_prevention']} findings
- Integrity Enforcement: {cat_sum['integrity_enforcement']} findings
- System Interaction: {cat_sum['system_interaction']} findings

### Flags

- **Evasion Tactics Found:** {'YES' if threat['evasion_tactics_found'] else 'NO'}
- **Protection Mechanisms Found:** {'YES' if threat['protection_mechanisms_found'] else 'NO'}
- **Vulnerability Exposure:** {'YES' if threat['vulnerability_exposure'] else 'NO'}

## Recommendations

"""
        for i, rec in enumerate(threat["hardening_recommendations"], 1):
            md += f"{i}. {rec}\n"
        
        return md


def integrate_with_m_ilea(analysis_report: Dict, app_name: str, 
                         output_dir: str = "evaluation/results") -> Dict:
    """
    Convenience function to integrate analysis with M-ILEA
    
    Usage:
        integrated = integrate_with_m_ilea(analysis_report, "pinning.apk")
        integrator.save_integrated_report(integrated, "pinning")
    """
    
    integrator = M2AnalysisIntegrator(output_dir)
    integrated_report = integrator.integrate_analysis(analysis_report, app_name)
    
    return integrated_report
