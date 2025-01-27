
class InvalidResultDuringValidation(Exception):
    def __init__(self, *args, message):
        super().__init__(*args, message)
        self.message = message