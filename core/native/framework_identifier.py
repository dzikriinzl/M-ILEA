from typing import List

class FrameworkIdentifier:
    """
    Identifies the underlying mobile framework to contextualize 
    subsequent native and logic analysis.
    """

    FRAMEWORK_LIBS = {
        "Flutter": ["libflutter.so", "libapp.so"],
        "ReactNative": ["libreactnativejni.so", "libhermes.so"],
        "Unity": ["libunity.so", "libmain.so", "libil2cpp.so"],
        "Xamarin": ["libmonosgen-2.0.so", "libmonodroid.so"],
        "Cordova": ["libchord.so"]
    }

    def identify(self, lib_names: List[str]) -> List[str]:
        """
        Input: Daftar nama file .so yang ditemukan di APK
        Output: List framework yang terdeteksi
        """
        detected = []
        # Normalisasi ke lowercase untuk robustness
        libs_lower = [lib.lower() for lib in lib_names]

        for fw, indicators in self.FRAMEWORK_LIBS.items():
            if any(ind.lower() in libs_lower for ind in indicators):
                detected.append(fw)

        return detected
