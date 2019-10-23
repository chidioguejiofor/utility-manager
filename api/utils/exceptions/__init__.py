class UniqueConstraintException(Exception):
    def __init__(self, message, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message


class MessageOnlyResponseException(Exception):
    def __init__(self, message, status_code=400, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.status_code = status_code


class ModelOperationException(Exception):
    def __init__(self, message, api_message, status_code=400, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.status_code = status_code
        self.api_message = api_message
