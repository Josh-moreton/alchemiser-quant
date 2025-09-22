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

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO


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
            (re.compile(pattern), token_type)
            for pattern, token_type in self.token_patterns
        ]

    def tokenize(self, text: str) -> list[tuple[str, str]]:
        """Tokenize S-expression text.

        Args:
            text: S-expression text to tokenize

        Returns:
            List of (token_value, token_type) tuples

        Raises:
            SexprParseError: If tokenization fails

        """
        tokens = []
        position = 0

        while position < len(text):
            matched = False

            # Fast-path for strings to correctly handle escapes
            if text[position] == '"':
                i = position + 1
                while i < len(text):
                    ch = text[i]
                    if ch == "\\":
                        i += 2  # Skip escaped character
                        continue
                    if ch == '"':
                        token_value = text[position : i + 1]
                        tokens.append((token_value, "STRING"))
                        position = i + 1
                        matched = True
                        break
                    i += 1
                if not matched:
                    raise SexprParseError("Unterminated string literal", position)
                continue

            for pattern, token_type in self.compiled_patterns:
                match = pattern.match(text, position)
                if match:
                    token_value = match.group()

                    # Skip whitespace, comments, and commas
                    if token_type not in ("WHITESPACE", "COMMENT", "COMMA"):
                        tokens.append((token_value, token_type))

                    position = match.end()
                    matched = True
                    break

            if not matched:
                raise SexprParseError(
                    f"Unexpected character: {text[position]}", position
                )

        return tokens

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
            raise SexprParseError(
                f"Unexpected tokens after expression: {remaining_tokens}"
            )

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

    def _parse_map(
        self, tokens: list[tuple[str, str]], index: int
    ) -> tuple[ASTNodeDTO, int]:
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
