class CTkCodeBoxError(Exception):
    """Base exception for CTkCodeBoxPlus errors."""
    pass


class LanguageNotAvailableError(CTkCodeBoxError):
    """Raised when a requested language is not available or not recognized."""
    pass


class ThemeNotAvailableError(CTkCodeBoxError):
    """Raised when a requested theme name is invalid or not installed."""
    pass


class LexerError(CTkCodeBoxError):
    """Raised when a provided lexer is invalid or fails to tokenize input."""
    pass


class ConfigureBadType(CTkCodeBoxError):
    """Raised when a type of provided kwargs in configure() not the right one."""
    pass
