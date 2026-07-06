class LibraryError(Exception):
    """Base exception for ShelfWise domain errors."""


class BookUnavailable(LibraryError):
    pass


class MemberNotFound(LibraryError):
    pass


class BookNotFound(LibraryError):
    pass


class LoanNotFound(LibraryError):
    pass


class LoanAlreadyReturned(LibraryError):
    pass