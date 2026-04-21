from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AutomationRequest:
    target_tier: str
    additional_runs: int


@dataclass(frozen=True, slots=True)
class TemplateMatch:
    label: str
    confidence: float
    left: int
    top: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)
