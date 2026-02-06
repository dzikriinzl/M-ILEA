import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict
from core.decompiler.models import DecompiledClass, DecompiledMethod

def decompile_apk_smali(apk_path: Path):
    """
    Level 1 Decompiler: DEX -> Smali menggunakan apktool.
    Mengembalikan: classes, source_map, dan tmpdir (untuk analisis native).
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="milea_"))

    try:
        subprocess.run(
            ["apktool", "d", str(apk_path), "-o", str(tmpdir), "-f"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        raise RuntimeError("apktool tidak ditemukan di PATH.")
    except subprocess.CalledProcessError:
        raise RuntimeError("apktool gagal mendekode APK.")

    decompiled_classes: List[DecompiledClass] = []
    source_code_map: Dict[str, List[str]] = {}

    # Multi-DEX Support: cari semua folder smali*
    smali_dirs = [d for d in tmpdir.iterdir() if d.is_dir() and d.name.startswith("smali")]

    for smali_dir in smali_dirs:
        for smali_file in smali_dir.rglob("*.smali"):
            lines = smali_file.read_text(errors="ignore").splitlines()
            class_name = None
            methods = []
            current_method = None
            buffer = []

            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith(".class"):
                    parts = clean_line.split()
                    class_name = parts[-1].lstrip("L").rstrip(";").replace("/", ".")
                elif clean_line.startswith(".method"):
                    current_method = clean_line.split()[-1]
                    buffer = []
                elif clean_line.startswith(".end method"):
                    if current_method:
                        methods.append(DecompiledMethod(name=current_method, code_lines=buffer))
                    current_method = None
                elif current_method:
                    buffer.append(line) # Simpan line asli (dengan indentasi)

            if class_name:
                decompiled_classes.append(DecompiledClass(name=class_name, methods=methods))
                source_code_map[class_name] = lines

    return decompiled_classes, source_code_map, tmpdir
