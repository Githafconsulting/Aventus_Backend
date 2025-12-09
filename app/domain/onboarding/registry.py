"""
Onboarding Strategy Registry.

Provides dynamic registration and lookup of onboarding strategies.
Implements the Registry pattern for strategy management.
"""
from typing import Dict, Type, List, Optional
from app.domain.onboarding.strategies.base import OnboardingStrategy
from app.domain.contractor.value_objects import OnboardingRoute


class OnboardingRegistryMeta(type):
    """Metaclass to ensure singleton behavior for registry."""
    _instances: Dict[type, "OnboardingRegistry"] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class OnboardingRegistry(metaclass=OnboardingRegistryMeta):
    """
    Registry for onboarding strategies.

    Allows dynamic registration and lookup of strategies by route.
    Uses the Registry pattern to decouple strategy creation from usage.

    Usage:
        # Register a strategy
        @OnboardingRegistry.register(OnboardingRoute.UAE)
        class UAEOnboardingStrategy(OnboardingStrategy):
            ...

        # Get a strategy
        strategy = OnboardingRegistry.get("uae")

        # List available routes
        routes = OnboardingRegistry.available_routes()
    """

    _strategies: Dict[str, Type[OnboardingStrategy]] = {}
    _instances: Dict[str, OnboardingStrategy] = {}

    @classmethod
    def register(cls, route: OnboardingRoute):
        """
        Decorator to register a strategy class.

        Args:
            route: The OnboardingRoute this strategy handles

        Returns:
            Decorator function

        Usage:
            @OnboardingRegistry.register(OnboardingRoute.UAE)
            class UAEOnboardingStrategy(OnboardingStrategy):
                ...
        """
        def decorator(strategy_class: Type[OnboardingStrategy]):
            cls._strategies[route.value] = strategy_class
            return strategy_class
        return decorator

    @classmethod
    def register_class(cls, route: str, strategy_class: Type[OnboardingStrategy]) -> None:
        """
        Programmatically register a strategy class.

        Args:
            route: Route identifier string
            strategy_class: The strategy class to register
        """
        cls._strategies[route] = strategy_class

    @classmethod
    def get(cls, route: str) -> OnboardingStrategy:
        """
        Get a strategy instance for a route.

        Instances are cached for reuse.

        Args:
            route: Route identifier (e.g., "uae", "saudi")

        Returns:
            OnboardingStrategy instance

        Raises:
            KeyError: If route is not registered
        """
        if route not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise KeyError(
                f"No strategy registered for route: '{route}'. "
                f"Available routes: {available}"
            )

        # Return cached instance or create new one
        if route not in cls._instances:
            cls._instances[route] = cls._strategies[route]()

        return cls._instances[route]

    @classmethod
    def get_or_none(cls, route: str) -> Optional[OnboardingStrategy]:
        """
        Get a strategy instance, returning None if not found.

        Args:
            route: Route identifier

        Returns:
            OnboardingStrategy instance or None
        """
        try:
            return cls.get(route)
        except KeyError:
            return None

    @classmethod
    def available_routes(cls) -> List[str]:
        """
        Get list of all registered route identifiers.

        Returns:
            List of route strings
        """
        return list(cls._strategies.keys())

    @classmethod
    def is_registered(cls, route: str) -> bool:
        """
        Check if a route is registered.

        Args:
            route: Route identifier

        Returns:
            True if registered, False otherwise
        """
        return route in cls._strategies

    @classmethod
    def get_all_strategies(cls) -> Dict[str, OnboardingStrategy]:
        """
        Get all registered strategies as instances.

        Returns:
            Dict mapping route names to strategy instances
        """
        return {route: cls.get(route) for route in cls._strategies}

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered strategies.

        Primarily used for testing.
        """
        cls._strategies.clear()
        cls._instances.clear()

    @classmethod
    def get_route_info(cls) -> List[Dict[str, str]]:
        """
        Get info about all registered routes.

        Returns:
            List of dicts with route info (id, display_name, document_count)
        """
        info = []
        for route in cls._strategies:
            strategy = cls.get(route)
            info.append({
                "id": route,
                "display_name": strategy.display_name,
                "required_documents": len(strategy.get_required_documents()),
                "workflow_steps": len(strategy.get_workflow_steps()),
            })
        return info


def _register_all_strategies() -> None:
    """
    Register all built-in strategies.

    Called on module import to ensure strategies are available.
    """
    from app.domain.onboarding.strategies.uae import UAEOnboardingStrategy
    from app.domain.onboarding.strategies.saudi import SaudiOnboardingStrategy
    from app.domain.onboarding.strategies.offshore import OffshoreOnboardingStrategy
    from app.domain.onboarding.strategies.wps import WPSOnboardingStrategy
    from app.domain.onboarding.strategies.freelancer import FreelancerOnboardingStrategy

    OnboardingRegistry.register_class(OnboardingRoute.UAE.value, UAEOnboardingStrategy)
    OnboardingRegistry.register_class(OnboardingRoute.SAUDI.value, SaudiOnboardingStrategy)
    OnboardingRegistry.register_class(OnboardingRoute.OFFSHORE.value, OffshoreOnboardingStrategy)
    OnboardingRegistry.register_class(OnboardingRoute.WPS.value, WPSOnboardingStrategy)
    OnboardingRegistry.register_class(OnboardingRoute.FREELANCER.value, FreelancerOnboardingStrategy)


# Register strategies on import
_register_all_strategies()
