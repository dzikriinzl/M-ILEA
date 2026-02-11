from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class EvidenceSlice:
    """
    Model ini menyimpan potongan kode bukti (evidence) yang telah diproses.
    Didesain untuk mendukung dashboard interaktif dan validasi jurnal.
    """
    pattern_type: str
    impact_hint: str
    
    # Metadata lokasi yang presisi
    location: Dict[str, Any]
    
    # Potongan kode yang sudah diformat (L0001 [*] content...)
    code_snippet: List[str]
    
    # Indeks baris di dalam snippet yang harus di-highlight.
    # Menggunakan List karena satu temuan bisa memiliki beberapa baris kritis 
    # (misal: pemuatan string + eksekusi invoke).
    highlighted_lines: List[int] = field(default_factory=list)
    
    # Label penjelasan mendalam (Semantic context ala ARAP)
    semantic_label: str = "Security-Relevant Logic Extraction"
    
    # Skor dari Scorer (0.0 - 1.0)
    confidence_score: float = 0.0
    
    # Metadata tambahan untuk keperluan grouping di UI (Accordion)
    timestamp: str = field(default_factory=lambda: "")

    def to_dict(self):
        """Konversi ke dictionary untuk JSON report"""
        return {
            "pattern_type": self.pattern_type,
            "impact_hint": self.impact_hint,
            "location": self.location,
            "semantic_label": self.semantic_label,
            "confidence_score": self.confidence_score,
            "evidence_snippet": self.code_snippet,
            "highlights": self.highlighted_lines
        }