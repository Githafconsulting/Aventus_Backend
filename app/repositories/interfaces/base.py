"""
Base repository interface.

Defines the contract for all repository implementations.
Uses Generic types for type safety.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any, Dict

# Type variable for entity types
T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Abstract base repository interface.

    All entity-specific repositories must implement this interface.
    This abstraction allows for:
    - Easy mocking in tests
    - Swapping implementations (SQL → NoSQL, etc.)
    - Consistent API across all repositories

    Type parameter T represents the entity type.
    """

    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        """
        Get an entity by its ID.

        Args:
            id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[T]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data: Entity data as dictionary

        Returns:
            Created entity
        """
        pass

    @abstractmethod
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            id: Entity ID
            data: Fields to update

        Returns:
            Updated entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, id: int) -> bool:
        """
        Check if an entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def count(self, **filters) -> int:
        """
        Count entities matching filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            Count of matching entities
        """
        pass


class IReadOnlyRepository(ABC, Generic[T]):
    """
    Read-only repository interface.

    For entities that should not be modified through this interface.
    """

    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def exists(self, id: int) -> bool:
        """Check if entity exists."""
        pass

    @abstractmethod
    async def count(self, **filters) -> int:
        """Count entities matching filters."""
        pass
