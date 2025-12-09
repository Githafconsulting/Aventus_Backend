# Repository interfaces (ABCs)
from app.repositories.interfaces.base import IRepository, IReadOnlyRepository
from app.repositories.interfaces.contractor_repo import IContractorRepository
from app.repositories.interfaces.client_repo import IClientRepository

__all__ = [
    "IRepository",
    "IReadOnlyRepository",
    "IContractorRepository",
    "IClientRepository",
]
