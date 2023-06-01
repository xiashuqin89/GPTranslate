class Error(Exception):
    pass


class LoginFailedError(Error):
    pass


class ActionFailed(Error):
    pass
