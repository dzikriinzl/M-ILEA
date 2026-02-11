"""
M-ILEA Report Generator v2.0
Integrates 4-category self-protection classification into analysis reports

Generates:
1. Categorized findings report (JSON)
2. Threat model assessment (JSON)
3. Vulnerability summary (JSON)
4. Hardening recommendations (JSON/Markdown)
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from core.patterns.self_protection_classifier import (
    SelfProtectionClassifier,
    classify_and_filter_findings
)


class CategoryReportGenerator:
    """Generates 4-category classification reports"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.classifier = SelfProtectionClassifier()
        self.output_dir = Path(output_dir) if output_dir else Path("evaluation/results")
    
    def generate_categorized_report(self, findings: List[Dict], app_name: str, 
                                   framework: Optional[str] = None) -> Dict:
        """Generate comprehensive categorized analysis report"""
        
        # Classify findings
        classified_report, vuln_summary = classify_and_filter_findings(findings, framework)
        
        # Enrich with metadata
        report = {
            "metadata": {
                "app_name": app_name,
                "framework": framework or "Unknown",
                "analysis_timestamp": datetime.now().isoformat(),
                "total_findings": len(findings),
                "framework_noise_count": vuln_summary["framework_noise"],
                "actual_self_protection_count": vuln_summary["actual_self_protection"],
                "classification_engine": "M-ILEA Self-Protection Classifier v2.0"
            },
            "findings_by_category": classified_report["classification_results"],
            "threat_model": classified_report["threat_model"],
            "vulnerability_statistics": vuln_summary,
            "unknown_findings": classified_report["unknown_classification"]
        }
        
        return report
    
    def generate_threat_level_assessment(self, report: Dict) -> Dict:
        """Assess overall threat level based on findings"""
        
        env_manip_detected = report["findings_by_category"]["environment_manipulation"]["count"] > 0
        analysis_prev_detected = report["findings_by_category"]["analysis_prevention"]["count"] > 0
        integrity_detected = report["findings_by_category"]["integrity_enforcement"]["count"] > 0
        sys_inter_detected = report["findings_by_category"]["system_interaction"]["count"] > 0
        
        # Determine threat level
        if env_manip_detected or analysis_prev_detected:
            threat_level = "HIGH"
            assessment = "Application implements anti-analysis mechanisms"
        elif integrity_detected and sys_inter_detected:
            threat_level = "MEDIUM"
            assessment = "Application has mixed security posture with both protection and vulnerabilities"
        elif integrity_detected:
            threat_level = "LOW"
            assessment = "Application implements legitimate security features without evasion"
        else:
            threat_level = "INFO"
            assessment = "No significant self-protection mechanisms detected"
        
        return {
            "threat_level": threat_level,
            "assessment": assessment,
            "evasion_tactics_found": env_manip_detected or analysis_prev_detected,
            "protection_mechanisms_found": integrity_detected,
            "vulnerability_exposure": sys_inter_detected
        }
    
    def save_json_report(self, report: Dict, output_path: str) -> str:
        """Save report as JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(output_file)
    
    def save_markdown_report(self, report: Dict, output_path: str) -> str:
        """Save report as Markdown"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        markdown_content = self._generate_markdown(report)
        
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        
        return str(output_file)
    
    def _generate_markdown(self, report: Dict) -> str:
        """Convert JSON report to Markdown format"""
        
        meta = report["metadata"]
        threat = report["threat_model"]
        findings = report["findings_by_category"]
        
        md = f"""# {meta["app_name"]} - 4-Category Self-Protection Analysis

**Framework:** {meta["framework"]}  
**Analysis Date:** {meta["analysis_timestamp"]}  
**Engine:** {meta["classification_engine"]}

## Summary

- **Total Findings:** {meta["total_findings"]}
- **Framework Noise:** {meta["framework_noise_count"]}
- **Actual Self-Protection:** {meta["actual_self_protection_count"]}

## Threat Assessment

**Level:** {threat.get("assessment", "Unknown")}

**Self-Protection Presence:** {threat.get("self_protection_presence", "Unknown")}  
**Evasion Mechanisms:** {threat.get("evasion_mechanisms", "Unknown")}

---

## Findings by Category

### 1. Environment Manipulation
**Status:** {findings["environment_manipulation"]["status"]}  
**Count:** {findings["environment_manipulation"]["count"]}

"""
        if findings["environment_manipulation"]["findings"]:
            md += "**Detected Mechanisms:**\n"
            for finding in findings["environment_manipulation"]["findings"][:10]:
                md += f"- {finding.get('protection_type', 'Unknown')} ({finding.get('location', {}).get('class', 'N/A')})\n"
        else:
            md += "No environment manipulation mechanisms detected.\n"
        
        md += f"""
### 2. Analysis Prevention
**Status:** {findings["analysis_prevention"]["status"]}  
**Count:** {findings["analysis_prevention"]["count"]}

"""
        if findings["analysis_prevention"]["findings"]:
            md += "**Detected Mechanisms:**\n"
            for finding in findings["analysis_prevention"]["findings"][:10]:
                md += f"- {finding.get('protection_type', 'Unknown')} ({finding.get('location', {}).get('class', 'N/A')})\n"
        else:
            md += "No analysis prevention mechanisms detected.\n"
        
        md += f"""
### 3. Integrity Enforcement
**Status:** {findings["integrity_enforcement"]["status"]}  
**Count:** {findings["integrity_enforcement"]["count"]}

"""
        if findings["integrity_enforcement"]["findings"]:
            md += "**Detected Mechanisms:**\n"
            for finding in findings["integrity_enforcement"]["findings"][:10]:
                md += f"- {finding.get('protection_type', 'Unknown')} ({finding.get('location', {}).get('class', 'N/A')})\n"
        else:
            md += "No integrity enforcement mechanisms detected.\n"
        
        md += f"""
### 4. System Interaction
**Status:** {findings["system_interaction"]["status"]}  
**Count:** {findings["system_interaction"]["count"]}

"""
        if findings["system_interaction"]["findings"]:
            md += "**Detected Mechanisms:**\n"
            for finding in findings["system_interaction"]["findings"][:10]:
                md += f"- {finding.get('protection_type', 'Unknown')} ({finding.get('location', {}).get('class', 'N/A')})\n"
        else:
            md += "No system interaction findings detected.\n"
        
        md += f"""
---

## Recommendations

"""
        for i, rec in enumerate(threat.get("hardening_recommendations", []), 1):
            md += f"{i}. {rec}\n"
        
        return md


def process_analysis_results(analysis_report: Dict, app_name: str) -> Dict:
    """
    Process M-ILEA analysis results through 4-category classification
    
    Args:
        analysis_report: Original M-ILEA analysis report (JSON)
        app_name: Application name (without .apk)
    
    Returns:
        Enhanced report with 4-category classification
    """
    
    generator = CategoryReportGenerator()
    findings = analysis_report.get("findings", [])
    framework = analysis_report.get("metadata", {}).get("framework", None)
    
    # Generate categorized report
    categorized_report = generator.generate_categorized_report(
        findings=findings,
        app_name=app_name,
        framework=framework
    )
    
    # Add threat level assessment
    threat_assessment = generator.generate_threat_level_assessment(categorized_report)
    categorized_report["threat_assessment"] = threat_assessment
    
    return categorized_report


def export_categorized_results(categorized_report: Dict, output_dir: str) -> Dict[str, str]:
    """
    Export categorized results to multiple formats
    
    Returns:
        Dictionary with file paths to generated reports
    """
    
    generator = CategoryReportGenerator(output_dir)
    app_name = categorized_report["metadata"]["app_name"].replace(".apk", "")
    output_paths = {}
    
    # Save JSON report
    json_path = f"{output_dir}/{app_name}/{app_name}_categorized_report.json"
    output_paths["json"] = generator.save_json_report(categorized_report, json_path)
    
    # Save Markdown report
    md_path = f"{output_dir}/{app_name}/{app_name}_categorized_report.md"
    output_paths["markdown"] = generator.save_markdown_report(categorized_report, md_path)
    
    return output_paths
