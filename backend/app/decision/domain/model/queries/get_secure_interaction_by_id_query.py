from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSecureInteractionByIdQuery:
    interaction_id: int

    def __post_init__(self) -> None:
        if self.interaction_id <= 0:
            raise ValueError("Interaction ID must be a positive number")
