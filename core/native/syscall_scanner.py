import re
from core.native.models import NativeSinkHit

def scan_syscalls(disassembly_lines, sink_registry, library_name="unknown"):
    hits = []

    for idx, line in enumerate(disassembly_lines):
        # Deteksi instruksi SVC (Supervisor Call) pada ARM/ARM64
        if "svc" in line:
            # Menggunakan regex untuk menangkap ID baik desimal maupun heksa
            # Contoh: svc #26, svc 0x1a, svc #0x1a
            match = re.search(r"(?:#|svc\s+)(0x[0-9a-fA-F]+|[0-9]+)", line)
            if not match:
                continue

            try:
                val = match.group(1)
                syscall_id = int(val, 16) if val.startswith("0x") else int(val)
            except ValueError:
                continue

            sink = sink_registry.match_native_syscall(syscall_id)
            if sink:
                hits.append(
                    NativeSinkHit(
                        sink=sink,
                        library=library_name,
                        offset=hex(idx), # Menggunakan format heksadesimal untuk offset biner
                        evidence=line.strip(),
                        is_syscall=True,
                        is_symbol=False,
                        is_string_based=False,
                        # Parameter tambahan untuk sinkronisasi Step 3-6
                        arguments=[f"Syscall ID: {syscall_id}"],
                        conditional=True,
                        context_snippet=[line.strip()]
                    )
                )
    return hits