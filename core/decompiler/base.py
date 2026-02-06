from abc import ABC, abstractmethod
from typing import Tuple, List, Dict

class DecompilerBackend(ABC):
    @abstractmethod
    def decompile(self, apk_path):
        """
        Must return:
        - decompiled_classes: List[DecompiledClass]
        - source_code_map: Dict[str, List[str]]
        """
        pass
