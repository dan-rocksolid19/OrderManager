current_user = None


def login(user):
    global current_user
    current_user = user


def logout():
    global current_user
    current_user = None


def login_required(func):
    def wrapper(*args, **kwargs):
        if current_user is None:
            raise PermissionError("login required")
        return func(*args, **kwargs)
    return wrapper 