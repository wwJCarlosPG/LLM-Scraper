
class InvalidResultAfterValidation(Exception):
    def __init__(self, *args, last_explanation: str):
        super().__init__(*args, last_explanation)

        self.last_explanation = last_explanation