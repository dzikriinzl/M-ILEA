from elftools.elf.elffile import ELFFile

def detect_arch(so_path):
    with open(so_path, "rb") as f:
        elf = ELFFile(f)
        return elf['e_machine']
