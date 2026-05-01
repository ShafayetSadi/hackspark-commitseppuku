class AuthServiceError(Exception):
    """Base application error for auth-service use cases."""


class DuplicateEmailError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass
