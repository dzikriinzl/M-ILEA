"""
M-ILEA Core Integration Module
Provides 4-category self-protection classification for Android APK analysis
"""

from .m2_integrator import M2AnalysisIntegrator, integrate_with_m_ilea

__all__ = ["M2AnalysisIntegrator", "integrate_with_m_ilea"]
