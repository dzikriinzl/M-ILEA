from dataclasses import dataclass
from typing import List

@dataclass
class DecompiledMethod:
    name: str
    code_lines: List[str]

@dataclass
class DecompiledClass:
    name: str
    methods: List[DecompiledMethod]
