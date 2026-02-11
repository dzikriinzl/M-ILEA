"""
Library Detection & Filtering Module
Identifies and filters out third-party library findings to reduce noise.

Common Android Libraries (by package prefix):
- OkHttp: okhttp3.*
- Retrofit: retrofit2.*
- Glide: com.bumptech.glide.*
- Picasso: com.squareup.picasso.*
- RxJava: io.reactivex.*
- Gson: com.google.gson.*
- Firebase: com.google.firebase.*
- AndroidX: androidx.*
- Support Library: android.support.*
"""

THIRD_PARTY_LIBRARY_PATTERNS = [
    # HTTP Clients & Networking
    "okhttp3",
    "retrofit2",
    "com.squareup",
    
    # JSON & Serialization
    "com.google.gson",
    "com.fasterxml.jackson",
    "org.json",
    
    # Image Loading
    "com.bumptech.glide",
    "com.squareup.picasso",
    "com.nostra13.universalimageloader",
    
    # Reactive Programming
    "io.reactivex",
    "rx.android",
    
    # Firebase & Google Services
    "com.google.firebase",
    "com.google.android.gms",
    
    # Architecture Components
    "androidx",
    "android.support",
    "android.arch",
    
    # Other Common Libraries
    "org.apache",
    "com.google.guava",
    "junit",
    "org.junit",
    "org.mockito",
    "org.hamcrest",
]


def is_library_code(class_name: str) -> bool:
    """
    Determine if a class is from a known third-party library.
    
    Args:
        class_name: Fully qualified class name (e.g., "okhttp3.OkHttpClient")
    
    Returns:
        True if the class is from a known library, False otherwise
    """
    for pattern in THIRD_PARTY_LIBRARY_PATTERNS:
        if class_name.startswith(pattern):
            return True
    return False


def tag_finding_origin(finding):
    """
    Add origin tag to finding for reporting purposes.
    
    Args:
        finding: Finding object/dict with 'location' field
    
    Returns:
        Updated finding with 'origin' tag: "library" or "application"
    """
    class_name = finding.get('location', {}).get('class', '')
    
    if is_library_code(class_name):
        finding['origin'] = 'library'
        finding['origin_note'] = 'Third-party library - may not reflect app\'s own protections'
    else:
        finding['origin'] = 'application'
    
    return finding


def filter_findings_by_source(findings, exclude_libraries=False):
    """
    Filter findings by origin (application vs library).
    
    Args:
        findings: List of finding objects
        exclude_libraries: If True, remove library findings; if False, keep all
    
    Returns:
        Filtered list of findings (or same if exclude_libraries=False)
    """
    if not exclude_libraries:
        return findings
    
    return [f for f in findings if not is_library_code(
        f.get('location', {}).get('class', '')
    )]
