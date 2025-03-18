from dataclasses import dataclass


@dataclass(frozen=True)
class MickaIds:
    metadata_uuid: str

    def __init__(self, *, uuid: str):
        object.__setattr__(self, 'metadata_uuid', f"m-{uuid}")
