from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MenuSettings:
    enabled: bool = True
    fg_color: Optional[str] = None
    text_color: Optional[str] = None
    hover_color: Optional[str] = None


@dataclass()
class HistorySettings:
    enabled: bool = True
    cooldown: int = 1500  # ms
    max: int = 100


@dataclass(frozen=True)
class NumberingSettings:
    enabled: bool = True
    color: Optional[str] = None
    justify: str = "left"
    padx: int = 30
    auto_padx: bool = True

__all__ = ["MenuSettings", "HistorySettings", "NumberingSettings"]
