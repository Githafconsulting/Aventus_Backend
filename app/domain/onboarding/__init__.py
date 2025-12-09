# Onboarding workflow domain module
from app.domain.onboarding.registry import OnboardingRegistry
from app.domain.onboarding.strategies import (
    OnboardingStrategy,
    OnboardingResult,
    WorkflowStep,
    UAEOnboardingStrategy,
    SaudiOnboardingStrategy,
    OffshoreOnboardingStrategy,
    WPSOnboardingStrategy,
    FreelancerOnboardingStrategy,
)

__all__ = [
    "OnboardingRegistry",
    "OnboardingStrategy",
    "OnboardingResult",
    "WorkflowStep",
    "UAEOnboardingStrategy",
    "SaudiOnboardingStrategy",
    "OffshoreOnboardingStrategy",
    "WPSOnboardingStrategy",
    "FreelancerOnboardingStrategy",
]
