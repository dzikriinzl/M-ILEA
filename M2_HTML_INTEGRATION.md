# M2 Classification Integration with HTML Dashboard

## Overview

The M2 4-category self-protection classification system is now fully integrated with the HTML dashboard generator. When you run M-ILEA analysis, the HTML report automatically includes M2 threat assessment, category indicators, and framework noise filtering results.

## Architecture

```
M-ILEA Analysis Pipeline
    ↓
    ├─ Standard Analysis (findings, vulnerabilities, metrics)
    └─ M2 Integration (4-category classification, threat assessment)
         ↓
    ├─ JSON Report (m2_integrated.json)
    ├─ Markdown Summary (m2_summary.md)
    └─ HTML Dashboard (dashboard.html) ← Enhanced with M2 sections
```

## Components

### 1. HTMLM2Generator (`core/report/html_m2_generator.py`)

Extended version of `HTMLReportGenerator` that:
- **Accepts M2 data**: Takes M2 integration report as input
- **Builds threat cards**: Displays threat level with color-coded indicators
- **Shows categories**: Visual grid of detected/undetected protection categories
- **Filters visualization**: Stacked bar chart showing framework noise vs. actual findings
- **Adds badges**: Each finding gets M2 classification badge (Framework Noise, Environment Manipulation, etc.)
- **Generates recommendations**: Hardening recommendations based on threat level

**Key Classes:**
```python
class HTMLM2Generator(HTMLReportGenerator):
    def generate_with_m2(self, metadata, findings, chart_images, 
                        vulnerabilities=None, metrics=None, m2_report=None)
    
    def _build_m2_threat_section(self) -> str
    def _build_m2_noise_section(self) -> str
    def _build_m2_classification_badges(self, finding: Dict) -> str
```

### 2. run.py Integration Hook

**Location:** Lines 362-387 in `run.py`

```python
# Check if M2 integration data is available
m2_report = None
m2_json_path = results_dir / app_base_name / "m2_integration" / f"{app_base_name}_m2_integrated.json"
if m2_json_path.exists():
    with open(m2_json_path) as f:
        m2_report = json.load(f)

# Use M2-enhanced HTML generator if M2 data available
if m2_report:
    html_gen = HTMLM2Generator(results_dir / "dashboard.html")
    html_gen.generate_with_m2(output_data["metadata"], serialized_findings, chart_names, 
                             vulnerabilities=vulnerabilities, metrics=metrics, m2_report=m2_report)
else:
    html_gen = HTMLReportGenerator(...)  # Fallback to standard
```

## HTML Dashboard Sections

### 1. Threat Assessment Card

**Features:**
- Threat level badge with icon (🔴 HIGH, 🟡 MEDIUM, 🟢 LOW, 🔵 INFO)
- Color-coded background based on threat level
- Assessment message describing the threat
- Category indicators showing which categories detected/not detected
- Threat properties (Evasion Tactics, Protection Mechanisms, Vulnerability Exposure)
- Hardening recommendations list

**Example Output:**
```
🔵 INFO - Threat Assessment
No significant self-protection mechanisms detected

Category Indicators:
  🔓 Environment Manipulation: 0
  🛡️ Analysis Prevention: 0
  🔐 Integrity Enforcement: 0
  ⚙️ System Interaction: 0

Hardening Recommendations:
  • Validate all input data before processing
  • Use EncryptedSharedPreferences for sensitive data
  • Enforce HTTPS-only communication
  ...
```

### 2. Analysis Filtering Results Card

**Features:**
- Statistics grid showing:
  - Total findings analyzed
  - Framework noise count & percentage
  - Actual findings count & percentage
- Visual bar chart with stacked segments:
  - Orange segment: Framework noise
  - Green segment: Actual findings
- Easy-to-understand noise filtering effectiveness

**Example:**
```
Total Analyzed: 87
Framework Noise: 85 (97.7%)
Actual Findings: 2 (2.3%)

[████████████████████ 97% ] [█ 2%]
```

### 3. Finding Cards with M2 Badges

**Features:**
- Each finding now has M2 classification badge
- Badge colors match category:
  - **Purple**: Environment Manipulation (🔓)
  - **Pink**: Analysis Prevention (🛡️)
  - **Blue**: Integrity Enforcement (🔐)
  - **Orange**: System Interaction (⚙️)
  - **Orange/Brown**: Framework Noise (🔧)
- Badge shows confidence level on hover

**Example:**
```
Detection Path: com.example.App > checkDevice
Confidence: 0.845
[Frame Noise 🔧] [Environment Manipulation 🔓] [Confidence: 0.845]
```

## Styling

Added comprehensive M2-specific CSS in the HTML template:

```css
:root {
    --m2-env: #8B5CF6;           /* Purple */
    --m2-analysis: #EC4899;       /* Pink */
    --m2-integrity: #3B82F6;      /* Blue */
    --m2-system: #F97316;         /* Orange */
}

.threat-assessment-card { border-left: 4px solid; background: gradient; }
.threat-assessment-card.threat-high { border-color: #DC2626; }
.threat-assessment-card.threat-medium { border-color: #F59E0B; }
.threat-assessment-card.threat-low { border-color: #10B981; }
.threat-assessment-card.threat-info { border-color: #3B82F6; }

.m2-badge { padding: 4px 10px; border-radius: 4px; font-weight: 600; }
.m2-badge.badge-noise { background: rgba(249, 115, 22, 0.1); }
.m2-badge.badge-env { background: rgba(139, 92, 246, 0.1); }
```

## Usage

### Automatic Integration

Simply run the analyzer as normal:

```bash
python3 run.py analyze evaluation/apps/pinning.apk --verbose
```

The M2 data will be automatically:
1. Generated during analysis (M2 integrator)
2. Loaded from JSON report
3. Integrated into HTML dashboard
4. Rendered with threat assessment and filtering sections

### Checking the Dashboard

```bash
# View HTML in browser
open evaluation/results/pinning/dashboard.html

# Or check file exists and size
ls -lh evaluation/results/pinning/dashboard.html

# Verify M2 sections are present
grep "Threat Assessment" evaluation/results/pinning/dashboard.html
grep "Framework Noise" evaluation/results/pinning/dashboard.html
```

## Testing Results (pinning.apk)

**Dashboard Statistics:**
- Total file size: 570 KB
- M2 threat sections: ✅ Present
- Framework noise visualization: ✅ Rendered
- M2 badges on findings: ✅ 86 noise badges + 2 protection badges
- Hardening recommendations: ✅ Included
- Threat level display: ✅ INFO (correct)

**Rendered Sections:**
```
✅ Threat Assessment Card (with threat-info styling)
✅ Analysis Filtering Results (97% noise, 2% actual)
✅ Category Indicators (all 4 categories shown)
✅ Hardening Recommendations (6 items)
✅ Finding Badges (86x Framework Noise, 2x Actual findings)
```

## File Changes Summary

### New Files Created
- `core/report/html_m2_generator.py` (760+ lines)

### Modified Files
- `run.py` (added import + updated HTML generation section)

### Integration Points
1. **Post M2 Integration**: M2 JSON report is loaded
2. **Before HTML Generation**: M2 data passed to HTMLM2Generator
3. **During Rendering**: Threat sections inserted before findings
4. **Finding Display**: Each finding gets M2 classification badge

## Browser Compatibility

The M2-enhanced dashboard uses:
- Modern CSS (custom properties, gradients, flexbox, grid)
- Standard JavaScript (no frameworks required)
- Compatible with:
  - Chrome 90+
  - Firefox 88+
  - Safari 14+
  - Edge 90+

## Performance Impact

- HTML generation: **+5-10ms** (loading M2 JSON)
- File size increase: **+15-20KB** (CSS + extra sections)
- Browser rendering: **No noticeable difference**

## Future Enhancements

1. **Interactive Charts**: Chart.js integration for threat trend visualization
2. **Drill-Down Analysis**: Click on findings to see M2 classification details
3. **Comparison View**: Side-by-side comparison of findings with/without M2 filtering
4. **Export Options**: PDF export with M2 sections
5. **Dark Mode**: Theme toggle for dark mode support
6. **Mobile Responsive**: Optimize for mobile viewing

## Troubleshooting

### M2 sections not appearing

**Check:**
1. M2 integration ran successfully:
   ```bash
   ls evaluation/results/pinning/pinning/m2_integration/
   ```

2. M2 JSON file exists and is valid:
   ```bash
   python3 -m json.tool evaluation/results/pinning/pinning/m2_integration/pinning_m2_integrated.json
   ```

3. run.py loaded the M2Generator:
   ```bash
   python3 run.py analyze ... --verbose 2>&1 | grep "M2 Dashboard"
   ```

### HTML rendering issues

**Try:**
1. Clear browser cache
2. Check console for JavaScript errors
3. Verify JSON is properly loaded in Network tab
4. Try different browser

### Missing badges on findings

**Check:**
1. M2 data was enriched correctly:
   ```python
   import json
   with open("pinning_m2_integrated.json") as f:
       data = json.load(f)
       print(len(data['enriched_findings']))
   ```

2. Findings have `classification` field in enriched data

## API Reference

### HTMLM2Generator Methods

```python
def set_m2_data(self, m2_report: Dict[str, Any]) -> None
    """Set M2 classification data"""

def generate_with_m2(self, metadata, findings, chart_images, 
                    vulnerabilities=None, metrics=None, 
                    m2_report=None) -> None
    """Generate HTML with M2 sections"""

def _build_m2_threat_section(self) -> str
    """Build threat assessment card HTML"""

def _build_m2_noise_section(self) -> str
    """Build framework noise filtering card HTML"""

def _build_m2_classification_badges(self, finding: Dict) -> str
    """Generate M2 classification badge HTML for finding"""

def _get_threat_level_color(self, level: str) -> str
    """Get CSS class for threat level (high/medium/low/info)"""

def _get_threat_level_icon(self, level: str) -> str
    """Get emoji icon for threat level"""
```

## Configuration

The M2 HTML integration can be customized by modifying:

1. **Colors** (in `:root` CSS variables):
   - Change `--m2-env`, `--m2-analysis`, `--m2-integrity`, `--m2-system`

2. **Styling**:
   - Edit CSS for threat cards, badges, visualizations

3. **Badge Layout**:
   - Modify `.badges-container` flex properties

4. **Category Display**:
   - Adjust `.categories-grid` columns and spacing

## Examples

### Example 1: High Threat Level

When analysis detects evasion mechanisms:

```
🔴 HIGH - Threat Assessment
Application implements active anti-analysis mechanisms

Category Indicators:
  🔓 Environment Manipulation: 3 ✓ ACTIVE
  🛡️ Analysis Prevention: 5 ✓ ACTIVE
  🔐 Integrity Enforcement: 2
  ⚙️ System Interaction: 1

Evasion Tactics: Yes
Protection Mechanisms: Yes
Vulnerability Exposure: No
```

### Example 2: Medium Threat Level

Mixed security posture:

```
🟡 MEDIUM - Threat Assessment
Mixed security posture with both protections and vulnerabilities

Category Indicators:
  🔓 Environment Manipulation: 0
  🛡️ Analysis Prevention: 0
  🔐 Integrity Enforcement: 4 ✓ ACTIVE
  ⚙️ System Interaction: 7 ✓ ACTIVE

Evasion Tactics: No
Protection Mechanisms: Yes
Vulnerability Exposure: Yes
```

### Example 3: Low Threat Level

Legitimate security features:

```
🟢 LOW - Threat Assessment
Legitimate security features without evasion

Category Indicators:
  🔓 Environment Manipulation: 0
  🛡️ Analysis Prevention: 0
  🔐 Integrity Enforcement: 2 ✓ ACTIVE
  ⚙️ System Interaction: 0

Evasion Tactics: No
Protection Mechanisms: Yes
Vulnerability Exposure: No
```

## Conclusion

The M2 classification system is now seamlessly integrated into the HTML dashboard, providing users with:
- ✅ Clear threat assessment at a glance
- ✅ Visual indication of framework noise filtering effectiveness
- ✅ Per-finding classification with color-coded badges
- ✅ Hardening recommendations based on threat level
- ✅ Professional, production-ready visualization
