import json
import os
from datetime import datetime
from core.vulnerability_visualizer import get_vulnerability_html_card

class HTMLReportGenerator:
    def __init__(self, output_path):
        self.output_path = output_path

    def _get_current_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _deduplicate_findings(self, findings):
        """
        Menghilangkan looping evidence yang sama dengan mengecek 
        kombinasi protection_type, class, method, dan isi snippet.
        """
        unique_findings = []
        seen_fingerprints = set()
        
        for f in findings:
            snippet_str = "".join(f.get('evidence_snippet', []))
            # Membuat fingerprint unik
            fingerprint = (
                f.get('protection_type'),
                f.get('location', {}).get('class'),
                f.get('location', {}).get('method'),
                hash(snippet_str)
            )
            
            if fingerprint not in seen_fingerprints:
                unique_findings.append(f)
                seen_fingerprints.add(fingerprint)
        
        return unique_findings

    def generate(self, metadata, findings, chart_images, vulnerabilities=None, metrics=None):
        # 1. Deduplikasi data agar tidak looping
        findings = self._deduplicate_findings(findings)
        
        # 2. Grouping berdasarkan kategori
        grouped = {}
        for f in findings:
            cat = f['protection_type']
            if cat not in grouped: grouped[cat] = []
            grouped[cat].append(f)

        # 3. Menangani Multiple Charts (Revisi: Loop melalui semua chart)
        charts_html = ""
        if chart_images:
            for img_path in chart_images:
                charts_html += f"""
                <div class="chart-box">
                    <img src="{img_path}" alt="Security Visualization">
                </div>
                """
        else:
            charts_html = '<div class="chart-box"><span>No visual data available</span></div>'

        # 4. Build Enhanced Vulnerability Section with Charts and OWASP MSTG Mapping
        if vulnerabilities:
            vuln_html = get_vulnerability_html_card(vulnerabilities, metadata)
        else:
            vuln_html = f"""
            <div class="card vulnerability-card">
                <h2>Vulnerability Analysis (v2.0)</h2>
                <div class="vuln-grid">
                    <div class="vuln-stat critical"><span class="vuln-num">0</span><span>Critical</span></div>
                    <div class="vuln-stat high"><span class="vuln-num">0</span><span>High</span></div>
                    <div class="vuln-stat medium"><span class="vuln-num">0</span><span>Medium</span></div>
                    <div class="vuln-stat low"><span class="vuln-num">0</span><span>Low</span></div>
                </div>
            </div>
            """

        # 5. Build Metrics Section for Research (always show, even if 0)
        metrics_html = f"""
        <div class="card metrics-card">
            <h2>Confidence Metrics (v2.0)</h2>
            <div class="metrics-grid">
                <div class="metric-item">
                    <span class="metric-label">Mean Confidence</span>
                    <span class="metric-value">{metrics.get('mean', 0):.3f}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Median Confidence</span>
                    <span class="metric-value">{metrics.get('median', 0):.3f}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Std Deviation</span>
                    <span class="metric-value">{metrics.get('std_dev', 0):.3f}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Score Range</span>
                    <span class="metric-value">{metrics.get('min', 0):.3f} - {metrics.get('max', 0):.3f}</span>
                </div>
            </div>
        </div>
        """
        
        # 6. Build Vulnerability Details Section with Evidence
        vuln_details_html = ""
        if vulnerabilities:
            vuln_details_html += """
            <div class="card vulnerability-details">
                <h2>Vulnerability Evidence & Details</h2>
                <div class="vulnerability-list">
            """
            
            # Group vulnerabilities by type for better organization
            by_type = {}
            for v in vulnerabilities:
                v_type = v.get('name') if isinstance(v, dict) else getattr(v, 'name', 'Unknown')
                if v_type not in by_type:
                    by_type[v_type] = []
                by_type[v_type].append(v)
            
            # Display grouped vulnerabilities
            for vuln_type, vulns in sorted(by_type.items()):
                sev = vulns[0].get('severity') if isinstance(vulns[0], dict) else getattr(vulns[0], 'severity')
                sev_class = sev.lower() if sev else "info"
                
                vuln_details_html += f"""
                <div class="vuln-detail-group">
                    <div class="vuln-detail-header" onclick="toggleVulnDetail(this)">
                        <span class="badge badge-{sev_class}">{sev}</span>
                        <span class="vuln-type-name">{vuln_type}</span>
                        <span class="vuln-count">({len(vulns)} instances)</span>
                        <span class="chevron">▼</span>
                    </div>
                    <div class="vuln-detail-content">
                """
                
                # Show all instances of this vulnerability type
                for i, v in enumerate(vulns[:5]):  # Show first 5
                    location = v.get('location') if isinstance(v, dict) else getattr(v, 'location', {})
                    evidence = v.get('evidence') if isinstance(v, dict) else getattr(v, 'evidence', [])
                    source_code = v.get('source_code') if isinstance(v, dict) else getattr(v, 'source_code', '')
                    description = v.get('description') if isinstance(v, dict) else getattr(v, 'description', '')
                    remediation = v.get('remediation') if isinstance(v, dict) else getattr(v, 'remediation', '')
                    owasp = v.get('owasp_mstg') if isinstance(v, dict) else getattr(v, 'owasp_mstg', 'N/A')
                    
                    # Format location
                    if isinstance(location, dict):
                        if location.get('type') == 'manifest':
                            loc_str = f"<code>{location.get('component', 'Unknown')}</code> in <strong>AndroidManifest.xml</strong>"
                        else:
                            loc_str = f"<code>{location.get('class', 'Unknown')}.{location.get('method', '')}</code> ({location.get('file', 'Unknown')})"
                    else:
                        loc_str = str(location)
                    
                    vuln_details_html += f"""
                        <div class="vuln-instance">
                            <div class="instance-header">
                                <strong>Instance {i+1}</strong>
                                <span class="instance-location">{loc_str}</span>
                            </div>
                            <div class="instance-meta">
                                <span><strong>OWASP MSTG:</strong> <code>{owasp}</code></span>
                                <span><strong>Category:</strong> {v.get('category') if isinstance(v, dict) else getattr(v, 'category', 'Unknown')}</span>
                            </div>
                    """
                    
                    # Show evidence code
                    if evidence:
                        vuln_details_html += """
                            <div class="evidence-container">
                                <div class="evidence-label">Evidence:</div>
                                <div class="code-snippet">
                        """
                        for line in evidence[:10]:  # Show first 10 lines
                            # Escape HTML
                            line_safe = str(line).replace('<', '&lt;').replace('>', '&gt;')
                            vuln_details_html += f'<div class="code-line">{line_safe}</div>'
                        
                        if len(evidence) > 10:
                            vuln_details_html += f'<div class="code-line">... and {len(evidence)-10} more lines</div>'
                        
                        vuln_details_html += """
                                </div>
                            </div>
                        """
                    
                    # Show description and remediation
                    if description or remediation:
                        vuln_details_html += f"""
                            <div class="instance-details">
                        """
                        if description:
                            vuln_details_html += f"""
                                <div class="detail-section">
                                    <strong>Description:</strong>
                                    <p>{description}</p>
                                </div>
                            """
                        if remediation:
                            vuln_details_html += f"""
                                <div class="detail-section remediation">
                                    <strong>Remediation:</strong>
                                    <p>{remediation}</p>
                                </div>
                            """
                        vuln_details_html += """
                            </div>
                        """
                    
                    vuln_details_html += """
                        </div>
                    """
                
                # Show "more" message if truncated
                if len(vulns) > 5:
                    vuln_details_html += f"""
                        <div class="more-instances">
                            ... and {len(vulns) - 5} more instances of {vuln_type}
                        </div>
                    """
                
                vuln_details_html += """
                    </div>
                </div>
                """
            
            vuln_details_html += """
                </div>
            </div>
            """

        # 6. Build Accordion & Findings
        accordion_html = ""
        for category, items in grouped.items():
            accordion_html += f"""
            <div class="category-wrapper">
                <button class="accordion-header" onclick="toggleAccordion(this)">
                    <div class="header-left">
                        <span class="chevron">▶</span>
                        <span class="cat-title">{category}</span>
                    </div>
                    <span class="cat-count">{len(items)} Detections</span>
                </button>
                <div class="accordion-content">
            """
            for f in items:
                # Evidence Highlighting Logic
                evidence_html = ""
                snippet = f.get('evidence_snippet', [])
                
                for line in snippet:
                    # Deteksi marker: [*] untuk sink, [!] untuk decision point
                    is_sink = "[*]" in line
                    is_decision = "[!]" in line
                    
                    # Replace markers dengan emoji
                    clean_line = line.replace("[*]", "🎯")  # Sink marker
                    clean_line = clean_line.replace("[!]", "⚡")  # Decision point marker
                    
                    # Extract line content untuk cek apakah meaningful
                    line_content = clean_line.split("    ", 1)[-1].strip() if "    " in clean_line else clean_line.strip()
                    
                    # Only highlight jika:
                    # 1. Ada marker [*] atau [!]
                    # 2. Bukan baris kosong
                    # 3. Bukan metadata (bukan dimulai dengan . atau #)
                    should_highlight = (
                        (is_sink or is_decision) and 
                        line_content and 
                        not line_content.startswith((".", "#", "🎯", "⚡", "/")) and
                        len(line_content) > 3
                    )
                    
                    # Gunakan CSS class yang berbeda untuk sink vs decision point
                    if should_highlight:
                        if is_decision:
                            highlight_class = "highlight-line highlight-decision"
                        else:
                            highlight_class = "highlight-line"
                    else:
                        highlight_class = ""
                    
                    evidence_html += f'<div class="code-line {highlight_class}">{clean_line}</div>'

                # Get confidence score with v2.0 enhancement
                score = float(f.get('signal_confidence', f.get('confidence_score', 0.0)))
                badge_class = "bg-green" if score >= 0.8 else "bg-blue" if score >= 0.5 else "bg-gray"
                
                # Get associated vulnerabilities for this finding
                associated_vulns = f.get('associated_vulnerabilities', [])
                vuln_display = ""
                if associated_vulns:
                    vuln_display = '<div class="vulns-associated"><span class="vuln-label">⚠️ Associated Vulnerabilities:</span>'
                    for v in associated_vulns[:5]:  # Show max 5
                        if isinstance(v, dict):
                            v_name = v.get('name', 'Unknown')
                            v_severity = v.get('severity', 'Info')
                            vuln_display += f'<span class="vuln-badge vuln-{v_severity.lower()}">{v_name}</span>'
                    if len(associated_vulns) > 5:
                        vuln_display += f'<span class="vuln-more">+{len(associated_vulns)-5} more</span>'
                    vuln_display += '</div>'

                accordion_html += f"""
                    <div class="finding-card">
                        <div class="card-meta">
                            <div class="loc-info">
                                <span class="label">DETECTION PATH</span>
                                <code class="path-text">{f['location']['class']} <span class="arrow">→</span> {f['location']['method']}</code>
                            </div>
                            <div class="badge {badge_class}">Confidence v2.0: {score:.3f}</div>
                        </div>
                        <div class="taxonomy-bar">
                            <span><b>Strategy:</b> {f['taxonomy']['strategy']}</span>
                            <span class="separator">|</span>
                            <span><b>Impact:</b> {f['taxonomy']['impact']}</span>
                        </div>
                        {vuln_display}
                        <div class="source-container">
                            <div class="source-header">
                                <span>Method Implementation Detail (Evidence)</span>
                                <div class="source-toggle">
                                    <button class="source-lang-btn active" onclick="toggleSourceLang(this, 'smali')">Smali</button>
                                    <button class="source-lang-btn" onclick="toggleSourceLang(this, 'java')">Java</button>
                                </div>
                            </div>
                            <pre><code class="source-code-smali" style="display: block;">{evidence_html}</code></pre>
                            <pre><code class="source-code-java" style="display: none;">// Java source code coming soon...</code></pre>
                        </div>
                    </div>
                """
            accordion_html += "</div></div>"

        # 7. Full HTML Template with v2.0 Enhancements
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>M-ILEA Enhanced Report</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
            <!-- Chart.js for vulnerability visualization -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
            <style>
                :root {{
                    --bg-body: #F8FAFC; --bg-card: #FFFFFF; --bg-darker: #F1F5F9;
                    --text-primary: #1E293B; --text-secondary: #64748B;
                    --accent: #4F46E5; --accent-hover: #4338CA; --border: #E2E8F0;
                    --critical: #DC2626; --high: #F59E0B; --medium: #EAB308; --low: #10B981;
                    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
                    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }}

                body {{ margin: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg-body); color: var(--text-primary); display: flex; min-height: 100vh; font-size: 14px; }}
                
                /* Sidebar Navigation */
                .sidebar {{
                    position: fixed;
                    left: 0;
                    top: 0;
                    width: 260px;
                    height: 100vh;
                    background: var(--bg-card);
                    border-right: 1px solid var(--border);
                    padding: 20px;
                    overflow-y: auto;
                    z-index: 1000;
                    display: flex;
                    flex-direction: column;
                    box-shadow: var(--shadow-sm);
                }}
                
                .sidebar-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 32px;
                    padding-bottom: 0;
                    border-bottom: none;
                }}
                
                .sidebar-brand {{
                    font-size: 1.3rem;
                    font-weight: 800;
                    color: #1E293B;
                    text-decoration: none;
                    letter-spacing: -0.5px;
                }}
                
                .sidebar-toggle {{
                    display: none;
                    background: none;
                    border: none;
                    color: var(--text-primary);
                    font-size: 1.5rem;
                    cursor: pointer;
                }}
                
                .sidebar-menu {{
                    list-style: none;
                    padding: 0;
                    margin: 0;
                    flex: 1;
                }}
                
                .sidebar-menu li {{
                    margin: 6px 0;
                }}
                
                .sidebar-menu a {{
                    display: block;
                    padding: 10px 14px;
                    color: #64748B;
                    text-decoration: none;
                    border-radius: 6px;
                    transition: all 0.15s ease;
                    font-size: 0.9rem;
                    font-weight: 500;
                    cursor: pointer;
                    border-left: none;
                }}
                
                .sidebar-menu a:hover {{
                    color: #4F46E5;
                    background: #F0F4FF;
                }}
                
                .sidebar-footer {{
                    padding-top: 24px;
                    border-top: 1px solid #E2E8F0;
                    text-align: center;
                }}
                
                .sidebar-version {{
                    font-size: 0.75rem;
                    font-weight: 600;
                    color: #1E293B;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 4px;
                }}
                
                .sidebar-subtitle {{
                    font-size: 0.7rem;
                    color: #94A3B8;
                    margin-top: 4px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    font-weight: 600;
                }}
                
                /* Sticky Header */
                header {{
                    position: sticky;
                    top: 0;
                    background: #FFFFFF;
                    backdrop-filter: none;
                    z-index: 100;
                    padding: 16px 0;
                    margin: -40px -40px 40px -40px;
                    padding: 16px 40px;
                    border-bottom: 2px solid #E0E7FF;
                    box-shadow: var(--shadow-sm);
                }}
                
                .container {{ 
                    max-width: 1400px; 
                    margin: 0 0 0 280px;
                    padding: 40px 40px; 
                    flex: 1;
                }}
                
                header {{ 
                    display: flex; justify-content: space-between; align-items: flex-end; 
                    margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid var(--border); 
                }}
                .brand h1 {{ margin: 0; font-size: 1.8rem; font-weight: 800; }}
                .brand span {{ color: var(--accent); }}
                .version-badge {{ background: var(--accent); color: white; padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }}
                
                /* Section Anchors for Sidebar Navigation */
                .section-anchor {{
                    display: block;
                    height: 0;
                    visibility: hidden;
                }}

                /* Professional Layout Grid */
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 32px;
                    margin-bottom: 40px;
                    align-items: start;
                }}
                
                .dashboard-row {{
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 28px;
                    margin-bottom: 40px;
                }}
                
                .chart-container-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 18px;
                    width: 100%;
                    align-content: start;
                }}

                .card {{ 
                    background: var(--bg-card);
                    border: 1px solid var(--border); 
                    border-radius: 12px; 
                    padding: 32px;
                    box-shadow: var(--shadow-md);
                    transition: var(--transition);
                    position: relative;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }}
                
                .card:hover {{
                    border-color: var(--accent);
                    box-shadow: var(--shadow-lg);
                    transform: translateY(-2px);
                }}
                
                .card h2 {{ 
                    font-size: 1.25rem; 
                    color: var(--text-primary); 
                    margin: 0 0 24px 0;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                
                .card h2::before {{
                    content: '';
                    display: inline-block;
                    width: 4px;
                    height: 18px;
                    background: var(--accent);
                    border-radius: 2px;
                }}
                
                .stat-item {{ 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center;
                    padding: 14px 0; 
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                    font-size: 0.95rem;
                }}
                
                .stat-item:last-child {{
                    border-bottom: none;
                }}
                
                .stat-item span:first-child {{
                    color: var(--text-secondary);
                    font-weight: 500;
                }}
                
                .highlight-val {{ 
                    color: var(--accent); 
                    font-weight: 700;
                    font-size: 1.1rem;
                }}

                /* Vulnerability Stats */
                .vuln-grid {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 16px;
                    margin-top: 20px;
                }}
                
                .vuln-stat {{
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    background: #F8FAFC;
                    border: 1.5px solid var(--border);
                    transition: var(--transition);
                    cursor: default;
                }}
                
                .vuln-stat:hover {{
                    border-color: var(--accent);
                    background: #EEF2FF;
                    transform: translateY(-2px);
                }}
                
                .vuln-stat.critical {{ 
                    border-color: #FCA5A5;
                    background: #FEF2F2;
                }}
                
                .vuln-stat.high {{ 
                    border-color: #FCD34D;
                    background: #FFFBEB;
                }}
                
                .vuln-stat.medium {{ 
                    border-color: #FDE047;
                    background: #FFFEF4;
                }}
                
                .vuln-stat.low {{ 
                    border-color: #86EFAC;
                    background: #F0FDF4;
                }}
                
                .vuln-num {{
                    display: block;
                    font-size: 2rem;
                    font-weight: 800;
                    margin-bottom: 8px;
                    line-height: 1;
                }}
                
                .vuln-stat.critical .vuln-num {{ color: var(--critical); }}
                .vuln-stat.high .vuln-num {{ color: var(--high); }}
                .vuln-stat.medium .vuln-num {{ color: var(--medium); }}
                .vuln-stat.low .vuln-num {{ color: var(--low); }}
                
                .vuln-stat span:last-child {{
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}

                /* Metrics Grid */
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 16px;
                    margin-top: 20px;
                }}
                
                .metric-item {{
                    padding: 20px;
                    background: #F8FAFC;
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    text-align: center;
                    transition: var(--transition);
                }}
                
                .metric-item:hover {{
                    background: var(--bg-card);
                    border-color: var(--accent);
                    transform: translateY(-2px);
                    box-shadow: var(--shadow-md);
                }}
                
                .metric-label {{
                    display: block;
                    font-size: 0.75rem;
                    color: var(--text-secondary);
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    font-weight: 600;
                }}
                
                .metric-value {{
                    display: block;
                    font-size: 1.6rem;
                    font-weight: 800;
                    color: var(--accent);
                    line-height: 1.2;
                }}

                .chart-box {{ 
                    background: linear-gradient(135deg, rgba(240, 245, 250, 0.95) 0%, rgba(225, 235, 245, 0.9) 100%);
                    border-radius: 10px; 
                    border: 1px solid rgba(59, 130, 246, 0.2); 
                    padding: 20px;
                    overflow: hidden;
                    transition: all 0.3s ease;
                    min-height: 300px;
                }}
                
                .chart-box:hover {{
                    border-color: rgba(59, 130, 246, 0.4);
                    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.15);
                }}
                
                .chart-box img {{ 
                    width: 100%; 
                    height: auto; 
                    display: block;
                    border-radius: 6px;
                }}
                
                .chart-box span {{
                    color: var(--text-primary);
                    font-weight: 500;
                }}

                /* Accordion UI */
                .category-wrapper {{ 
                    margin-bottom: 14px; 
                    border: 1px solid var(--border); 
                    border-radius: 10px; 
                    background: #FFFFFF;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }}
                
                .category-wrapper:hover {{
                    border-color: var(--accent);
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
                }}
                
                .accordion-header {{ 
                    width: 100%; 
                    padding: 20px 24px; 
                    background: none; 
                    border: none; 
                    color: var(--text-primary); 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.2s ease;
                }}
                
                .accordion-header:hover {{ 
                    background: #EEF2FF;
                }}
                
                .chevron {{ 
                    font-size: 0.7rem; 
                    transition: transform 0.3s ease; 
                    color: var(--accent);
                }}
                
                .header-left {{ 
                    display: flex; 
                    align-items: center; 
                    gap: 12px;
                }}
                
                .cat-count {{ 
                    font-size: 0.7rem; 
                    background: var(--accent);
                    padding: 4px 14px; 
                    border-radius: 20px;
                    font-weight: 700;
                    color: #FFFFFF;
                }}
                
                .accordion-content {{ 
                    display: none; 
                    padding: 24px; 
                    background: #F8FAFC;
                    border-top: 1px solid #E0E7FF;
                }}
                
                .active .chevron {{ 
                    transform: rotate(90deg);
                }}
                
                .active + .accordion-content {{ 
                    display: block;
                }}

                /* Finding Cards */
                .finding-card {{ 
                    background: #FFFFFF;
                    border: 2px solid #DDD6FE; 
                    border-radius: 10px; 
                    padding: 22px; 
                    margin-bottom: 20px;
                    transition: all 0.3s ease;
                }}
                
                .finding-card:hover {{
                    border-color: var(--accent);
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
                }}
                
                .path-text {{ 
                    font-family: 'Fira Code', monospace; 
                    color: var(--accent); 
                    font-size: 0.85rem;
                }}
                
                .badge {{ 
                    padding: 6px 14px; 
                    border-radius: 6px; 
                    font-weight: 700; 
                    font-size: 0.7rem; 
                    border: 1px solid rgba(255,255,255,0.2);
                    display: inline-block;
                    transition: all 0.2s ease;
                }}
                
                .badge:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                }}
                
                .bg-green {{ 
                    color: #34d399; 
                    background: rgba(16, 185, 129, 0.15);
                    border-color: rgba(16, 185, 129, 0.4);
                }}
                
                .bg-blue {{ 
                    color: #60a5fa; 
                    background: rgba(59, 130, 246, 0.15);
                    border-color: rgba(59, 130, 246, 0.4);
                }}
                
                .bg-gray {{ 
                    color: #cbd5e1; 
                    background: rgba(148, 163, 184, 0.1);
                    border-color: rgba(148, 163, 184, 0.3);
                }}

                /* Vulnerability Badges */
                .vulns-associated {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    padding: 12px;
                    background: rgba(220, 38, 38, 0.1);
                    border-left: 3px solid var(--critical);
                    border-radius: 4px;
                    margin: 10px 0;
                    font-size: 0.85rem;
                }}
                
                .vuln-label {{
                    font-weight: 600;
                    color: var(--critical);
                }}
                
                .vuln-badge {{
                    background: var(--critical);
                    color: white;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    white-space: nowrap;
                }}
                
                .vuln-badge.vuln-critical {{ background: var(--critical); }}
                .vuln-badge.vuln-high {{ background: var(--high); }}
                .vuln-badge.vuln-medium {{ background: var(--medium); }}
                .vuln-badge.vuln-low {{ background: var(--low); }}
                .vuln-badge.vuln-info {{ background: var(--accent); }}
                
                .vuln-more {{
                    color: var(--critical);
                    font-weight: 600;
                }}

                /* Source Viewer - Professional Enhancement */
                .source-container {{ 
                    border-radius: 8px; 
                    border: 1px solid var(--border); 
                    overflow: hidden; 
                    margin-top: 15px;
                    background: #0f1419;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                
                .source-header {{ 
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                    padding: 12px 16px; 
                    font-size: 0.7rem; 
                    color: var(--text-secondary); 
                    text-transform: uppercase;
                    border-bottom: 1px solid var(--border);
                    font-weight: 600;
                }}
                
                .source-toggle {{
                    display: flex;
                    gap: 8px;
                }}
                
                .source-lang-btn {{
                    padding: 4px 12px;
                    border: 1px solid #DDD6FE;
                    background: #F8FAFC;
                    color: var(--text-secondary);
                    border-radius: 4px;
                    font-size: 0.65rem;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-weight: 600;
                }}
                
                .source-lang-btn:hover {{
                    background: #EEF2FF;
                    border-color: var(--accent);
                    color: var(--accent);
                }}
                
                .source-lang-btn.active {{
                    background: var(--accent);
                    border-color: var(--accent);
                    color: white;
                }}
                
                pre {{ 
                    margin: 0; 
                    padding: 16px; 
                    overflow-x: auto; 
                    background: #0f1419;
                    line-height: 1.6;
                }}
                
                code {{ 
                    font-family: 'Fira Code', monospace; 
                    font-size: 0.85rem;
                    color: #e0e7ff;
                }}
                
                .code-line {{ color: #a0aec0; white-space: pre; }}
                .highlight-line {{ color: #ffa657; background: rgba(255, 166, 87, 0.1); display: block; margin: 0 -16px; padding: 0 16px; border-left: 3px solid #ffa657; }}
                .highlight-decision {{ color: #f59e0b; background: rgba(245, 158, 11, 0.15); border-left: 3px solid #f59e0b; font-weight: 600; }}

                /* Vulnerability Details */
                .vulnerability-details {{
                    margin-top: 40px;
                }}
                
                .vulnerability-list {{
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }}
                
                .vuln-detail-group {{
                    background: #FFFFFF;
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                
                .vuln-detail-header {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 15px 20px;
                    background: #F8FAFC;
                    border-bottom: 1px solid var(--border);
                    cursor: pointer;
                    user-select: none;
                }}
                
                .vuln-detail-header:hover {{
                    background: #F0F4FF;
                }}
                
                .vuln-type-name {{
                    flex: 1;
                    font-weight: 600;
                    color: var(--text-primary);
                }}
                
                .vuln-count {{
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }}
                
                .vuln-detail-header .chevron {{
                    color: var(--text-secondary);
                    transition: transform 0.2s;
                }}
                
                .vuln-detail-group.open .vuln-detail-header .chevron {{
                    transform: rotate(180deg);
                }}
                
                .vuln-detail-content {{
                    display: none;
                    padding: 20px;
                    background: #FFFFFF;
                }}
                
                .vuln-detail-group.open .vuln-detail-content {{
                    display: block;
                }}
                
                .vuln-instance {{
                    background: #F8FAFC;
                    border: 1px solid var(--border);
                    border-radius: 6px;
                    padding: 15px;
                    margin-bottom: 15px;
                }}
                
                .instance-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #E2E8F0;
                }}
                
                .instance-location {{
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }}
                
                .instance-meta {{
                    display: flex;
                    gap: 20px;
                    margin-bottom: 15px;
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                }}
                
                .evidence-container {{
                    margin: 15px 0;
                }}
                
                .evidence-label {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: var(--text-secondary);
                    font-size: 0.85rem;
                    text-transform: uppercase;
                }}
                
                .code-snippet {{
                    background: #010409;
                    border: 1px solid var(--border);
                    border-radius: 4px;
                    padding: 12px;
                    font-family: 'Fira Code', monospace;
                    font-size: 0.85rem;
                    max-height: 300px;
                    overflow-y: auto;
                }}
                
                .code-snippet .code-line {{
                    padding: 2px 0;
                    color: #7d8590;
                }}
                
                .instance-details {{
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px solid #E2E8F0;
                }}
                
                .detail-section {{
                    margin-bottom: 12px;
                }}
                
                .detail-section.remediation {{
                    background: rgba(34, 197, 94, 0.1);
                    padding: 12px;
                    border-radius: 4px;
                    border-left: 3px solid #22c55e;
                }}
                
                .detail-section p {{
                    margin: 6px 0 0 0;
                    font-size: 0.95rem;
                    line-height: 1.5;
                    color: var(--text-secondary);
                }}
                
                .more-instances {{
                    padding: 12px;
                    background: #F8FAFC;
                    border-radius: 4px;
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                    font-style: italic;
                }}

                /* Vulnerability Charts */
                .charts-row {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                
                .chart-container {{
                    background: #FFFFFF;
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    padding: 15px;
                    min-height: 300px;
                }}
                
                /* Findings Table */
                .findings-table {{
                    margin-top: 30px;
                }}
                
                .findings-table h3 {{
                    color: var(--text-primary);
                    font-size: 1rem;
                    margin-bottom: 15px;
                }}
                
                .findings-table table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: #FFFFFF;
                    border: 1px solid var(--border);
                    border-radius: 6px;
                    overflow: hidden;
                }}
                
                .findings-table thead {{
                    background: #F8FAFC;
                    border-bottom: 1px solid var(--border);
                }}
                
                .findings-table th {{
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                    text-transform: uppercase;
                }}
                
                .findings-table td {{
                    padding: 12px;
                    border-bottom: 1px solid #E2E8F0;
                    font-size: 0.9rem;
                }}
                
                .findings-table tbody tr:hover {{
                    background: #F0F4FF;
                }}
                
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                }}
                
                .badge-count {{
                    background: var(--accent);
                    color: white;
                }}
                
                .badge-critical {{
                    background: rgba(220, 38, 38, 0.2);
                    color: #dc2626;
                }}
                
                .badge-high {{
                    background: rgba(245, 158, 11, 0.2);
                    color: #f59e0b;
                }}
                
                .badge-medium {{
                    background: rgba(234, 179, 8, 0.2);
                    color: #eab308;
                }}
                
                .badge-low {{
                    background: rgba(16, 185, 129, 0.2);
                    color: #10b981;
                }}
                
                .findings-table code {{
                    background: #F8FAFC;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 0.8rem;
                    color: var(--accent);
                }}

                /* Findings Rundown Section */
                .findings-rundown {{
                    margin-top: 60px;
                    padding: 0;
                }}
                
                .findings-rundown > h2 {{
                    font-size: 0.8rem !important;
                    color: var(--text-primary) !important;
                    text-transform: uppercase;
                    margin-bottom: 28px !important;
                    letter-spacing: 0.15em;
                    font-weight: 800;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                
                .findings-rundown > h2::before {{
                    content: '';
                    display: inline-block;
                    width: 4px;
                    height: 4px;
                    background: var(--accent);
                    border-radius: 50%;
                }}

                footer {{ 
                    text-align: center; 
                    color: var(--text-secondary); 
                    font-size: 0.75rem; 
                    padding: 40px 20px;
                    border-top: 1px solid var(--border);
                    margin-top: 60px;
                    letter-spacing: 0.05em;
                }}
                
                /* Responsive Design */
                @media (max-width: 1024px) {{
                    /* Tablet: Adjust layout for sidebar */
                    .sidebar-toggle {{
                        display: block;
                    }}
                    
                    .container {{
                        margin: 0;
                        padding-left: 20px;
                        padding-right: 20px;
                    }}
                    
                    .dashboard-grid {{
                        grid-template-columns: 1fr;
                        gap: 24px;
                    }}
                    
                    .vuln-grid {{
                        grid-template-columns: repeat(2, 1fr);
                        gap: 14px;
                    }}
                    
                    .metrics-grid {{
                        grid-template-columns: repeat(2, 1fr);
                        gap: 14px;
                    }}
                    
                    .chart-container-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .container {{
                        padding: 30px 16px;
                    }}
                    
                    .card {{
                        padding: 22px;
                    }}
                    
                    header {{
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 16px;
                    }}
                    
                    .meta-info {{
                        width: 100%;
                    }}
                }}
                
                @media (max-width: 768px) {{
                    /* Mobile: Hide sidebar by default */
                    .sidebar {{
                        position: fixed;
                        left: -260px;
                        width: 260px;
                        height: 100vh;
                        background: var(--bg-card);
                        z-index: 1001;
                        transition: left 0.3s ease;
                        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                    }}
                    
                    .sidebar-toggle {{
                        display: block;
                    }}
                    
                    .container {{
                        margin: 0;
                        padding: 20px;
                    }}
                }}
                
                @media (max-width: 640px) {{
                    .brand h1 {{
                        font-size: 1.4rem;
                    }}
                    
                    .dashboard-grid {{
                        gap: 16px;
                        grid-template-columns: 1fr;
                    }}
                    
                    .dashboard-row {{
                        gap: 16px;
                    }}
                    
                    .vuln-grid {{
                        grid-template-columns: repeat(2, 1fr);
                        gap: 10px;
                    }}
                    
                    .metrics-grid {{
                        grid-template-columns: 1fr;
                        gap: 10px;
                    }}
                    
                    .chart-container-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .vuln-stat {{
                        padding: 12px;
                    }}
                    
                    .vuln-num {{
                        font-size: 1.2rem;
                    }}
                    
                    .source-header {{
                        flex-direction: column;
                        gap: 8px;
                        align-items: flex-start;
                    }}
                    
                    .source-toggle {{
                        width: 100%;
                    }}
                    
                    .source-lang-btn {{
                        flex: 1;
                    }}
                    
                    pre {{
                        font-size: 0.75rem;
                    }}
                    
                    code {{
                        font-size: 0.75rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <!-- Sidebar Navigation -->
            <nav class="sidebar">
                <div class="sidebar-header">
                    <div class="sidebar-brand">M-ILEA</div>
                    <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
                </div>
                <ul class="sidebar-menu">
                    <li><a href="#summary" onclick="scrollToSection('summary'); return false;">Summary</a></li>
                    <li><a href="#visualizations" onclick="scrollToSection('visualizations'); return false;">Security Visualizations</a></li>
                    <li><a href="#vulnerabilities" onclick="scrollToSection('vulnerabilities'); return false;">Vulnerabilities</a></li>
                    <li><a href="#metrics" onclick="scrollToSection('metrics'); return false;">Confidence Metrics</a></li>
                    <li><a href="#evidence" onclick="scrollToSection('evidence'); return false;">Evidence & Details</a></li>
                    <li><a href="#rundown" onclick="scrollToSection('rundown'); return false;">Analysis Rundown</a></li>
                </ul>
                <div class="sidebar-footer">
                    <div class="sidebar-version">v2.0</div>
                    <div class="sidebar-subtitle">Enhanced Framework</div>
                </div>
            </nav>
            <div class="container">
                <header>
                    <div class="brand">
                        <h1>M-ILEA <span>Security Analysis Dashboard</span></h1>
                    </div>
                    <div class="meta-info">
                        <div style="text-align: right;">
                            <div style="font-size: 0.9rem; color: var(--text-secondary);">Analyzing: <b style="color: var(--accent);">{metadata.get('app_name', 'Unknown')}</b></div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px;">Generated: {self._get_current_timestamp()}</div>
                        </div>
                    </div>
                </header>

                <div id="summary" class="dashboard-grid">
                    <div class="card">
                        <h2>Summary</h2>
                        <div class="stat-item"><span>Engine</span><span class="highlight-val">{metadata.get('analysis_engine', 'N/A')}</span></div>
                        <div class="stat-item"><span>Findings</span><span class="highlight-val">{len(findings)}</span></div>
                        <div class="stat-item"><span>v2.0 Features</span><span class="badge bg-green">Enabled</span></div>
                        <div class="stat-item"><span>Status</span><span class="badge bg-green">Enhanced</span></div>
                    </div>

                    <div id="visualizations" class="card">
                        <h2>Security Visualizations</h2>
                        <div class="chart-container-grid">
                            {charts_html}
                        </div>
                    </div>
                </div>

                <div id="vulnerabilities" class="dashboard-row">
                    {vuln_html}
                </div>

                <div id="metrics" class="dashboard-row">
                    {metrics_html}
                </div>

                <div id="evidence" class="section-anchor"></div>

                {vuln_details_html}

                <div id="rundown" class="findings-rundown">
                    <h2 style="font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 15px;">Detailed Analysis Rundown</h2>
                    {accordion_html}
                </div>

                <footer>M-ILEA Advanced Security Analysis Framework &bullet; Analysis Report v2.0 &bullet; {datetime.now().year}</footer>
            </div>

            <script>
                // Sidebar Navigation
                function scrollToSection(sectionId) {{
                    const section = document.getElementById(sectionId);
                    if (section) {{
                        section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        // Close sidebar on mobile after click
                        const sidebar = document.querySelector('.sidebar');
                        if (window.innerWidth <= 768) {{
                            sidebar.style.left = '-260px';
                        }}
                    }}
                }}
                
                function toggleSidebar() {{
                    const sidebar = document.querySelector('.sidebar');
                    if (sidebar.style.left === '0px') {{
                        sidebar.style.left = '-260px';
                    }} else {{
                        sidebar.style.left = '0px';
                    }}
                }}
                
                // Update active sidebar menu based on scroll position
                window.addEventListener('scroll', function() {{
                    const sections = ['summary', 'visualizations', 'vulnerabilities', 'metrics', 'evidence', 'rundown'];
                    for (const sectionId of sections) {{
                        const section = document.getElementById(sectionId);
                        if (section) {{
                            const rect = section.getBoundingClientRect();
                            if (rect.top <= 100 && rect.bottom >= 100) {{
                                const links = document.querySelectorAll('.sidebar-menu a');
                                links.forEach(link => link.style.color = 'var(--text-secondary)');
                                const activeLink = document.querySelector(`.sidebar-menu a[href="#${{sectionId}}"]`);
                                if (activeLink) {{
                                    activeLink.style.color = 'var(--text-primary)';
                                    activeLink.style.background = 'rgba(59, 130, 246, 0.15)';
                                    activeLink.style.borderLeftColor = 'var(--accent)';
                                }}
                            }}
                        }}
                    }}
                }});
                
                function toggleAccordion(btn) {{
                    btn.classList.toggle('active');
                    const content = btn.nextElementSibling;
                    content.style.display = content.style.display === "block" ? "none" : "block";
                }}
                
                function toggleVulnDetail(header) {{
                    const group = header.closest('.vuln-detail-group');
                    group.classList.toggle('open');
                }}
                
                function toggleSourceLang(btn, lang) {{
                    // Update button active state
                    const buttons = btn.parentElement.querySelectorAll('.source-lang-btn');
                    buttons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    // Toggle code visibility
                    const container = btn.closest('.source-container');
                    const javaCode = container.querySelector('.source-code-java');
                    const smaliCode = container.querySelector('.source-code-smali');
                    
                    if (lang === 'java') {{
                        javaCode.style.display = 'block';
                        smaliCode.style.display = 'none';
                    }} else {{
                        javaCode.style.display = 'none';
                        smaliCode.style.display = 'block';
                    }}
                    
                    // Save preference
                    localStorage.setItem('sourceCodeLang', lang);
                }}
                
                // Restore user's source language preference on page load
                window.addEventListener('load', function() {{
                    const savedLang = localStorage.getItem('sourceCodeLang') || 'smali';
                    if (savedLang === 'java') {{
                        document.querySelectorAll('.source-lang-btn').forEach(btn => {{
                            if (btn.textContent.trim() === 'Java') {{
                                btn.click();
                            }}
                        }});
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        with open(self.output_path, "w", encoding='utf-8') as f:
            f.write(html_content)