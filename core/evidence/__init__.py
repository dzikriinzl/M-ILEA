"""
Evidence-Based Viewer Module

Provides source code extraction, syntax highlighting, and visualization
similar to MobSF's evidence viewer.

Features:
- Extract source files from decompiled APK
- Highlight vulnerable/protective code
- Show context around findings
- Generate HTML viewer for evidence
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class CodeLocation:
    """Represents location in source code"""
    file_path: str
    line_start: int
    line_end: int
    class_name: Optional[str] = None
    method_name: Optional[str] = None


@dataclass
class CodeSnippet:
    """Represents a code snippet with highlighting"""
    location: CodeLocation
    lines: List[str]              # Full lines with line numbers
    highlighted_lines: List[int]  # Line numbers to highlight
    context_before: int = 2       # Lines before finding
    context_after: int = 2        # Lines after finding
    
    def to_dict(self):
        return {
            "location": asdict(self.location),
            "lines": self.lines,
            "highlighted_lines": self.highlighted_lines,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


class SourceExtractor(ABC):
    """Abstract base for source code extraction"""
    
    @abstractmethod
    def extract_file(self, file_path: str) -> Optional[str]:
        """Extract source code for a file"""
        pass
    
    @abstractmethod
    def get_lines(self, file_path: str, line_start: int, 
                 line_end: int, context: int = 2) -> Optional[CodeSnippet]:
        """Extract specific line range with context"""
        pass


class JavaSourceExtractor(SourceExtractor):
    """Extract source from decompiled Java/Smali code"""
    
    def __init__(self, source_root: Path):
        self.source_root = source_root
    
    def extract_file(self, file_path: str) -> Optional[str]:
        """
        Extract Java source file.
        
        Args:
            file_path: Relative path like "com/example/MainActivity.java"
        """
        full_path = self.source_root / file_path
        
        if not full_path.exists():
            logger.warning(f"Source file not found: {full_path}")
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading source file {full_path}: {e}")
            return None
    
    def get_lines(self, file_path: str, line_start: int, 
                 line_end: int, context: int = 2) -> Optional[CodeSnippet]:
        """
        Extract specific lines with context.
        
        Args:
            file_path: Relative path to source file
            line_start: Starting line number (1-indexed)
            line_end: Ending line number (1-indexed)
            context: Lines of context to include
        """
        content = self.extract_file(file_path)
        if not content:
            return None
        
        lines = content.split('\n')
        
        # Calculate range with context
        ctx_start = max(0, line_start - 1 - context)
        ctx_end = min(len(lines), line_end + context)
        
        # Extract lines
        snippet_lines = []
        for i in range(ctx_start, ctx_end):
            line_num = i + 1
            line_content = lines[i] if i < len(lines) else ""
            
            # Format: "   45 | code content"
            formatted = f"{line_num:4d} | {line_content}"
            snippet_lines.append(formatted)
        
        # Highlighted lines (relative to snippet start)
        highlighted = []
        for line_num in range(line_start, line_end + 1):
            if line_num >= ctx_start + 1 and line_num <= ctx_end:
                highlighted.append(line_num - ctx_start)
        
        location = CodeLocation(
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            class_name=self._extract_class_name(lines, line_start),
            method_name=self._extract_method_name(lines, line_start)
        )
        
        return CodeSnippet(
            location=location,
            lines=snippet_lines,
            highlighted_lines=highlighted,
            context_before=context,
            context_after=context
        )
    
    @staticmethod
    def _extract_class_name(lines: List[str], around_line: int) -> Optional[str]:
        """Find class name from 'public class ClassName'"""
        for i in range(max(0, around_line - 50), around_line):
            line = lines[i] if i < len(lines) else ""
            if "class " in line:
                # Extract class name
                parts = line.split("class ")
                if len(parts) > 1:
                    class_part = parts[1].split("{")[0].split("(")[0].strip()
                    return class_part
        return None
    
    @staticmethod
    def _extract_method_name(lines: List[str], around_line: int) -> Optional[str]:
        """Find method name from 'void methodName('"""
        for i in range(around_line - 1, max(0, around_line - 30), -1):
            line = lines[i] if i < len(lines) else ""
            if "(" in line and ("public" in line or "private" in line or "protected" in line):
                # Extract method name
                if "(" in line:
                    method_part = line.split("(")[0].strip().split()[-1]
                    return method_part
        return None


class SyntaxHighlighter:
    """
    Highlight code syntax for HTML display.
    
    Supports: Java, Smali, Python, etc.
    """
    
    # Simple keyword highlighting (can be enhanced with pygments if needed)
    JAVA_KEYWORDS = {
        'public', 'private', 'protected', 'class', 'interface', 'enum',
        'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break',
        'return', 'new', 'this', 'super', 'extends', 'implements',
        'try', 'catch', 'finally', 'throw', 'throws', 'static', 'final',
        'abstract', 'volatile', 'synchronized', 'native', 'transient',
        'instanceof', 'import', 'package', 'true', 'false', 'null'
    }
    
    SENSITIVE_PATTERNS = {
        '/system/xbin/su': 'su binary',
        '/system/bin/su': 'su binary',
        'su ': 'su command',
        'Runtime.exec': 'Runtime execution',
        'ProcessBuilder': 'Process builder',
        'Debug.isDebuggerConnected': 'Debugger check',
        'Debug.waitingForDebugger': 'Debugger wait',
        'android.os.Debug': 'Debug API',
        'Build.FINGERPRINT': 'Device fingerprint',
        'Build.HARDWARE': 'Hardware check',
        'ro.kernel.qemu': 'Emulator detection',
        'Build.MODEL': 'Model check',
    }
    
    @classmethod
    def highlight_java(cls, code: str, highlight_lines: List[int] = None) -> str:
        """
        Highlight Java code for HTML.
        
        Args:
            code: Java source code
            highlight_lines: Lines to highlight (1-indexed)
        
        Returns:
            HTML-safe highlighted code
        """
        import html
        
        lines = code.split('\n')
        highlighted_html = []
        
        for i, line in enumerate(lines, 1):
            line_html = html.escape(line)
            
            # Highlight keywords
            for keyword in cls.JAVA_KEYWORDS:
                # Word boundary regex-like matching
                line_html = line_html.replace(
                    keyword,
                    f'<span class="kw">{keyword}</span>'
                )
            
            # Highlight sensitive patterns
            for pattern, label in cls.SENSITIVE_PATTERNS.items():
                if pattern in line:
                    line_html = line_html.replace(
                        pattern,
                        f'<span class="sensitive" title="{label}">{pattern}</span>'
                    )
            
            # Highlight entire line if in highlight_lines
            if highlight_lines and i in highlight_lines:
                line_html = f'<span class="highlighted-line">{line_html}</span>'
            
            highlighted_html.append(line_html)
        
        return '\n'.join(highlighted_html)


class EvidenceViewer:
    """
    Generate interactive HTML evidence viewer.
    
    Similar to MobSF's file viewer with highlighting.
    """
    
    def __init__(self, source_root: Path, output_dir: Path):
        self.extractor = JavaSourceExtractor(source_root)
        self.output_dir = output_dir
        self.highlighter = SyntaxHighlighter()
    
    def generate_evidence_html(self, finding) -> str:
        """
        Generate HTML for a single finding's evidence.
        
        Args:
            finding: Finding object with location, evidence_snippet, etc.
        
        Returns:
            HTML string for embedding in report
        """
        loc = finding.location if isinstance(finding.location, dict) else asdict(finding.location)
        
        file_path = loc.get('file', loc.get('filename', 'Unknown'))
        line_start = loc.get('line_start', loc.get('line', 0))
        line_end = loc.get('line_end', line_start)
        
        # Try to extract source
        snippet = self.extractor.get_lines(file_path, line_start, line_end, context=3)
        
        if not snippet:
            # Fallback: use provided evidence_snippet
            return self._generate_fallback_html(finding)
        
        # Generate HTML
        protection_type = getattr(finding, 'protection_type', 'Unknown')
        confidence = getattr(finding, 'confidence_score', 
                           getattr(finding, 'signal_confidence', 0.4))
        
        html = f"""
<div class="evidence-viewer">
    <div class="evidence-header">
        <h3>{protection_type}</h3>
        <div class="evidence-meta">
            <span class="confidence">Confidence: {confidence:.2f}</span>
            <span class="location">{file_path}:{line_start}</span>
        </div>
    </div>
    
    <div class="code-viewer">
        <div class="code-header">
            <button class="view-btn">📄 View Full File</button>
            <span class="file-path">{file_path}</span>
        </div>
        
        <pre><code class="code-content">
{self._format_code_snippet(snippet)}
        </code></pre>
    </div>
    
    <div class="evidence-details">
        <h4>Detection Details</h4>
        <ul>
        """
        
        # Add breakdown details
        if hasattr(finding, 'confidence_breakdown'):
            breakdown = finding.confidence_breakdown
            for key, value in breakdown.items():
                if value:
                    html += f"<li><strong>{key}:</strong> {value}</li>"
        
        html += "</ul></div></div>"
        
        return html
    
    @staticmethod
    def _format_code_snippet(snippet: CodeSnippet) -> str:
        """Format code snippet with line numbers and highlighting"""
        result = []
        
        for i, line in enumerate(snippet.lines, 1):
            line_num = int(line.split('|')[0].strip())
            
            if i in snippet.highlighted_lines:
                result.append(f">>> {line}  ◄── DETECTION")
            else:
                result.append(f"    {line}")
        
        return '\n'.join(result)
    
    @staticmethod
    def _generate_fallback_html(finding) -> str:
        """Generate HTML when source file not available"""
        protection_type = getattr(finding, 'protection_type', 'Unknown')
        confidence = getattr(finding, 'confidence_score',
                           getattr(finding, 'signal_confidence', 0.4))
        evidence = getattr(finding, 'evidence_snippet', [])
        
        evidence_str = '<br>'.join(
            [line.replace('[*]', '🎯').replace('[!]', '⚡') 
             for line in evidence]
        )
        
        return f"""
<div class="evidence-viewer">
    <div class="evidence-header">
        <h3>{protection_type}</h3>
        <div class="evidence-meta">
            <span class="confidence">Confidence: {confidence:.2f}</span>
        </div>
    </div>
    
    <div class="code-viewer">
        <pre><code class="code-content">
{evidence_str}
        </code></pre>
    </div>
</div>
"""


class EvidenceCollector:
    """
    Collect and organize evidence across findings.
    
    Groups evidence by type and generates comparison views.
    """
    
    @staticmethod
    def group_evidence_by_type(findings: List) -> Dict[str, List]:
        """Group findings by protection type"""
        grouped = {}
        
        for f in findings:
            ptype = getattr(f, 'protection_type', 'Unknown')
            if ptype not in grouped:
                grouped[ptype] = []
            grouped[ptype].append(f)
        
        return grouped
    
    @staticmethod
    def get_unique_evidence(findings: List) -> Dict[str, int]:
        """Count unique evidence patterns"""
        evidence_counts = {}
        
        for f in findings:
            evidence = getattr(f, 'evidence_snippet', [])
            evidence_str = ''.join(evidence)
            
            evidence_counts[evidence_str] = evidence_counts.get(evidence_str, 0) + 1
        
        return evidence_counts
