class UniqueConstraintException(Exception):
    def __init__(self, message, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message
