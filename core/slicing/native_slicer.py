class NativeCodeSlicer:
    def slice(self, disassembly_lines, offset, window=5):
        start = max(0, offset - window)
        end = min(len(disassembly_lines), offset + window + 1)

        snippet = []
        for i in range(start, end):
            snippet.append(f"0x{i:08x}: {disassembly_lines[i]}")

        return snippet, offset - start
