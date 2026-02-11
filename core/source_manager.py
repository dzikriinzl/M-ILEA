"""
Source Code Manager

Handles extraction and management of source code from decompiled classes.
Provides both Java and Smali versions for vulnerability evidence display.
"""

from typing import Dict, List, Optional
from pathlib import Path


class SourceCodeManager:
    """Manages Java and Smali source code extraction"""
    
    def __init__(self):
        self.java_sources: Dict[str, str] = {}  # Class name -> Java source
        self.smali_sources: Dict[str, str] = {}  # Class name -> Smali source
    
    def extract_from_decompiled_classes(self, decompiled_classes: List) -> None:
        """
        Extract Java source code from decompiled classes.
        
        JADX provides Java source in code_lines from methods.
        We reconstruct the class-level source.
        """
        for cls in decompiled_classes:
            class_name = getattr(cls, 'name', 'Unknown')
            
            # Get method code (Java source)
            methods = getattr(cls, 'methods', [])
            java_code_lines = []
            
            # Add class header
            java_code_lines.append(f"// Class: {class_name}")
            java_code_lines.append("")
            
            for method in methods:
                method_name = getattr(method, 'name', 'Unknown')
                code_lines = getattr(method, 'code_lines', [])
                
                if isinstance(code_lines, list):
                    java_code_lines.extend(code_lines)
                else:
                    java_code_lines.append(str(code_lines))
                
                java_code_lines.append("")  # Spacing between methods
            
            java_source = "\n".join(java_code_lines)
            self.java_sources[class_name] = java_source
    
    def get_java_snippet(self, class_name: str, method_name: str = None, 
                        context_lines: int = 5) -> str:
        """
        Get Java source code snippet for a class/method.
        
        Args:
            class_name: Full class name
            method_name: Optional specific method name
            context_lines: Number of lines to include around match
        
        Returns:
            Java source snippet
        """
        if class_name not in self.java_sources:
            return f"// Source not available for {class_name}"
        
        source = self.java_sources[class_name]
        lines = source.split("\n")
        
        if method_name:
            # Find method and include context
            for i, line in enumerate(lines):
                if method_name in line and ("public" in line or "private" in line or "protected" in line):
                    # Found method signature
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 10)
                    return "\n".join(lines[start:end])
        
        # Return first N lines of class
        return "\n".join(lines[:20])
    
    def extract_from_smali(self, extracted_dir: Path) -> None:
        """
        Extract Smali source code from extracted APK.
        
        Args:
            extracted_dir: Path to extracted APK directory
        """
        if not extracted_dir:
            return
        
        # Find all smali files
        smali_dirs = list(extracted_dir.glob("smali*"))
        
        for smali_dir in smali_dirs:
            if not smali_dir.is_dir():
                continue
            
            # Recursively find .smali files
            for smali_file in smali_dir.rglob("*.smali"):
                try:
                    with open(smali_file, 'r', encoding='utf-8', errors='ignore') as f:
                        smali_content = f.read()
                    
                    # Extract class name from path
                    # smali/com/example/MyClass.smali -> com.example.MyClass
                    rel_path = smali_file.relative_to(smali_dir)
                    class_name = str(rel_path).replace('/', '.').replace('.smali', '')
                    
                    self.smali_sources[class_name] = smali_content
                except Exception as e:
                    pass
    
    def get_smali_snippet(self, class_name: str, context_lines: int = 10) -> str:
        """
        Get Smali source code snippet.
        
        Args:
            class_name: Full class name
            context_lines: Number of lines to return
        
        Returns:
            Smali source snippet
        """
        if class_name not in self.smali_sources:
            return f"// Smali source not available for {class_name}"
        
        source = self.smali_sources[class_name]
        lines = source.split("\n")
        
        # Return first N lines
        return "\n".join(lines[:context_lines])
    
    def get_source(self, class_name: str, method_name: str = None, 
                   language: str = "java", context_lines: int = 5) -> str:
        """
        Get source code in specified language.
        
        Args:
            class_name: Full class name
            method_name: Optional method name
            language: 'java' or 'smali'
            context_lines: Lines of context
        
        Returns:
            Source code snippet
        """
        if language.lower() == "java":
            return self.get_java_snippet(class_name, method_name, context_lines)
        elif language.lower() == "smali":
            return self.get_smali_snippet(class_name, context_lines)
        else:
            return "Invalid language. Use 'java' or 'smali'"
