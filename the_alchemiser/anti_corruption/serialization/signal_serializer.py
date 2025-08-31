"""Business Unit: utilities | Status: current

Anti-corruption layer for signal contract serialization.
"""

import json

from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1


class SignalSerializer:
    """Handles serialization of signal contracts for message publishing."""

    def signal_contract_to_json(self, signal: SignalContractV1) -> str:
        """Convert signal contract to JSON string.

        Args:
            signal: Signal contract to serialize

        Returns:
            JSON string representation

        Raises:
            ValueError: Serialization failure

        """
        try:
            # Use pydantic's json serialization for proper handling
            return signal.model_dump_json()
        except Exception as e:
            raise ValueError(f"Failed to serialize signal contract: {e}") from e

    def json_to_signal_contract(self, json_str: str) -> SignalContractV1:
        """Convert JSON string to signal contract.

        Args:
            json_str: JSON string to deserialize

        Returns:
            SignalContractV1 instance

        Raises:
            ValueError: Deserialization failure

        """
        try:
            data = json.loads(json_str)
            return SignalContractV1.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to deserialize signal contract: {e}") from e
