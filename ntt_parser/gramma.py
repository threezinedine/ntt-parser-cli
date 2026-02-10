class Gramma:
    @staticmethod
    def parse(gramma_str: str) -> "Gramma":
        gramma_part = (
            gramma_str.split("/start-gramma")[1].split("/end-gramma")[0].strip()
        )
        return Gramma(gramma_part)

    def __init__(self, gramma_part: str) -> None:
        self._terminals: set[str] = set()
        self._non_terminals: set[str] = set()
        self._productions: list[tuple[str, list[str]]] = []
        self._start_non_terminal: str = ""
        self._parse_gramma_part(gramma_part)

    def _parse_gramma_part(self, gramma_part: str) -> None:
        current_cursor = 0

        while True:
            next_non_terminal = gramma_part.find(":", current_cursor)
            if next_non_terminal == -1:
                return

            left_side = gramma_part[current_cursor:next_non_terminal].strip()
            self._non_terminals.add(left_side)
            if not self._start_non_terminal:
                self._start_non_terminal = left_side
            current_cursor = next_non_terminal + 1

            production_end = gramma_part.find(";", current_cursor)

            if production_end == -1:
                raise ValueError("Production must end with ';'")

            production_str = gramma_part[current_cursor:production_end].strip()
            current_cursor = production_end + 1

            current_production_cursor = 0

            while True:
                current_production_end = production_str.find(
                    "|", current_production_cursor
                )

                if current_production_end == -1:
                    current_production_str = production_str[current_production_cursor:]
                else:
                    current_production_str = production_str[
                        current_production_cursor:current_production_end
                    ]

                current_production_str = current_production_str.strip()
                if current_production_str[-1] == "\n":
                    current_production_str = current_production_str[:-1].strip()

                current_production_cursor = current_production_end + 1

                production_symbols = current_production_str.split(" ")

                production_right_side: list[str] = []

                for symbol in production_symbols:
                    if symbol == "":
                        continue

                    if symbol.startswith('"') and symbol.endswith('"'):
                        self._terminals.add(symbol[1:-1])
                        production_right_side.append(symbol[1:-1])
                    else:
                        self._non_terminals.add(symbol)
                        production_right_side.append(symbol)

                self._productions.append(
                    (
                        left_side,
                        production_right_side,
                    )
                )

                if current_production_end == -1:
                    break

    @property
    def Terminals(self) -> list[str]:
        return list(self._terminals)

    @property
    def NonTerminals(self) -> list[str]:
        return list(self._non_terminals)

    @property
    def Productions(self) -> list[tuple[str, list[str]]]:
        return self._productions

    @property
    def StartNonTerminal(self) -> str:
        if not self._non_terminals:
            raise ValueError("No non-terminals defined in the gramma")

        return self._start_non_terminal
