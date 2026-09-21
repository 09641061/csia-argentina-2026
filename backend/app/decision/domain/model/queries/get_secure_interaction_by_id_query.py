from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSecureInteractionByIdQuery:
    interaction_id: int
    requested_by: str = "system"

    def __post_init__(self) -> None:
        if self.interaction_id <= 0:
            raise ValueError("Interaction ID must be a positive number")
        if not self.requested_by.strip():
            raise ValueError("Authenticated user is required")
