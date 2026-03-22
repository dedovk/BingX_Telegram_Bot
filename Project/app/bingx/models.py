from dataclasses import dataclass


@dataclass
class SpotBalance:
    asset: str  # token name
    free: float  # free balance
    locked: float  # balance in orders

    @property
    def total(self) -> float:
        return self.free + self.locked
