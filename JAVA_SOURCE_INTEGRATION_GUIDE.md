# Java Source Code Integration Guide

## Overview
This guide explains how to integrate actual Java source code extraction from the JADX decompiler into vulnerability evidence display, completing the Java/Smali toggle feature.

---

## Current State

### What's Working ✅
- JADX decompiler backend exists
- Java/Smali toggle buttons functional
- JavaScript toggle functionality complete
- Dashboard responsive and professional

### What's Missing 🔄
- Java source code not being extracted from JADX output
- Placeholder "Java source code coming soon..." shown
- Need to bridge JADX output to vulnerability display

---

## Implementation Plan

### Step 1: Extract Java Source from DecompiledClass

The `DecompiledClass` object from JADX contains:
```python
class DecompiledClass:
    name: str              # com.example.MyClass
    methods: List[Method]  # List of methods
    # Each method has:
    #   - name: str
    #   - code_lines: List[str]  # Java source code lines
    #   - line_start: int
    #   - line_end: int
```

### Step 2: Update VulnerabilityScanner

Modify `core/vulnerability_v2.py` to extract and store Java code:

```python
class VulnerabilityScanner:
    def __init__(self, extracted_dir, source_manager=None):
        self.source_manager = source_manager or SourceCodeManager()
        self.extracted_dir = extracted_dir
    
    def scan(self, decompiled_classes):
        # Extract Java source from decompiled classes
        self.source_manager.extract_from_decompiled_classes(decompiled_classes)
        
        # Continue with vulnerability scanning...
        vulnerabilities = self._analyze_classes(decompiled_classes)
        
        # Enrich vulnerabilities with Java source
        for vuln in vulnerabilities:
            java_snippet = self.source_manager.get_java_snippet(
                vuln.class_name,
                vuln.method_name,
                context_lines=10
            )
            vuln.java_source = java_snippet
        
        return vulnerabilities
```

### Step 3: Update Vulnerability Model

Modify vulnerability data structure:

```python
@dataclass
class Vulnerability:
    # ... existing fields ...
    smali_source: str = ""  # Current Smali code
    java_source: str = ""   # NEW: Java source code
    
    def to_dict(self):
        return {
            # ... existing fields ...
            'smali_source': self.smali_source,
            'java_source': self.java_source,  # NEW
        }
```

### Step 4: Update HTML Generator

Modify `core/report/html_generator.py` to use Java source:

```python
def generate(self, vulnerabilities, ...):
    accordion_html = ""
    
    for vuln in vulnerabilities:
        # Get both Java and Smali code from vulnerability
        java_code = vuln.get('java_source', '// Java source not available')
        smali_code = vuln.get('evidence_snippet', ['// Smali not available'])[0]
        
        accordion_html += f"""
        <div class="source-container">
            <div class="source-header">
                <span>Method Implementation Detail (Evidence)</span>
                <div class="source-toggle">
                    <button class="source-lang-btn active" 
                            onclick="toggleSourceLang(this, 'smali')">Smali</button>
                    <button class="source-lang-btn" 
                            onclick="toggleSourceLang(this, 'java')">Java</button>
                </div>
            </div>
            <pre><code class="source-code-smali" style="display: block;">
{smali_code}
            </code></pre>
            <pre><code class="source-code-java" style="display: none;">
{java_code}
            </code></pre>
        </div>
        """
```

---

## Data Flow

```
APK File
   ↓
JADX Decompiler
   ↓
DecompiledClass objects with:
   - class name
   - method names
   - java code_lines (!!!)
   - smali equivalent
   ↓
SourceCodeManager.extract_from_decompiled_classes()
   ↓
Store in self.java_sources {class_name -> java_code}
   ↓
VulnerabilityScanner gets Java snippet for each vuln
   ↓
Add to Vulnerability object
   ↓
HTML Generator embeds both Java and Smali
   ↓
User can toggle between them with JavaScript
```

---

## Integration Points

### 1. In `run.py` (Main Orchestrator)

**Current:**
```python
scanner = VulnerabilityScanner(extracted_dir)
vulnerabilities = scanner.scan(decompiled_classes)
```

**Updated:**
```python
from core.source_manager import SourceCodeManager

source_mgr = SourceCodeManager()
source_mgr.extract_from_decompiled_classes(decompiled_classes)
source_mgr.extract_from_smali(Path(extracted_dir))

scanner = VulnerabilityScanner(extracted_dir, source_manager=source_mgr)
vulnerabilities = scanner.scan(decompiled_classes)
```

### 2. In `core/vulnerability_v2.py`

**Current:**
```python
def __init__(self, extracted_dir):
    self.extracted_dir = extracted_dir
```

**Updated:**
```python
def __init__(self, extracted_dir, source_manager=None):
    self.extracted_dir = extracted_dir
    self.source_manager = source_manager
```

Then in vulnerability creation:
```python
def _create_vulnerability(self, ...):
    vuln = {
        # ... existing fields ...
        'java_source': '',
        'smali_source': evidence_text,
    }
    
    # Extract Java if source manager available
    if self.source_manager:
        vuln['java_source'] = self.source_manager.get_java_snippet(
            class_name, method_name
        )
    
    return vuln
```

### 3. In `core/report/html_generator.py`

Already ready! Just needs to use the java_source field from vulnerabilities.

---

## Testing Strategy

### Unit Test 1: SourceCodeManager.extract_from_decompiled_classes()
```python
def test_extract_java_source():
    mgr = SourceCodeManager()
    mgr.extract_from_decompiled_classes([mock_decompiled_class])
    
    java_code = mgr.get_java_snippet('com.example.Test')
    assert 'public' in java_code or 'private' in java_code
    assert len(java_code) > 0
```

### Unit Test 2: VulnerabilityScanner with SourceManager
```python
def test_scanner_with_java_extraction():
    source_mgr = SourceCodeManager()
    scanner = VulnerabilityScanner(extracted_dir, source_mgr)
    
    vulns = scanner.scan(decompiled_classes)
    
    # Check that java_source field is populated
    assert vulns[0].get('java_source') != ''
    assert 'Java source' not in vulns[0]['java_source']
```

### Integration Test: Full Pipeline
```bash
python3 run.py analyze benchmarks/AndroGoat.apk --group
# Open evaluation/results/AndroGoat/dashboard.html
# Click "Java" button
# Verify Java code displays (not placeholder)
```

---

## Expected Behavior After Implementation

### Before Integration
1. User opens dashboard
2. Clicks "Java" button
3. Sees: "Java source code coming soon..."

### After Integration
1. User opens dashboard
2. Clicks "Java" button
3. Sees: Clean, readable Java source code with:
   - Full method signature
   - Variable declarations
   - Logic flow
   - Line numbers (optional)
   - Syntax highlighting (future)

---

## Syntax Highlighting (Optional Future Enhancement)

To add syntax highlighting for both Java and Smali:

```html
<!-- Add Highlight.js library -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

<!-- Use appropriate language classes -->
<pre><code class="language-java source-code-java">...</code></pre>
<pre><code class="language-smali source-code-smali">...</code></pre>

<!-- Auto-highlight on toggle -->
<script>
function toggleSourceLang(btn, lang) {
    // ... existing toggle code ...
    
    // Re-highlight new visible code
    document.querySelectorAll('code').forEach(block => {
        hljs.highlightElement(block);
    });
}
</script>
```

---

## Quick Integration Checklist

- [ ] 1. Import SourceCodeManager in run.py
- [ ] 2. Create SourceCodeManager instance
- [ ] 3. Extract Java source from decompiled classes
- [ ] 4. Pass to VulnerabilityScanner
- [ ] 5. Update VulnerabilityScanner to use source_manager
- [ ] 6. Enrich vulnerabilities with java_source field
- [ ] 7. Test with AndroGoat APK
- [ ] 8. Verify dashboard displays Java code
- [ ] 9. Test toggle functionality
- [ ] 10. (Optional) Add syntax highlighting

---

## Files to Modify

1. **run.py** - Add SourceCodeManager initialization
2. **core/vulnerability_v2.py** - Accept source_manager, extract Java code
3. **core/source_manager.py** - Already created, ready to use
4. **core/report/html_generator.py** - Use java_source from vulns (already done!)

---

## Expected Timeline

- **Data Extraction**: 5-10 minutes (extract Java from JADX)
- **Integration**: 10-15 minutes (wire up source manager)
- **Testing**: 5-10 minutes (run analysis, verify)
- **Total**: ~30 minutes for full implementation

---

## Fallback Strategy

If Java extraction fails for any reason:
1. Keep Smali as reliable default
2. Show toggle but only populate one option
3. Log warning but don't crash
4. User can still see Smali code (current state)

---

## Summary

The infrastructure for Java/Smali toggle is **fully in place**. This guide shows how to populate the Java section with actual source code from JADX, completing the user's request for "show Java source instead of Smali with toggle option". The implementation is straightforward and low-risk. 🎯
