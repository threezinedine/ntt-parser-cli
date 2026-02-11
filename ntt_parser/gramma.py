from dataclasses import dataclass
from enum import Enum, auto


class GrammaToken(Enum):
    LEFT_SIDE = auto()
    RIGHT_SIDE = auto()
    RETURN = auto()
    COLON = auto()
    SEMICOLON = auto()


@dataclass
class Token:
    type: GrammaToken
    value: str


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
        self._productions: list[tuple[str, list[str], str | None]] = []
        self._start_non_terminal: str = ""
        tokens = self._lexical_analysis(gramma_part)
        self._parse_gramma_part(tokens)

    def _lexical_analysis(self, gramma_part: str) -> list[Token]:
        cursor = 0
        token_hold_cursor = 0
        tokens: list[Token] = []

        while cursor < len(gramma_part):
            current_char = gramma_part[cursor]

            if current_char == ":":
                tokens.append(
                    Token(
                        GrammaToken.LEFT_SIDE,
                        gramma_part[token_hold_cursor:cursor].strip(),
                    )
                )
                tokens.append(Token(GrammaToken.COLON, ":"))
                cursor += 1
                token_hold_cursor = cursor
            elif current_char == "{":
                return_part, _, next_cursor = Gramma._extract_block(gramma_part, cursor)
                tokens.append(
                    Token(
                        GrammaToken.RIGHT_SIDE,
                        gramma_part[token_hold_cursor:cursor].strip(),
                    )
                )
                tokens.append(Token(GrammaToken.RETURN, return_part))
                cursor = next_cursor
                token_hold_cursor = cursor
            elif current_char == ";":
                if token_hold_cursor != cursor:
                    tokens.append(
                        Token(
                            GrammaToken.RIGHT_SIDE,
                            gramma_part[token_hold_cursor:cursor].strip(),
                        )
                    )

                tokens.append(Token(GrammaToken.SEMICOLON, ";"))
                cursor += 1
                token_hold_cursor = cursor
            elif current_char == "|":
                if token_hold_cursor != cursor:
                    tokens.append(
                        Token(
                            GrammaToken.RIGHT_SIDE,
                            gramma_part[token_hold_cursor:cursor].strip(),
                        )
                    )

                cursor += 1
                token_hold_cursor = cursor
            else:
                cursor += 1

        tokens = list(filter(lambda t: t.value != "", tokens))

        return tokens

    def _parse_gramma_part(self, tokens: list[Token]) -> None:
        assert tokens[-1].type == GrammaToken.SEMICOLON, "Gramma must end with ';'"
        cursor = 0
        current_left_side = tokens[cursor]
        assert (
            current_left_side.type == GrammaToken.LEFT_SIDE
        ), "Expected left side non-terminal"
        self._start_non_terminal = current_left_side.value

        while True:
            current_left_side = tokens[cursor]
            assert (
                current_left_side.type == GrammaToken.LEFT_SIDE
            ), "Expected left side non-terminal"

            next_semicolon_index = self._find_index(tokens, cursor, GrammaToken.COLON)
            assert next_semicolon_index != -1, "Expected ';' in gramma"

            self._non_terminals.add(current_left_side.value)

            current_production_index = cursor + 2

            while True:
                current_production = tokens[current_production_index]
                assert (
                    current_production.type == GrammaToken.RIGHT_SIDE
                ), f"Expected right side production but found {current_production.type} at {current_production_index}"

                production_parts = current_production.value.split(" ")
                partion_parts: list[str] = []
                for part in production_parts:
                    part = part.strip()
                    if part.startswith('"') and part.endswith('"'):
                        terminal_value = part[1:-1]
                        self._terminals.add(terminal_value)
                        partion_parts.append(terminal_value)
                    else:
                        partion_parts.append(part)

                if tokens[current_production_index + 1].type == GrammaToken.RETURN:
                    return_action = tokens[current_production_index + 1].value
                    self._productions.append(
                        (current_left_side.value, partion_parts, return_action)
                    )
                    current_production_index += 2
                else:
                    self._productions.append(
                        (current_left_side.value, partion_parts, None)
                    )
                    current_production_index += 1

                if tokens[current_production_index].type == GrammaToken.RIGHT_SIDE:
                    continue

                if tokens[current_production_index].type == GrammaToken.SEMICOLON:
                    cursor = current_production_index + 1
                    break

            if cursor >= len(tokens):
                break

    def _find_index(
        self,
        tokens: list[Token],
        start_index: int,
        token_type: GrammaToken,
    ) -> int:
        cursor = start_index

        while cursor < len(tokens):
            if tokens[cursor].type == token_type:
                return cursor

            cursor += 1

        return -1

    @staticmethod
    def _extract_block(content: str, start_index: int) -> tuple[str, str, int]:
        assert content[start_index] == "{", "Block must start with '{'"
        braceStack = 1
        cursor = start_index + 1

        while braceStack != 0:
            if content[cursor] == "{":
                braceStack += 1
            elif content[cursor] == "}":
                braceStack -= 1

            cursor += 1

        next_cursor = cursor

        if cursor >= len(content):
            next_cursor = -1

        return (
            content[start_index + 1 : cursor - 1].strip(),
            content[cursor - 1 :],
            next_cursor,
        )

    @property
    def Terminals(self) -> list[str]:
        return list(self._terminals)

    @property
    def NonTerminals(self) -> list[str]:
        return list(self._non_terminals)

    @property
    def Productions(self) -> list[tuple[str, list[str], str | None]]:
        return self._productions

    @property
    def StartNonTerminal(self) -> str:
        if not self._non_terminals:
            raise ValueError("No non-terminals defined in the gramma")

        return self._start_non_terminal
