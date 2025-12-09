"""
Base repository implementation.

Provides common CRUD operations for all entities using SQLAlchemy.
"""
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.repositories.interfaces.base import IRepository

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType], IRepository[ModelType]):
    """
    Base repository implementation with common CRUD operations.

    All entity-specific repositories inherit from this class.
    Provides default implementations that can be overridden.

    Usage:
        class ContractorRepository(BaseRepository[Contractor]):
            def __init__(self, db: Session):
                super().__init__(Contractor, db)
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    async def get(self, id: int) -> Optional[ModelType]:
        """Get entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Get all entities with pagination."""
        return (
            self.db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new entity."""
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[ModelType]:
        """Update an entity by ID."""
        entity = await self.get(id)
        if entity:
            for field, value in data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            self.db.commit()
            self.db.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        entity = await self.get(id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if entity exists."""
        return self.db.query(
            self.db.query(self.model).filter(self.model.id == id).exists()
        ).scalar()

    async def count(self, **filters) -> int:
        """Count entities matching filters."""
        query = self.db.query(func.count(self.model.id))
        if filters:
            query = query.filter_by(**filters)
        return query.scalar()

    async def filter_by(self, **kwargs) -> List[ModelType]:
        """
        Filter entities by field values.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            List of matching entities
        """
        return self.db.query(self.model).filter_by(**kwargs).all()

    async def first_by(self, **kwargs) -> Optional[ModelType]:
        """
        Get first entity matching filters.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            First matching entity or None
        """
        return self.db.query(self.model).filter_by(**kwargs).first()

    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple entities.

        Args:
            items: List of entity data dicts

        Returns:
            List of created entities
        """
        entities = [self.model(**item) for item in items]
        self.db.add_all(entities)
        self.db.commit()
        for entity in entities:
            self.db.refresh(entity)
        return entities

    async def bulk_update(self, ids: List[int], data: Dict[str, Any]) -> int:
        """
        Update multiple entities.

        Args:
            ids: List of entity IDs
            data: Fields to update

        Returns:
            Number of updated entities
        """
        result = (
            self.db.query(self.model)
            .filter(self.model.id.in_(ids))
            .update(data, synchronize_session=False)
        )
        self.db.commit()
        return result

    async def bulk_delete(self, ids: List[int]) -> int:
        """
        Delete multiple entities.

        Args:
            ids: List of entity IDs

        Returns:
            Number of deleted entities
        """
        result = (
            self.db.query(self.model)
            .filter(self.model.id.in_(ids))
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return result
