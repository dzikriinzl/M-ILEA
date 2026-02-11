import subprocess
import os
import sys
from pathlib import Path

# Sesuaikan path relatif karena script ini berada di dalam folder 'evaluation'
# BASE_DIR adalah root proyek (M-ILEA)
BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / "evaluation" / "apps"
RESULTS_DIR = BASE_DIR / "evaluation" / "results"
RUN_SCRIPT = BASE_DIR / "run.py"

def run_batch_analysis():
    # Pastikan direktori ada
    if not APPS_DIR.exists():
        print(f"[-] Error: Direktori aplikasi tidak ditemukan di {APPS_DIR}")
        return

    apk_files = list(APPS_DIR.glob("*.apk"))
    print(f"[*] Found {len(apk_files)} applications for evaluation.")

    for apk in apk_files:
        print(f"\n[>] Analyzing {apk.name}...")
        
        # Penentuan path output JSON (opsional, karena run.py Anda sudah 
        # otomatis membuat folder di evaluation/results/[nama_apk])
        # Kita biarkan run.py menangani output agar dashboard & JSON tetap satu folder
        
        try:
            # Menjalankan run.py dari root direktori
            # Kita gunakan sys.executable untuk memastikan menggunakan python yang sama
            subprocess.run([
                sys.executable, str(RUN_SCRIPT), "analyze", str(apk),
                "--group"
            ], check=True, cwd=str(BASE_DIR))
            
            print(f"[+] Success: {apk.name}")
        except subprocess.CalledProcessError as e:
            print(f"[-] Failed: {apk.name}. Error: {e}")
        except Exception as e:
            print(f"[-] Unexpected Error: {e}")

if __name__ == "__main__":
    # Membuat direktori hasil jika belum ada
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_batch_analysis()