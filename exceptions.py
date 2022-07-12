class Not200ApiAnswer(Exception):
    """If status code is not 200."""

    pass


class ResponseNotType(Exception):
    """In case of non dictionary response."""

    pass


class ResponseIsEmpty(Exception):
    """In case of dictionary is empty."""

    pass

