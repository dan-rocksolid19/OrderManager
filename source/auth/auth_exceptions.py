class AuthError(Exception):
    pass

class UserLockedError(AuthError):
    pass

class InvalidCredentials(AuthError):
    pass 

class UserInactiveError(AuthError):
    pass

class UserNotFoundError(AuthError):
    pass

class IncorrectPasswordError(AuthError):
    pass