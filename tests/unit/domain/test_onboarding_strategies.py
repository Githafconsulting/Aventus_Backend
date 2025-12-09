"""
Unit tests for onboarding strategies.
"""
import pytest
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.onboarding.registry import OnboardingRegistry
from app.domain.onboarding.strategies.base import OnboardingStrategy


class TestOnboardingRegistry:
    """Tests for OnboardingRegistry."""

    def test_registry_has_all_routes(self):
        """Test that all routes are registered."""
        expected_routes = ["wps", "freelancer", "uae", "saudi", "offshore"]
        available = OnboardingRegistry.available_routes()
        for route in expected_routes:
            assert route in available

    def test_get_strategy_uae(self):
        """Test getting UAE strategy."""
        strategy = OnboardingRegistry.get("uae")
        assert strategy is not None
        assert strategy.route_name == "uae"

    def test_get_strategy_saudi(self):
        """Test getting Saudi strategy."""
        strategy = OnboardingRegistry.get("saudi")
        assert strategy is not None
        assert strategy.route_name == "saudi"

    def test_get_strategy_wps(self):
        """Test getting WPS strategy."""
        strategy = OnboardingRegistry.get("wps")
        assert strategy is not None
        assert strategy.route_name == "wps"

    def test_get_strategy_freelancer(self):
        """Test getting Freelancer strategy."""
        strategy = OnboardingRegistry.get("freelancer")
        assert strategy is not None
        assert strategy.route_name == "freelancer"

    def test_get_strategy_offshore(self):
        """Test getting Offshore strategy."""
        strategy = OnboardingRegistry.get("offshore")
        assert strategy is not None
        assert strategy.route_name == "offshore"

    def test_get_invalid_strategy_raises(self):
        """Test getting invalid strategy raises error."""
        with pytest.raises(KeyError):
            OnboardingRegistry.get("invalid_route")

    def test_get_or_none_returns_none(self):
        """Test get_or_none returns None for invalid route."""
        result = OnboardingRegistry.get_or_none("invalid_route")
        assert result is None

    def test_is_registered(self):
        """Test is_registered check."""
        assert OnboardingRegistry.is_registered("uae") is True
        assert OnboardingRegistry.is_registered("invalid") is False


class TestUAEStrategy:
    """Tests for UAE onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("uae")

    def test_route_name(self, strategy):
        """Test route name."""
        assert strategy.route_name == "uae"

    def test_display_name(self, strategy):
        """Test display name."""
        assert "UAE" in strategy.display_name

    def test_get_required_documents(self, strategy):
        """Test required documents list."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert "passport" in [d.lower() for d in docs] or any("passport" in d.lower() for d in docs)

    def test_get_workflow_steps(self, strategy):
        """Test workflow steps."""
        steps = strategy.get_workflow_steps()
        assert isinstance(steps, list)
        assert len(steps) > 0

    def test_get_next_status(self, strategy):
        """Test getting next status."""
        next_status = strategy.get_next_status(ContractorStatus.DOCUMENTS_UPLOADED)
        assert next_status is not None
        assert isinstance(next_status, ContractorStatus)


class TestSaudiStrategy:
    """Tests for Saudi onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("saudi")

    def test_route_name(self, strategy):
        """Test route name."""
        assert strategy.route_name == "saudi"

    def test_display_name(self, strategy):
        """Test display name."""
        assert "Saudi" in strategy.display_name or "SAUDI" in strategy.display_name.upper()

    def test_get_required_documents(self, strategy):
        """Test required documents list."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)
        assert len(docs) > 0


class TestWPSStrategy:
    """Tests for WPS onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("wps")

    def test_route_name(self, strategy):
        """Test route name."""
        assert strategy.route_name == "wps"

    def test_display_name(self, strategy):
        """Test display name."""
        assert "WPS" in strategy.display_name.upper()

    def test_get_required_documents(self, strategy):
        """Test required documents list."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)


class TestFreelancerStrategy:
    """Tests for Freelancer onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("freelancer")

    def test_route_name(self, strategy):
        """Test route name."""
        assert strategy.route_name == "freelancer"

    def test_display_name(self, strategy):
        """Test display name."""
        assert "Freelancer" in strategy.display_name or "freelancer" in strategy.display_name.lower()

    def test_get_required_documents(self, strategy):
        """Test required documents list."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)
