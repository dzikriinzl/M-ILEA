# M-ILEA: Mobile Application Self-Protection Mechanisms Analyzer

M-ILEA is an automated framework designed to identify, localize, and analyze self-protection mechanisms in Android applications across multiple layers (Java and Native). It implements a context-aware analysis pipeline to provide evidence-based findings for security researchers and penetration testers.

## 🚀 Key Features

* **Hybrid Decompilation:** Seamlessly integrates Smali and JADX backends for comprehensive code extraction.
* **Multi-Layer Analysis:** * **Level 1 & 2:** Java/Kotlin API and string-based detection.
    * **Level 3:** Native library analysis (Symbols & Direct Syscalls).
* **Context-Aware Scoring:** Weighted confidence scoring for high-precision detection.
* **Semantic Mapping:** Automatically maps findings to a 4-Dimensional Security Taxonomy (Purpose, Layer, Strategy, Impact).
* **Evidence Slicing:** Contextual code snippets extracted directly from source/disassembly.

## 🛠 Project Structure

- `core/`: Core analysis logic (Analyzer, Patterns, Slicing, Scoring).
- `cli/`: Command-line interface and orchestrator.
- `data/`: Knowledge base (Sink Registry and Indicators).
- `benchmarks/`: APK testbed for evaluation.
- `utils/`: Common helpers for file handling and decompilation.

## 🚦 Getting Started

### Prerequisites
- Python 3.8+
- Java Runtime Environment (for Apktool/JADX)
- [Optional] `nm` or `objdump` (for Native Analysis)

### Installation
```bash
git clone [https://github.com/dzikriinzl/M-ILEA.git](https://github.com/dzikriinzl/M-ILEA.git)
cd M-ILEA
pip install -r requirements.txt