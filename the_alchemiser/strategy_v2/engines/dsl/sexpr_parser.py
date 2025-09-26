#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

S-expression parser for DSL engine.

Parses Clojure-style S-expressions from .clj files into ASTNodeDTO structures
for evaluation by the DSL engine.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from the_alchemiser.shared.schemas.ast_node import ASTNodeDTO


class SexprParseError(Exception):
    """Error parsing S-expressions."""

    def __init__(self, message: str, position: int | None = None) -> None:
        """Initialize parse error.

        Args:
            message: Error message
            position: Character position where error occurred

        """
        self.position = position
        super().__init__(message)


class SexprParser:
    """Parser for Clojure-style S-expressions.

    Converts S-expression text into ASTNodeDTO tree structures for DSL evaluation.
    """

    def __init__(self) -> None:
        """Initialize parser."""
        # Token patterns
        self.token_patterns = [
            (r"\s+", "WHITESPACE"),  # Whitespace
            (r";[^\n]*", "COMMENT"),  # Comments
            (r",", "COMMA"),  # Commas (ignored in Clojure)
            (r"\(", "LPAREN"),  # Left parenthesis
            (r"\)", "RPAREN"),  # Right parenthesis
            (r"\[", "LBRACKET"),  # Left bracket
            (r"\]", "RBRACKET"),  # Right bracket
            (r"\{", "LBRACE"),  # Left brace
            (r"\}", "RBRACE"),  # Right brace
            # Strings with escaped quotes/backslashes
            (r'"(?:\\.|[^"\\])*"', "STRING"),
            (r"-?\d+\.\d+", "FLOAT"),  # Floating point numbers
            (r"-?\d+", "INTEGER"),  # Integers
            (r":[a-zA-Z_][a-zA-Z0-9_-]*", "KEYWORD"),  # Keywords
            (r"[a-zA-Z_><=!?+*/-][a-zA-Z0-9_><=!?+*/-]*", "SYMBOL"),  # Symbols
        ]

        # Compile patterns
        self.compiled_patterns = [
            (re.compile(pattern), token_type) for pattern, token_type in self.token_patterns
        ]

    def tokenize(self, text: str) -> list[tuple[str, str]]:
        """Tokenize S-expression text into (value, type) tuples."""
        tokens: list[tuple[str, str]] = []
        position = 0
        length = len(text)

        while position < length:
            position = self._process_character_at_position(text, position, tokens)

        return tokens

    def _process_character_at_position(
        self, text: str, position: int, tokens: list[tuple[str, str]]
    ) -> int:
        """Process a single character at the given position.
        
        Args:
            text: The text being tokenized
            position: Current position in the text
            tokens: List of tokens to append to
            
        Returns:
            The new position after processing the character
            
        Raises:
            SexprParseError: If an unexpected character is encountered

        """
        char = text[position]
        if char == '"':
            string_token, new_position = self._consume_string(text, position)
            tokens.append((string_token, "STRING"))
            return new_position

        matched = self._match_patterns(text, position, tokens)
        if matched:
            _, new_position = matched
            return new_position

        raise SexprParseError(f"Unexpected character: {char}", position)

    def _consume_string(self, text: str, start_pos: int) -> tuple[str, int]:
        """Consume a string token handling escape characters."""
        i = start_pos + 1
        length = len(text)
        while i < length:
            if text[i] == "\\":
                i += 2  # skip escaped character
                continue
            if text[i] == '"':
                return text[start_pos : i + 1], i + 1
            i += 1
        raise SexprParseError("Unterminated string literal", start_pos)

    def _match_patterns(
        self, text: str, pos: int, tokens: list[tuple[str, str]]
    ) -> tuple[str, int] | None:
        """Try to match any compiled pattern at current position."""
        for pattern, token_type in self.compiled_patterns:
            match = pattern.match(text, pos)
            if match:
                value = match.group()
                if token_type not in ("WHITESPACE", "COMMENT", "COMMA"):
                    tokens.append((value, token_type))
                return value, match.end()
        return None

    def parse(self, text: str) -> ASTNodeDTO:
        """Parse S-expression text into AST.

        Args:
            text: S-expression text to parse

        Returns:
            ASTNodeDTO representing the parsed AST

        Raises:
            SexprParseError: If parsing fails

        """
        tokens = self.tokenize(text)
        if not tokens:
            raise SexprParseError("Empty input")

        ast, remaining = self._parse_expression(tokens, 0)

        if remaining < len(tokens):
            remaining_tokens = tokens[remaining:]
            raise SexprParseError(f"Unexpected tokens after expression: {remaining_tokens}")

        return ast

    def _parse_expression(
        self, tokens: list[tuple[str, str]], index: int
    ) -> tuple[ASTNodeDTO, int]:
        """Parse a single expression.

        Args:
            tokens: List of tokens
            index: Current token index

        Returns:
            Tuple of (ASTNodeDTO, next_index)

        Raises:
            SexprParseError: If parsing fails

        """
        if index >= len(tokens):
            raise SexprParseError("Unexpected end of input")

        token_value, tok_type = tokens[index]

        if tok_type == "LPAREN":
            return self._parse_list(tokens, index + 1, "RPAREN")
        if tok_type == "LBRACKET":
            return self._parse_list(tokens, index + 1, "RBRACKET")
        if tok_type == "LBRACE":
            return self._parse_map(tokens, index + 1)
        return self._parse_atom(token_value, tok_type), index + 1

    def _parse_list(
        self, tokens: list[tuple[str, str]], index: int, end_token: str
    ) -> tuple[ASTNodeDTO, int]:
        """Parse a list expression.

        Args:
            tokens: List of tokens
            index: Current token index
            end_token: Expected end token type

        Returns:
            Tuple of (ASTNodeDTO, next_index)

        Raises:
            SexprParseError: If parsing fails

        """
        children: list[ASTNodeDTO] = []
        current_index = index

        while current_index < len(tokens):
            _token_value, tok_type = tokens[current_index]

            if tok_type == end_token:
                return ASTNodeDTO.list_node(children), current_index + 1

            child, current_index = self._parse_expression(tokens, current_index)
            children.append(child)

        raise SexprParseError(f"Missing closing {end_token}")

    def _parse_map(self, tokens: list[tuple[str, str]], index: int) -> tuple[ASTNodeDTO, int]:
        """Parse a map expression.

        Args:
            tokens: List of tokens
            index: Current token index

        Returns:
            Tuple of (ASTNodeDTO, next_index)

        Raises:
            SexprParseError: If parsing fails

        """
        children: list[ASTNodeDTO] = []
        current_index = index

        while current_index < len(tokens):
            _token_value, tok_type = tokens[current_index]

            if tok_type == "RBRACE":
                # Convert map to list node with metadata indicating it's a map
                return (
                    ASTNodeDTO.list_node(children, metadata={"node_subtype": "map"}),
                    current_index + 1,
                )

            # Parse key-value pairs
            key, current_index = self._parse_expression(tokens, current_index)
            children.append(key)

            if current_index >= len(tokens):
                raise SexprParseError("Missing value in map")

            value, current_index = self._parse_expression(tokens, current_index)
            children.append(value)

        raise SexprParseError("Missing closing }")

    def _parse_atom(self, token_value: str, tok_type: str) -> ASTNodeDTO:
        """Parse an atomic value.

        Args:
            token_value: Token value
            tok_type: Token type

        Returns:
            ASTNodeDTO representing the atom

        """
        if tok_type == "SYMBOL":
            return ASTNodeDTO.symbol(token_value)
        if tok_type == "STRING":
            # Remove quotes and unescape common sequences
            raw = token_value[1:-1]
            # Unescape \" and \\
            string_value = (
                raw.replace(r"\\\"", '"')
                .replace(r"\\n", "\n")
                .replace(r"\\t", "\t")
                .replace(r"\\r", "\r")
                .replace(r"\\\\", "\\")
            )
            return ASTNodeDTO.atom(string_value)
        if tok_type == "FLOAT" or tok_type == "INTEGER":
            return ASTNodeDTO.atom(Decimal(token_value))
        if tok_type == "KEYWORD":
            # Keywords are symbols with : prefix
            return ASTNodeDTO.symbol(token_value)
        raise SexprParseError(f"Unknown token type: {tok_type}")

    def parse_file(self, file_path: str) -> ASTNodeDTO:
        """Parse S-expression from file.

        Args:
            file_path: Path to .clj file

        Returns:
            ASTNodeDTO representing the parsed AST

        Raises:
            SexprParseError: If parsing fails
            FileNotFoundError: If file not found

        """
        try:
            with Path(file_path).open(encoding="utf-8") as file:
                content = file.read()
            return self.parse(content)
        except OSError as e:
            raise SexprParseError(f"Error reading file {file_path}: {e}") from e
