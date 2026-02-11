#!/usr/bin/env python3
"""
Test decision point detection in JavaCodeSlicer.
This demonstrates the new concept of highlighting based on decision points,
not just sink locations.
"""

from core.slicing.java_slicer import JavaCodeSlicer

# Test case 1: Root detection with clear decision point
test_code_1 = [
    ".class public Lcom/example/app/RootChecker;",
    ".super Ljava/lang/Object;",
    "",
    ".method public isDeviceRooted()Z",
    "    .registers 3",
    "",
    "    const-string v0, \"com.noshufou.android.su\"",  # L0007 - SINK (Awal deteksi)
    "    invoke-static {v0}, Ljava/io/File;->exists()Z",  # L0008 - Processing
    "    move-result v0",  # L0009 - Result preparation
    "    if-eqz v0, :cond_0",  # L0010 - DECISION POINT (Ujung deteksi)
    "",
    "    const/4 v1, 0x1",
    "    return v1",
    "",
    "    :cond_0",
    "    const/4 v1, 0x0",
    "    return v1",
    ".end method",
]

# Test case 2: Multiple root indicators in sequence
test_code_2 = [
    ".class public Lcom/example/app/DetailedRootChecker;",
    ".super Ljava/lang/Object;",
    "",
    ".method private checkMagisk()Z",
    "    .registers 2",
    "",
    "    const-string v0, \"magisk\"",  # L0006 - SINK
    "    invoke-static {v0}, Ljava/lang/Runtime;->exec()L...",  # L0007 - Processing
    "    move-result-object v0",  # L0008",
    "    if-nez v0, :not_found",  # L0009 - DECISION POINT
    "",
    "    const/4 v1, 0x1",
    "    return v1",
    "",
    "    :not_found",
    "    const/4 v1, 0x0",
    "    return v1",
    ".end method",
]

# Test case 3: String match followed by API check
test_code_3 = [
    ".method public isEmulator()Z",
    "    .registers 4",
    "",
    "    const-string v0, \"ro.secure\"",  # L0003 - SINK
    "    invoke-static {v0}, Landroid/os/SystemProperties;->get()L...",  # L0004",
    "    move-result-object v1",  # L0005",
    "    const-string v2, \"0\"",  # L0006",
    "    invoke-virtual {v1, v2}, Ljava/lang/String;->equals()Z",  # L0007",
    "    move-result v1",  # L0008",
    "    if-eqz v1, :not_emulator",  # L0009 - DECISION POINT",
    "",
    "    const/4 v3, 0x1",
    "    return v3",
    "",
    "    :not_emulator",
    "    const/4 v3, 0x0",
    "    return v3",
    ".end method",
]

def test_slicer(test_code, description, expected_sink_line, expected_decision_line):
    """Test the JavaCodeSlicer with decision point detection."""
    
    slicer = JavaCodeSlicer()
    
    # The scanner would report this line number (1-indexed)
    line_number = expected_sink_line
    
    snippet, highlights = slicer.slice(test_code, line_number, window=5)
    
    print(f"\n{'=' * 80}")
    print(f"TEST: {description}")
    print(f"{'=' * 80}")
    
    print(f"\nInput:")
    print(f"  - Sink reported at line: {expected_sink_line}")
    print(f"  - Expected decision point: {expected_decision_line}")
    
    print(f"\nOutput Snippet:")
    for idx, line in enumerate(snippet):
        is_highlighted = idx in highlights
        marker = " ✓ HIGHLIGHTED" if is_highlighted else ""
        print(f"  {line}{marker}")
    
    print(f"\nAnalysis:")
    print(f"  - Highlighted line indices: {highlights}")
    print(f"  - Total lines in snippet: {len(snippet)}")
    
    # Verify
    has_sink_marker = any("[*]" in line for line in snippet)
    has_decision_marker = any("[!]" in line for line in snippet)
    
    print(f"\nMarkers Found:")
    print(f"  - [*] Sink marker: {'YES' if has_sink_marker else 'NO'}")
    print(f"  - [!] Decision marker: {'YES' if has_decision_marker else 'NO'}")
    
    if has_sink_marker and has_decision_marker:
        print(f"\n✓ SUCCESS: Both sink and decision point markers present!")
    elif has_sink_marker:
        print(f"\n⚠ PARTIAL: Sink marker found, but decision point not detected")
    else:
        print(f"\n✗ ISSUE: No markers found")
    

# Run tests
print("\n" + "=" * 80)
print("DECISION POINT DETECTION TEST SUITE")
print("=" * 80)

test_slicer(test_code_1, "Root detection with File.exists()", 7, 10)
test_slicer(test_code_2, "Root detection with Runtime.exec()", 6, 9)
test_slicer(test_code_3, "Emulator detection with SystemProperties", 4, 10)

print("\n" + "=" * 80)
print("CONCEPT VERIFICATION")
print("=" * 80)
print("""
The decision point detection follows this logic:

1. SINK (Awal Deteksi): The point where we detect a security-relevant string
   Example: const-string v0, "com.noshufou.android.su"
   Marker: [*]

2. PROCESSING (Proses): The point where we process/use the detected value
   Example: invoke-static {v0}, Ljava/io/File;->exists()Z
   This uses the string we detected

3. DECISION POINT (Ujung Deteksi): The conditional that makes the decision
   Example: if-eqz v0, :cond_0
   Marker: [!]
   THIS is where the application actually decides based on our detection

By highlighting BOTH sink and decision point:
- Sink shows WHAT was detected
- Decision point shows WHERE the detection is actually used
- Context shows the complete logical flow

This matches your requirement that the highlighting should show the complete
"The Decision Point" (titik akhir secara teknis) where the app makes its choice.
""")
