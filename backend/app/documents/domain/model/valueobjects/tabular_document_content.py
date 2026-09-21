from dataclasses import dataclass

TableCell = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class TabularDocumentContent:
    columns: tuple[str, ...]
    rows: tuple[dict[str, TableCell], ...]
    metadata: dict[str, TableCell]

    def __post_init__(self) -> None:
        if not self.columns:
            raise ValueError("Tabular document requires at least one column")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Tabular document columns must be unique")
        if any(not column.strip() for column in self.columns):
            raise ValueError("Tabular document columns cannot be empty")
