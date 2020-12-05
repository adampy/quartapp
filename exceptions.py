class UsernameTaken(Exception):
    """Exception raised if username given is taken."""
    pass

class DateTimeParserError(Exception):
    """Exception raised when a datetime given is not parsable."""
    pass