from pathlib import Path
from core.decompiler.smali import decompile_apk_smali
from core.decompiler.jadx_backend import JadxBackend

def decompile_hybrid(apk_path: Path):
    """
    Orkestrasi Decompiler: 
    Mencoba JADX (Level 2), jika gagal (obfuscated/error) fallback ke Smali (Level 1).
    Mengembalikan: final_classes, source_map, extracted_dir
    """
    # 1. Jalankan Smali (Selalu sukses mengekstrak APK)
    smali_classes, smali_source, extracted_dir = decompile_apk_smali(apk_path)

    # 2. Jalankan JADX
    try:
        jadx_backend = JadxBackend()
        jadx_map, failed_names = jadx_backend.decompile(apk_path)
    except Exception:
        jadx_map, failed_names = {}, set()

    final_classes = []
    source_map = {}

    # 3. Gabungkan Hasil (Prioritas JADX karena lebih readable untuk Slicer)
    for cls_name, jadx_cls in jadx_map.items():
        final_classes.append(jadx_cls)
        # Rekonstruksi source code dari methods untuk source_map
        full_code = []
        for m in jadx_cls.methods:
            full_code.extend(m.code_lines)
        source_map[cls_name] = full_code

    # 4. Fallback: Tambahkan kelas dari Smali yang gagal di JADX
    for s_cls in smali_classes:
        if s_cls.name in failed_names or s_cls.name not in jadx_map:
            final_classes.append(s_cls)
            source_map[s_cls.name] = smali_source.get(s_cls.name, [])

    return final_classes, source_map, extracted_dir
