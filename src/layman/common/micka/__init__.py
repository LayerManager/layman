from dataclasses import dataclass


@dataclass(frozen=True)
class MickaIds:
    id: str  # # pylint: disable=invalid-name

    def __init__(self, *, uuid: str):
        object.__setattr__(self, 'id', f"m-{uuid}")
