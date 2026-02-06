from pathlib import Path
from typing import Dict, List, Tuple, Set
from core.decompiler.base import DecompilerBackend
from core.decompiler.models import DecompiledClass, DecompiledMethod

try:
    from jadx.api import JadxDecompiler
except ImportError:
    JadxDecompiler = None

class JadxBackend(DecompilerBackend):
    DECOMPILATION_ERROR_MARKERS = ["JADX ERROR", "Method generation error"]

    def decompile(self, apk_path: Path) -> Tuple[Dict[str, DecompiledClass], Set[str]]:
        if not JadxDecompiler:
            raise ImportError("jadx-python tidak terinstal.")

        jadx = JadxDecompiler()
        jadx.load_file(str(apk_path))

        decompiled_map = {}
        failed_classes = set()

        for cls in jadx.get_classes():
            code = cls.get_code()
            fqcn = cls.get_full_name()

            if not code or any(marker in code for marker in self.DECOMPILATION_ERROR_MARKERS):
                failed_classes.add(fqcn)
                continue

            methods = []
            for m in cls.get_methods():
                m_code = m.get_code()
                if m_code:
                    methods.append(DecompiledMethod(
                        name=m.get_name(),
                        code_lines=m_code.splitlines()
                    ))

            decompiled_map[fqcn] = DecompiledClass(name=fqcn, methods=methods)

        return decompiled_map, failed_classes
