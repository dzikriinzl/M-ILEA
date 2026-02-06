class JavaCodeSlicer:
    def slice(self, source_lines, line_number, window=5):
        # Smali line numbers seringkali 0-based atau offset, pastikan dalam range
        actual_idx = max(0, line_number - 1) if line_number > 0 else 0
        
        start = max(0, actual_idx - window)
        end = min(len(source_lines), actual_idx + window + 1)

        # Re-format snippet dengan nomor baris dan highlight
        final_snippet = []
        for i in range(start, end):
            prefix = "[*]" if i == actual_idx else "   "
            content = source_lines[i].strip()
            final_snippet.append(f"L{i+1:04d} {prefix} {content}")

        return final_snippet, actual_idx - start