from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListDocumentsQuery:
    page: int = 1
    page_size: int = 20
    owner_user_id: int | None = None

    def __post_init__(self) -> None:
        if self.page <= 0:
            raise ValueError("Page must be greater than zero")
        if not 1 <= self.page_size <= 100:
            raise ValueError("Page size must be between 1 and 100")
        if self.owner_user_id is not None and self.owner_user_id <= 0:
            raise ValueError("Owner user ID must be a positive number")

