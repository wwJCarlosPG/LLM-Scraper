
class InvalidResultDuringValidation(Exception):
    """
    Exception raised when an invalid result is encountered during the validation process.

    This exception typically indicates that the validation logic has failed to
    produce a valid or expected outcome.

    Attributes:
        message (str): A descriptive message explaining the reason for the exception.
    """
    def __init__(self, *args, message):
        """
        Initializes an InvalidResultDuringValidation exception.

        Args:
            message (str): A descriptive message explaining the reason for the exception.
        """
        super().__init__(*args, message)
        self.message = message

class InvalidValidationFormat(Exception):
    """
    Exception raised when the validation format is invalid.

    This exception indicates that the input data or the expected format for
    validation is not in the correct format, preventing the validation
    process from proceeding correctly.

    Attributes:
        message (str): A descriptive message explaining the reason for the exception.
    """
    def __init__(self, *args, message):
        """
        Initializes an InvalidValidationFormat exception.

        Args:
            message (str): A descriptive message explaining the reason for the exception.
        """
        super().__init__(*args, message)
        self.message = message
