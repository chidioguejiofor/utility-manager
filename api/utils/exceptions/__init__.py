class ModelsNotOfSameTypeException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__('All the models must be of the same type', *args,
                         **kwargs)
