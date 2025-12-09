"""
Base entity class for all domain entities.
"""
from abc import ABC
from datetime import datetime
from typing import Optional


class Entity(ABC):
    """
    Base class for all domain entities.

    Domain entities represent core business objects with identity.
    They encapsulate business logic and validation rules.

    Attributes:
        id: Unique identifier (None for new entities)
        created_at: When the entity was created
        updated_at: When the entity was last updated
    """

    def __init__(
        self,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._id = id
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at

    @property
    def id(self) -> Optional[int]:
        """Entity's unique identifier."""
        return self._id

    @property
    def created_at(self) -> datetime:
        """When the entity was created."""
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        """When the entity was last updated."""
        return self._updated_at

    @property
    def is_new(self) -> bool:
        """Check if entity is new (not yet persisted)."""
        return self._id is None

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return False
        if self._id is None or other._id is None:
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash based on entity ID."""
        return hash(self._id) if self._id else hash(id(self))

    def __repr__(self) -> str:
        """String representation of entity."""
        return f"<{self.__class__.__name__}(id={self._id})>"
