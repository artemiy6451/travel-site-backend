"""File with basic exceptions."""


class AppError(Exception):
    """Base exception."""


class RepositoryError(AppError):
    """Repository exception."""


class ServiceError(AppError):
    """Service exception."""


class ApiError(AppError):
    """Api excection."""
