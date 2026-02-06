import math
from pathlib import Path
from core.native.models import NativeSinkHit

def calculate_entropy(data):
    if not data: return 0
    entropy = 0
    length = len(data)
    for x in range(256):
        p_x = data.count(x) / length
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy

def find_and_analyze_bins(apk_extract_dir: Path):
    # Cari .so
    native_files = list(apk_extract_dir.rglob("*.so"))
    pre_analysis_hits = []

    for so_path in native_files:
        with open(so_path, "rb") as f:
            data = f.read()
        entropy = calculate_entropy(data)

        if entropy > 7.2:
            # Pseudo-sink untuk packing
            mock_sink = {"name": "packed_native_binary", "layer": "Native", "risk": "Anti-Analysis"}
            pre_analysis_hits.append(NativeSinkHit(
                sink=mock_sink, library=so_path.name, offset="0x0",
                evidence=f"High Entropy: {entropy:.2f}",
                is_syscall=False, is_symbol=False, is_string_based=False
            ))
    return native_files, pre_analysis_hits
