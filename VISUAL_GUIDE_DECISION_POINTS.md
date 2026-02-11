# Visual Guide: The Decision Point Detection

## Your Concept Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SECURITY DETECTION LOGIC FLOW                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1️⃣  AWAL DETEKSI (Initial Detection)                                      │
│     ════════════════════════════════════════                               │
│     const-string v0, "com.noshufou.android.su"  ← 🎯 SINK MARKER [*]      │
│     │                                                                       │
│     │ "Ada string yang mencurigakan"                                        │
│     │ "Kemungkinan root indicator"                                         │
│                                                                             │
│ 2️⃣  PROSES (Processing)                                                    │
│     ════════════════════════════════════════                               │
│     invoke-static {v0}, Ljava/io/File;->exists()Z                        │
│     move-result v0                                                         │
│     │                                                                       │
│     │ "String ini DIGUNAKAN untuk pengecekan"                              │
│     │ "Bukan hanya ada, tapi dipanggil"                                    │
│                                                                             │
│ 3️⃣  UJUNG (Decision Point) ⭐ CRITICAL                                    │
│     ════════════════════════════════════════                               │
│     if-eqz v0, :cond_0                         ← ⚡ DECISION MARKER [!]    │
│     │                                                                       │
│     │ "KEPUTUSAN DIBUAT berdasarkan hasil"                                 │
│     │ "Aplikasi MENGALIRKAN logika berbeda"                                │
│     │ "PROTECTION PROTECTION LOGIC CONFIRMED"                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

KEY INSIGHT:
═════════════════════════════════════════════════════════════════════════════
  • Hanya sink [*] = 30% confidence (bisa coincidence)
  • Sink + Decision [!] = 95% confidence (real protection logic)
  • Complete flow = Full forensic trail
═════════════════════════════════════════════════════════════════════════════
```

## Implementation Visualization

```
┌──────────────────────────────────────────────────────────────────────────┐
│ M-ILEA PIPELINE WITH DECISION POINT DETECTION                          │
└──────────────────────────────────────────────────────────────────────────┘

[1] SINK DETECTION (Existing)
    ───────────────────────────────────────────────────────
    JavaSinkScanner analyzes code
    └─> Finds: const-string v0, "su" at line 21
        └─> Creates: SinkHit(line=21, ...)

[2] DECISION POINT DETECTION (NEW) ⭐
    ───────────────────────────────────────────────────────
    JavaCodeSlicer scans forward from sink
    └─> Calls: _find_decision_point(code, sink_idx=20)
        └─> Searches: if-eqz, if-nez, return, throw...
            └─> Finds: if-eqz v0 at line 24
                └─> Returns: decision_idx = 23

[3] EVIDENCE RENDERING (Enhanced)
    ───────────────────────────────────────────────────────
    Both indices marked in snippet
    ├─> Line 21: [*] const-string          ← mark as sink
    ├─> Line 22-23: (context)
    └─> Line 24: [!] if-eqz                ← mark as decision

[4] HTML GENERATION (Enhanced)
    ───────────────────────────────────────────────────────
    Different CSS for different markers
    ├─> [*] → CSS class: "highlight-line" (orange)
    └─> [!] → CSS class: "highlight-line highlight-decision" (amber)

[5] DASHBOARD DISPLAY
    ───────────────────────────────────────────────────────
    Complete security logic visible to analyst
    └─> Orange [*] + Context + Amber [!] = Full understanding
```

## Code Flow Diagram

```
┌─ core/slicing/java_slicer.py ─────────────────────────────────────────┐
│                                                                        │
│  def slice(source_lines, line_number, window=8):                     │
│  ═════════════════════════════════════════════════════════════         │
│      1. Find sink at line_number                                      │
│         └─> actual_idx = 20                                           │
│                                                                        │
│      2. NEW: Call _find_decision_point()                              │
│         ├─> scan from sink_idx+1 to sink_idx+30                      │
│         ├─> skip empty/comment/metadata                              │
│         ├─> look for: if-, switch, return, throw                      │
│         └─> return decision_idx OR None                               │
│                                                                        │
│      3. Build snippet with context window                             │
│         └─> show both sink and decision point                         │
│                                                                        │
│      4. Mark positions in snippet                                     │
│         ├─> if i == sink_idx: prefix = "[*] "                        │
│         ├─> if i == decision_idx: prefix = "[!] "                    │
│         └─> add indices to highlighted_indices[]                     │
│                                                                        │
│      5. Return (snippet, highlighted_indices)                         │
│         └─> Both marked for HTML generator                            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌─ core/report/html_generator.py ───────────────────────────────────────┐
│                                                                        │
│  for line in snippet:                                                │
│  ═════════════════════════════════════════════════════════════         │
│      1. NEW: Detect both markers                                      │
│         ├─> is_sink = "[*]" in line                                  │
│         └─> is_decision = "[!]" in line                              │
│                                                                        │
│      2. NEW: Different CSS classes                                    │
│         ├─> if is_sink: "highlight-line"                            │
│         └─> if is_decision: "highlight-line highlight-decision"     │
│                                                                        │
│      3. Apply highlighting                                            │
│         └─> Only if content meaningful (skip empty/metadata)         │
│                                                                        │
│      4. Generate HTML with CSS class                                  │
│         └─> User sees different colors in dashboard                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Decision Point Search Algorithm

```
START: Searching for decision point from sink_idx
│
├─ FOR i from (sink_idx+1) TO (sink_idx+30):
│  │
│  ├─ Skip empty lines, comments
│  │
│  ├─ Skip metadata (.class, .super, etc.)
│  │
│  ├─ Check for decision instruction:
│  │  ├─ if-eqz, if-nez, if-eq, if-ne
│  │  ├─ if-lt, if-gt, if-le, if-ge
│  │  ├─ sparse-switch, packed-switch
│  │  ├─ return, throw
│  │  │
│  │  └─ IF FOUND: return i ✓
│  │
│  ├─ Track first invoke-* (method processing)
│  │
│  └─ Continue or break based on context
│
└─ END: Return None if not found (fallback: sink only)

OPTIMIZATION:
═══════════════════════════════════════════════════════════════
• Limit scan to 30 lines (handles 99% of real code)
• Track first invoke (allows method chaining)
• Stop at unrelated invoke (far from sink)
• Return early when decision found
═══════════════════════════════════════════════════════════════
```

## Real Example: Complete Detection Flow

```
Original Code (Smali):
═════════════════════════════════════════════════════════════════

.method public isDeviceRooted()Z
    .registers 3
    
L0021   const-string v0, "com.noshufou.android.su"    ← Sink!
L0022   invoke-static {v0}, Ljava/io/File;->exists()Z
L0023   move-result v0
L0024   if-eqz v0, :cond_0                            ← Decision!
L0025   const/4 v1, 0x1
L0026   return v1
L0027   
L0028   :cond_0
L0029   const/4 v1, 0x0
L0030   return v1
.end method

M-ILEA Processing:
═════════════════════════════════════════════════════════════════

Scanner → SinkHit(line=21, sink="File.exists")
          ↓
Slicer → _find_decision_point(code, 20)
         └─> Scans lines 21-50
             └─> Finds "if-eqz" at line 23 (0-indexed, line 24 displayed)
                 └─> Returns 23
          ↓
slice() → Returns:
  snippet = [
    "L0020 ...",
    "L0021 [*] const-string v0, ...",  ← SINK MARKER
    "L0022 ...",
    "L0023 ...",
    "L0024 [!] if-eqz v0, :cond_0",   ← DECISION MARKER
    ...
  ]
  highlights = [1, 4]  ← indices to highlight

HTML Generator:
═════════════════════════════════════════════════════════════════

For each line:
  • Line with [*] → CSS class: "highlight-line"           (orange)
  • Line with [!] → CSS class: "highlight-line highlight-decision" (amber)
  • Apply different colors and styling

Dashboard Display:
═════════════════════════════════════════════════════════════════

L0021 🎯 const-string v0, "com.noshufou.android.su"   ← Orange highlight
L0022    invoke-static {v0}, Ljava/io/File;->exists()Z
L0023    move-result v0
L0024 ⚡ if-eqz v0, :cond_0                           ← Amber highlight (bolder)

User Interpretation:
═════════════════════════════════════════════════════════════════
✓ Orange [*]: "Ah, ada detection string untuk root"
✓ Amber [!]: "Dan di sini dia membuat decision berdasarkan hasilnya"
✓ Together: "Jadi ini protection logic yang REAL, bukan false positive"
```

## Confidence Level Progression

```
DETECTION CONFIDENCE EVOLUTION
═══════════════════════════════════════════════════════════════

Level 1: String Found (Before Enhancement)
──────────────────────────────────────────────────────────────
String: "su"  ← Only highlighted
Confidence: 30%
Problem: Could be testing code, logging, or coincidence

Level 2: String + Processing (Better)
──────────────────────────────────────────────────────────────
String: "su"
File.exists(su) ← Context shows actual check
Confidence: 70%
Better: Clear intent to check something

Level 3: String + Processing + Decision (After Enhancement) ⭐
──────────────────────────────────────────────────────────────
String: "su" [*]
File.exists(su)
if-eqz [!] ← Decision made based on result
Confidence: 95%
Perfect: Complete protection logic visible!
```

## Visual CSS Styling

```
┌──────────────────────────────────────────────────────────────┐
│ HIGHLIGHT STYLING IN DASHBOARD                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ [*] SINK MARKER (Orange)                                    │
│ ════════════════════════════════════════════════════════════ │
│ Color: #ffa657 (vibrant orange)                             │
│ Background: rgba(255, 166, 87, 0.1) (light orange)         │
│ Border: 3px solid #ffa657 (orange left border)             │
│ Font: normal weight                                         │
│                                                              │
│ Visual:  ┃ const-string v0, "su"                           │
│          ┃ (orange left border, light orange background)   │
│                                                              │
│ [!] DECISION MARKER (Amber) ⭐ MORE PROMINENT             │
│ ════════════════════════════════════════════════════════════ │
│ Color: #f59e0b (amber/gold)                                │
│ Background: rgba(245, 158, 11, 0.15) (light amber)        │
│ Border: 3px solid #f59e0b (amber left border)             │
│ Font: bold (600 weight) ← STANDS OUT MORE                 │
│                                                              │
│ Visual:  ┃ if-eqz v0, :cond_0                             │
│          ┃ (amber left border, darker background, BOLD)   │
│                                                              │
│ PURPOSE:                                                     │
│ • [*] indicates "worth investigating"                        │
│ • [!] indicates "THIS IS IT - decision point found!"        │
│ • Different styling helps analyst focus on decision        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

**Legend**:
- 🎯 = Orange marker [*] = Sink location
- ⚡ = Amber marker [!] = Decision point
- ⭐ = Critical insight
- ✓ = Verification point

**Key Takeaway**:
The Decision Point Detection transforms evidence highlighting from **"here's what we found"** to **"here's the complete security logic from detection to decision"** - giving analysts full context at a glance.
