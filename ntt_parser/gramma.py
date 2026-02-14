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
        lexma_part = Gramma.parser_section(gramma_str, "lexma")

        if lexma_part is None:
            lexicals: dict[str, str] = {}
        else:
            lexicals: dict[str, str] = Gramma.lexical_parse(lexma_part)

        macro_part = Gramma.parser_section(gramma_str, "macro")
        if macro_part is None:
            macros = {}
        else:
            macros = Gramma.macro_parse(macro_part)

        gramma_part = Gramma.parser_section(gramma_str, "gramma")
        assert gramma_part is not None, "No /start-gramma ... /end-gramma section found"

        for macro_name, macro_value in macros.items():
            gramma_part = gramma_part.replace(macro_name, macro_value)

        return Gramma(gramma_part, lexicals)

    @staticmethod
    def lexical_parse(lexma_str: str) -> dict[str, str]:
        lexma_str = lexma_str.strip()
        lexma_strs = lexma_str.split("\n")
        lexicals: dict[str, str] = {}

        for line in lexma_strs:
            line = line.strip()
            if line == "":
                continue

            if ":" not in line:
                raise ValueError(f"Invalid lexical definition: {line}")

            lexical_name, lexical_value = line.split(":", 1)
            lexicals[lexical_name.strip()] = lexical_value.strip()

        return lexicals

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

    def __init__(self, gramma_part: str, lexicals: dict[str, str]) -> None:
        self._terminals: set[str] = set()
        self._non_terminals: set[str] = set()
        self._productions: list[tuple[str, list[str], str | None]] = []
        self._start_non_terminal: str = ""
        self._first_set: dict[str, set[str]] = {}
        self._follow_set: dict[str, set[str]] = {}
        self._lexicals: dict[str, str] = lexicals

        tokens = self._lexical_analysis(gramma_part)
        self._parse_gramma_part(tokens)
        self._parse_first_set()
        self._parse_follow_set()

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
                        terminal_value = part
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

    @property
    def FirstSet(self) -> list[tuple[str, list[str]]]:
        return [(k, list(v)) for k, v in self._first_set.items()]

    @property
    def FollowSet(self) -> list[tuple[str, list[str]]]:
        return [(k, list(v)) for k, v in self._follow_set.items()]

    def _parse_first_set(self) -> None:
        for symbol in self._non_terminals:
            self._parse_non_terminal_first_set(symbol)

    def _parse_non_terminal_first_set(self, non_terminal: str):
        if non_terminal not in self._first_set:
            self._first_set[non_terminal] = set()
        else:
            return

        productions = [p for p in self._productions if p[0] == non_terminal]

        assert (
            len(productions) > 0
        ), f"No productions found for non-terminal '{non_terminal}'"

        for production in productions:
            dependencies = production[1]

            dep_index = 0

            while dep_index < len(dependencies):
                if dependencies[dep_index] in self._terminals:
                    self._first_set[non_terminal].add(dependencies[dep_index])
                    break
                elif dependencies[dep_index] in self._first_set:
                    self._first_set[non_terminal].update(
                        self._first_set[dependencies[dep_index]]
                    )
                    if "" in self._first_set[dependencies[dep_index]]:
                        dep_index += 1
                        continue
                    else:
                        break
                elif dependencies[dep_index] in self._lexicals:
                    self._first_set[non_terminal].add(dependencies[dep_index])
                    break

                self._parse_non_terminal_first_set(dependencies[dep_index])
                self._first_set[non_terminal].update(
                    self._first_set[dependencies[dep_index]]
                )
                if '""' in dependencies[dep_index]:
                    dep_index += 1
                else:
                    break

    def _parse_follow_set(self) -> None:
        self._parse_non_terminal_follow_set(self._start_non_terminal)

        for non_terminal in self._non_terminals:
            self._parse_non_terminal_follow_set(non_terminal)

    def _get_first_set(self, symbols: list[str]) -> set[str]:
        first_set: set[str] = set()

        index = 0

        while index < len(symbols):
            symbol = symbols[index]

            if symbol in self._terminals:
                if symbol == '""':
                    index += 1
                    continue

                first_set.add(symbol)
                break

            if symbol in self._first_set:
                first_set.update(self._first_set[symbol])
                if '""' in self._first_set[symbol]:
                    index += 1
                    continue
                else:
                    break

        return first_set

    def _parse_non_terminal_follow_set(self, non_terminal: str) -> None:
        if non_terminal not in self._follow_set:
            self._follow_set[non_terminal] = set()
        else:
            return

        if non_terminal == self._start_non_terminal:
            self._follow_set[non_terminal].add("$")  # End of input marker

        contained_in_productions = [
            p for p in self._productions if non_terminal in p[1]
        ]

        for production in contained_in_productions:
            rhs = production[1]
            index = rhs.index(non_terminal)

            if index != len(rhs) - 1:
                first_set = self._get_first_set(rhs[index + 1 :])
                self._follow_set[non_terminal].update(first_set)

                if '""' in first_set:
                    self._parse_non_terminal_follow_set(production[0])
                    self._follow_set[non_terminal].update(
                        self._follow_set[production[0]]
                    )
            else:
                if production[0] != non_terminal:
                    self._parse_non_terminal_follow_set(production[0])
                    self._follow_set[non_terminal].update(
                        self._follow_set[production[0]]
                    )

        if '""' in self._follow_set.get(non_terminal, set()):
            self._follow_set[non_terminal].remove('""')
