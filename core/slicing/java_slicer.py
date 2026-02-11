class JavaCodeSlicer:
    def __init__(self):
        # Daftar instruksi Smali yang dianggap sebagai 'eksekusi nyata'
        self.executable_opcodes = [
            "invoke-", "const-string", "if-", "check-cast", 
            "new-instance", "sget", "iget", "return", "throw"
        ]
        
        # Instruksi keputusan (Decision Points) - Titik akhir sebuah deteksi
        self.decision_instructions = [
            "if-eqz", "if-nez", "if-eq", "if-ne", "if-lt", "if-gt", "if-le", "if-ge",
            "if-eqz/range", "if-nez/range",
            "sparse-switch", "packed-switch",
            "return", "throw"  # Return/throw juga merupakan decision point
        ]

    def _find_decision_point(self, source_lines, sink_idx):
        """
        Scan ke bawah dari sink untuk menemukan DECISION POINT.
        Decision point adalah instruksi kondisional yang mengkonsumsi hasil deteksi.
        
        Contoh:
        L0021     const-string v0, "su"            ← SINK (Awal Deteksi)
        L0022     invoke-static {v0}, File->exists ← SINK PROCESSING (Proses)
        L0023     move-result v0                    ← Data preparation
        L0024     if-eqz v0, :cond_0               ← DECISION POINT (Ujung!)
        """
        scan_limit = 30  # Scan hingga 30 baris ke bawah untuk handle complex chains
        first_invoke_seen = False
        
        for i in range(sink_idx + 1, min(sink_idx + scan_limit, len(source_lines))):
            line_content = source_lines[i].strip()
            
            # Skip baris kosong dan komentar
            if not line_content or line_content.startswith("#"):
                continue
            
            # Skip metadata directives
            if line_content.startswith("."):
                continue
            
            # Cari decision instruction (SEBELUM membuat logic break)
            for decision_op in self.decision_instructions:
                if decision_op in line_content:
                    return i  # Ketemu decision point
            
            # Track first invoke setelah sink
            if "invoke-" in line_content:
                if not first_invoke_seen:
                    first_invoke_seen = True
                    # Continue scanning setelah first invoke
                else:
                    # Invoke ke-2 = mungkin sudah masuk logika berbeda
                    # TAPI jangan hentikan immediately, scan lebih lanjut
                    # karena mungkin ada method chaining (invoke-virtual calls)
                    # Hanya hentikan jika sudah sangat jauh dari sink
                    if i > sink_idx + 15:
                        break
        
        return None  # Tidak ada decision point ditemukan

    def slice(self, source_lines, line_number, window=8):
        """
        Slice dengan fokus pada DECISION POINT (konsep titik akhir).
        
        Strategi highlighting:
        1. Cari sink di line_number
        2. Scan ke bawah untuk menemukan decision point
        3. Highlight BOTH: sink (awal) dan decision point (ujung)
        4. Tampilkan konteks penuh (awal → proses → ujung)
        """
        raw_idx = max(0, line_number - 1)
        sink_idx = raw_idx
        found_executable = False
        fallback_idx = None
        
        # STEP 1: Temukan SINK (const-string atau invoke-)
        for i in range(raw_idx, min(raw_idx + 15, len(source_lines))):
            line_content = source_lines[i].strip()
            
            # Skip baris kosong dan komentar
            if not line_content or line_content.startswith("#"):
                continue
                
            # Abaikan metadata, tapi simpan sebagai fallback
            if line_content.startswith("."):
                if not fallback_idx and not any(op in line_content for op in self.executable_opcodes):
                    if "=" in line_content or ":" in line_content or len(line_content) > 20:
                        fallback_idx = i
                continue
                
            # Sink ditemukan: const-string atau invoke-
            if ("const-string" in line_content or "invoke-" in line_content):
                sink_idx = i
                found_executable = True
                break
            
            # Fallback untuk library code
            if not found_executable and line_content and not line_content.startswith("#"):
                if not fallback_idx:
                    fallback_idx = i

        # Jika tidak ketemu sink, gunakan fallback
        if not found_executable and fallback_idx is not None:
            sink_idx = fallback_idx

        # STEP 2: Scan ke bawah untuk DECISION POINT
        decision_idx = self._find_decision_point(source_lines, sink_idx)
        
        # Tentukan jendela tampilan yang mencakup sink dan decision point
        if decision_idx is not None:
            # Tampilkan dari sink sampai decision point + context window
            start = max(0, sink_idx - window)
            end = min(len(source_lines), decision_idx + window + 1)
        else:
            # Jika tidak ada decision point, tampilkan konteks normal di sekitar sink
            start = max(0, sink_idx - window)
            end = min(len(source_lines), sink_idx + window + 1)

        final_snippet = []
        highlighted_indices = []

        for i in range(start, end):
            content = source_lines[i].rstrip()
            prefix = "    "
            relative_idx = i - start
            
            # Highlight SINK (awal deteksi) - dengan [*]
            if i == sink_idx:
                prefix = "[*] "
                content_stripped = content.strip()
                if content_stripped and not content_stripped.startswith(("#",)):
                    highlighted_indices.append(relative_idx)
            
            # Highlight DECISION POINT (ujung deteksi) - dengan [!]
            elif decision_idx is not None and i == decision_idx:
                prefix = "[!] "  # Tanda beda untuk decision point
                content_stripped = content.strip()
                if content_stripped and not content_stripped.startswith(("#",)):
                    highlighted_indices.append(relative_idx)
            
            final_snippet.append(f"L{i+1:04d} {prefix} {content}")

        return final_snippet, highlighted_indices