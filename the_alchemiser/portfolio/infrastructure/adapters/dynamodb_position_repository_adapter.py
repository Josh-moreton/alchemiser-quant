"""Business Unit: portfolio assessment & management | Status: current

DynamoDB position repository adapter implementing PositionRepositoryPort.
"""

import logging
from typing import Sequence

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.anti_corruption.persistence.position_mapper import PositionMapper
from the_alchemiser.portfolio.application.ports import PositionRepositoryPort
from the_alchemiser.portfolio.domain.entities.position import Position
from the_alchemiser.portfolio.domain.exceptions import ConcurrencyError
from the_alchemiser.shared_kernel.exceptions.base_exceptions import DataAccessError
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol

logger = logging.getLogger(__name__)

class DynamoDbPositionRepositoryAdapter(PositionRepositoryPort):
    """DynamoDB adapter for position persistence with optimistic locking."""
    
    def __init__(self, table_name: str, region_name: str = "us-east-1") -> None:
        """Initialize DynamoDB client and table reference.
        
        Args:
            table_name: DynamoDB table name for positions
            region_name: AWS region
        """
        dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self._table = dynamodb.Table(table_name)
        self._mapper = PositionMapper()
        self._logger = logger.bind(
            component="DynamoDbPositionRepositoryAdapter",
            table_name=table_name
        )
    
    def load_positions(self) -> Sequence[Position]:
        """Load all current positions from DynamoDB.
        
        Returns:
            Sequence of Position entities
            
        Raises:
            DataAccessError: DynamoDB failure
        """
        try:
            self._logger.info("Loading all positions from DynamoDB")
            
            response = self._table.scan()
            
            positions = []
            for item in response["Items"]:
                position = self._mapper.dynamodb_item_to_position(item)
                positions.append(position)
            
            # Handle pagination if needed
            while "LastEvaluatedKey" in response:
                response = self._table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                for item in response["Items"]:
                    position = self._mapper.dynamodb_item_to_position(item)
                    positions.append(position)
            
            self._logger.debug(
                "Successfully loaded positions",
                position_count=len(positions)
            )
            
            return positions
            
        except ClientError as e:
            self._logger.error(
                "DynamoDB error loading positions",
                error=str(e),
                error_code=e.response["Error"]["Code"]
            )
            raise DataAccessError(
                f"Failed to load positions from DynamoDB: {e}"
            ) from e
    
    def save_positions(self, positions: Sequence[Position]) -> None:
        """Atomically save all positions using DynamoDB transaction.
        
        Args:
            positions: Complete set of positions to persist
            
        Raises:
            DataAccessError: DynamoDB failure
            ConcurrencyError: Optimistic lock violation
        """
        if not positions:
            self._logger.debug("No positions to save, skipping")
            return
        
        try:
            # Build transaction items
            transact_items = []
            for position in positions:
                item = self._mapper.position_to_dynamodb_item(position)
                
                # Add optimistic locking condition if position has version
                if position.version > 1:
                    transact_items.append({
                        "Put": {
                            "TableName": self._table.table_name,
                            "Item": item,
                            "ConditionExpression": "version = :expected_version",
                            "ExpressionAttributeValues": {
                                ":expected_version": position.version - 1
                            }
                        }
                    })
                else:
                    # New position, ensure it doesn't already exist
                    transact_items.append({
                        "Put": {
                            "TableName": self._table.table_name,
                            "Item": item,
                            "ConditionExpression": "attribute_not_exists(symbol)"
                        }
                    })
            
            self._logger.info(
                "Saving positions to DynamoDB",
                position_count=len(positions)
            )
            
            # Execute transaction
            region = self._table.meta.client.meta.region_name
            dynamodb_client = boto3.client("dynamodb", region_name=region)
            dynamodb_client.transact_write_items(TransactItems=transact_items)
            
            self._logger.debug("Successfully saved positions")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            
            if error_code == "ConditionalCheckFailedException":
                self._logger.warning(
                    "Optimistic lock violation saving positions",
                    error=str(e)
                )
                raise ConcurrencyError(
                    "Position was modified by another process"
                ) from e
            else:
                self._logger.error(
                    "DynamoDB error saving positions",
                    error=str(e),
                    error_code=error_code
                )
                raise DataAccessError(
                    f"Failed to save positions to DynamoDB: {e}"
                ) from e
    
    def get_position(self, symbol: Symbol) -> Position | None:
        """Get specific position by symbol.
        
        Args:
            symbol: Symbol to lookup
            
        Returns:
            Position if found, None otherwise
            
        Raises:
            DataAccessError: DynamoDB failure
        """
        try:
            self._logger.debug(
                "Getting position by symbol",
                symbol=symbol.value
            )
            
            response = self._table.get_item(
                Key={"symbol": symbol.value}
            )
            
            if "Item" not in response:
                self._logger.debug(
                    "Position not found",
                    symbol=symbol.value
                )
                return None
            
            position = self._mapper.dynamodb_item_to_position(response["Item"])
            
            self._logger.debug(
                "Successfully retrieved position",
                symbol=symbol.value,
                quantity=str(position.quantity)
            )
            
            return position
            
        except ClientError as e:
            self._logger.error(
                "DynamoDB error getting position",
                symbol=symbol.value,
                error=str(e),
                error_code=e.response["Error"]["Code"]
            )
            raise DataAccessError(
                f"Failed to get position for {symbol.value}: {e}"
            ) from e