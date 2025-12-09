# Onboarding strategies
from app.domain.onboarding.strategies.base import (
    OnboardingStrategy,
    OnboardingResult,
    WorkflowStep,
)
from app.domain.onboarding.strategies.uae import UAEOnboardingStrategy
from app.domain.onboarding.strategies.saudi import SaudiOnboardingStrategy
from app.domain.onboarding.strategies.offshore import OffshoreOnboardingStrategy
from app.domain.onboarding.strategies.wps import WPSOnboardingStrategy
from app.domain.onboarding.strategies.freelancer import FreelancerOnboardingStrategy

__all__ = [
    "OnboardingStrategy",
    "OnboardingResult",
    "WorkflowStep",
    "UAEOnboardingStrategy",
    "SaudiOnboardingStrategy",
    "OffshoreOnboardingStrategy",
    "WPSOnboardingStrategy",
    "FreelancerOnboardingStrategy",
]
