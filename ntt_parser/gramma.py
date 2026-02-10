class Gramma:
    @staticmethod
    def parse(gramma_str: str) -> "Gramma":
        macro_part = Gramma.parser_section(gramma_str, "macro")
        if macro_part is None:
            macros = {}
        else:
            macros = Gramma.macro_parse(macro_part)

        gramma_part = Gramma.parser_section(gramma_str, "gramma")
        assert gramma_part is not None, "No /start-gramma ... /end-gramma section found"

        for macro_name, macro_value in macros.items():
            gramma_part = gramma_part.replace(macro_name, macro_value)

        return Gramma(gramma_part)

    @staticmethod
    def parser_section(content: str, section_header: str) -> str | None:
        try:
            section_content = (
                content.split(f"/start-{section_header}")[1]
                .split(f"/end-{section_header}")[0]
                .strip()
            )
            return section_content
        except IndexError:
            return None

    @staticmethod
    def macro_parse(macro_str: str) -> dict[str, str]:
        macro_str = macro_str.strip()
        macro_strs = macro_str.split("\n")
        macros: dict[str, str] = {}

        for line in macro_strs:
            line = line.strip()
            if line == "":
                continue

            if ":" not in line:
                raise ValueError(f"Invalid macro definition: {line}")

            macro_name, macro_value = line.split(":", 1)
            macros[macro_name.strip()] = macro_value.strip()

        return macros

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

                current_production_str, _ = Gramma._get_return_part(
                    current_production_str
                )

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

    @staticmethod
    def _get_return_part(part: str) -> tuple[str, str | None]:
        part = part.strip()

        left_bracket_index = part.find("{")
        right_bracket_index = part.find("}")

        if left_bracket_index == -1 or right_bracket_index == -1:
            return part, None

        if right_bracket_index < left_bracket_index:
            raise ValueError("Invalid return part format")

        return (
            part[:left_bracket_index].strip(),
            part[left_bracket_index + 1 : right_bracket_index].strip(),
        )

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
