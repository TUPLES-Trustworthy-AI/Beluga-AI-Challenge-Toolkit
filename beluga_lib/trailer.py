from beluga_lib.jigs import Jig


class Trailer:

    def __init__(self, name: str, jig: Jig | None = None) -> None:
        self.name = name
        self.jig = jig

    def __repr__(self) -> str:
        return self.name