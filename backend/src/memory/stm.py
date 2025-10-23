"""
ShortTermMemoryBuffer - Manages short-term memory using Redis-like list operations

STM stores recent observations before they are consolidated into the
long-term knowledge graph. It uses a FIFO queue with a maximum size.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import redis
import logging

logger = logging.getLogger(__name__)


@dataclass
class Observation:
    """
    Represents a single observation in short-term memory.
    
    Attributes:
        content: The text content of the observation
        timestamp: When the observation was recorded
        metadata: Additional metadata (source, user_id, tags, etc.)
    """
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert observation to dictionary for serialization.
        
        Returns:
            dict: Serializable dictionary representation
        """
        data = asdict(self)
        # Convert datetime to ISO format string
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Observation":
        """
        Create Observation from dictionary.
        
        Args:
            data: Dictionary with observation data
        
        Returns:
            Observation: New Observation instance
        """
        # Convert timestamp string back to datetime
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """
        Convert observation to JSON string.
        
        Returns:
            str: JSON representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "Observation":
        """
        Create Observation from JSON string.
        
        Args:
            json_str: JSON string with observation data
        
        Returns:
            Observation: New Observation instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class ShortTermMemoryBuffer:
    """
    Manages short-term memory using Redis-compatible list operations.
    
    The STM buffer stores recent observations as a FIFO queue with a maximum size.
    Older observations are automatically removed when the buffer is full.
    
    Attributes:
        host: Redis/FalkorDB host
        port: Redis/FalkorDB port
        max_size: Maximum number of observations to keep (default: 100)
        buffer_key: Redis key for storing the buffer (default: "agentmind:stm")
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        max_size: int = 100,
        buffer_key: str = "agentmind:stm",
        db: int = 0
    ):
        """
        Initialize STM buffer with Redis connection.
        
        Args:
            host: Redis/FalkorDB host address
            port: Redis/FalkorDB port number
            max_size: Maximum number of observations to keep
            buffer_key: Redis key for the buffer
            db: Redis database number
        """
        self.host = host
        self.port = port
        self.max_size = max_size
        self.buffer_key = buffer_key
        
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"STM Buffer initialized at {host}:{port} with key '{buffer_key}'")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {host}:{port}: {e}")
            raise ConnectionError(f"Cannot connect to Redis: {e}")
    
    def add(self, observation: Observation) -> None:
        """
        Add an observation to the STM buffer.
        
        If the buffer is full, the oldest observation is removed (FIFO).
        
        Args:
            observation: Observation to add
        """
        try:
            # Serialize observation to JSON
            json_data = observation.to_json()
            
            # Add to Redis list (right push)
            self.redis_client.rpush(self.buffer_key, json_data)
            
            # Trim list to max_size (keep only the most recent)
            self.redis_client.ltrim(self.buffer_key, -self.max_size, -1)
            
            logger.debug(f"Added observation to STM: {observation.content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to add observation to STM: {e}")
            raise RuntimeError(f"Cannot add observation: {e}")
    
    def get_all(self) -> List[Observation]:
        """
        Get all observations from the STM buffer.
        
        Returns:
            list[Observation]: List of all observations (oldest to newest)
        """
        try:
            # Get all items from Redis list
            json_items = self.redis_client.lrange(self.buffer_key, 0, -1)
            
            # Deserialize to Observation objects
            observations = [Observation.from_json(item) for item in json_items]
            
            return observations
        except Exception as e:
            logger.error(f"Failed to get observations from STM: {e}")
            return []
    
    def get_recent(self, n: int) -> List[Observation]:
        """
        Get N most recent observations.
        
        Args:
            n: Number of recent observations to retrieve
        
        Returns:
            list[Observation]: List of N most recent observations
        """
        try:
            # Get last N items from Redis list
            json_items = self.redis_client.lrange(self.buffer_key, -n, -1)
            
            # Deserialize to Observation objects
            observations = [Observation.from_json(item) for item in json_items]
            
            return observations
        except Exception as e:
            logger.error(f"Failed to get recent observations from STM: {e}")
            return []
    
    def size(self) -> int:
        """
        Get the current number of observations in the buffer.
        
        Returns:
            int: Number of observations
        """
        try:
            return self.redis_client.llen(self.buffer_key)
        except Exception as e:
            logger.error(f"Failed to get STM buffer size: {e}")
            return 0
    
    def clear(self) -> None:
        """
        Clear all observations from the STM buffer.
        """
        try:
            self.redis_client.delete(self.buffer_key)
            logger.info(f"Cleared STM buffer: {self.buffer_key}")
        except Exception as e:
            logger.error(f"Failed to clear STM buffer: {e}")
            raise RuntimeError(f"Cannot clear buffer: {e}")
    
    def is_empty(self) -> bool:
        """
        Check if the buffer is empty.
        
        Returns:
            bool: True if empty, False otherwise
        """
        return self.size() == 0
    
    def is_full(self) -> bool:
        """
        Check if the buffer has reached max_size.
        
        Returns:
            bool: True if full, False otherwise
        """
        return self.size() >= self.max_size
    
    def __repr__(self) -> str:
        """String representation of STM buffer"""
        return (
            f"ShortTermMemoryBuffer("
            f"host='{self.host}', "
            f"port={self.port}, "
            f"max_size={self.max_size}, "
            f"current_size={self.size()})"
        )

