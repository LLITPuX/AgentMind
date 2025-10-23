"""
Tests for ShortTermMemoryBuffer class

The STM buffer uses FalkorDB's built-in Redis-compatible list operations
to store recent observations before they are consolidated into LTM.
"""

import pytest
from datetime import datetime
from src.memory.stm import ShortTermMemoryBuffer, Observation


@pytest.mark.integration
class TestShortTermMemoryBuffer:
    """Tests for ShortTermMemoryBuffer basic operations"""
    
    def test_stm_buffer_can_be_created(self, falkordb_host, falkordb_port):
        """
        Test that STM buffer can be instantiated
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            max_size=10
        )
        assert buffer is not None
        assert buffer.max_size == 10
    
    def test_stm_buffer_can_add_observation(self, falkordb_host, falkordb_port):
        """
        Test that we can add an observation to STM
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_stm_add"
        )
        
        # Add observation
        obs = Observation(
            content="User said: Hello, how are you?",
            timestamp=datetime.now(),
            metadata={"source": "chat", "user_id": "test_user"}
        )
        
        buffer.add(obs)
        
        # Verify it was added
        assert buffer.size() == 1
        
        # Cleanup
        buffer.clear()
    
    def test_stm_buffer_can_get_all_observations(self, falkordb_host, falkordb_port):
        """
        Test that we can retrieve all observations from STM
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_stm_get_all"
        )
        
        # Add multiple observations
        obs1 = Observation(content="First observation", timestamp=datetime.now())
        obs2 = Observation(content="Second observation", timestamp=datetime.now())
        obs3 = Observation(content="Third observation", timestamp=datetime.now())
        
        buffer.add(obs1)
        buffer.add(obs2)
        buffer.add(obs3)
        
        # Get all observations
        observations = buffer.get_all()
        
        assert len(observations) == 3
        assert observations[0].content == "First observation"
        assert observations[1].content == "Second observation"
        assert observations[2].content == "Third observation"
        
        # Cleanup
        buffer.clear()
    
    def test_stm_buffer_respects_max_size(self, falkordb_host, falkordb_port):
        """
        Test that STM buffer respects max_size limit (FIFO)
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            max_size=3,
            buffer_key="test_stm_max_size"
        )
        
        # Add 5 observations (max_size is 3)
        for i in range(5):
            obs = Observation(
                content=f"Observation {i}",
                timestamp=datetime.now()
            )
            buffer.add(obs)
        
        # Should only have 3 most recent
        assert buffer.size() == 3
        
        observations = buffer.get_all()
        # Should have observations 2, 3, 4 (oldest removed)
        assert observations[0].content == "Observation 2"
        assert observations[1].content == "Observation 3"
        assert observations[2].content == "Observation 4"
        
        # Cleanup
        buffer.clear()
    
    def test_stm_buffer_can_get_recent_observations(self, falkordb_host, falkordb_port):
        """
        Test that we can get N most recent observations
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_stm_recent"
        )
        
        # Add 5 observations
        for i in range(5):
            obs = Observation(
                content=f"Observation {i}",
                timestamp=datetime.now()
            )
            buffer.add(obs)
        
        # Get 2 most recent
        recent = buffer.get_recent(n=2)
        
        assert len(recent) == 2
        assert recent[0].content == "Observation 3"
        assert recent[1].content == "Observation 4"
        
        # Cleanup
        buffer.clear()
    
    def test_stm_buffer_can_be_cleared(self, falkordb_host, falkordb_port):
        """
        Test that STM buffer can be cleared
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_stm_clear"
        )
        
        # Add observations
        for i in range(3):
            obs = Observation(content=f"Observation {i}", timestamp=datetime.now())
            buffer.add(obs)
        
        assert buffer.size() == 3
        
        # Clear
        buffer.clear()
        
        assert buffer.size() == 0
        assert buffer.get_all() == []
    
    def test_stm_buffer_preserves_observation_metadata(self, falkordb_host, falkordb_port):
        """
        Test that observation metadata is preserved
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_stm_metadata"
        )
        
        # Create observation with metadata
        metadata = {
            "source": "chat",
            "user_id": "user123",
            "confidence": 0.95,
            "tags": ["greeting", "casual"]
        }
        
        obs = Observation(
            content="Hello, how are you?",
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        buffer.add(obs)
        
        # Retrieve and check metadata
        retrieved = buffer.get_all()[0]
        assert retrieved.metadata["source"] == "chat"
        assert retrieved.metadata["user_id"] == "user123"
        assert retrieved.metadata["confidence"] == 0.95
        assert "greeting" in retrieved.metadata["tags"]
        
        # Cleanup
        buffer.clear()
    
    def test_stm_buffer_handles_empty_buffer(self, falkordb_host, falkordb_port):
        """
        Test that empty buffer operations don't crash
        """
        buffer = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_stm_empty"
        )
        
        # Operations on empty buffer
        assert buffer.size() == 0
        assert buffer.get_all() == []
        assert buffer.get_recent(n=5) == []
        
        # Clear empty buffer should not crash
        buffer.clear()
        assert buffer.size() == 0


@pytest.mark.unit
class TestObservation:
    """Tests for Observation data class"""
    
    def test_observation_can_be_created(self):
        """Test that Observation can be created"""
        obs = Observation(
            content="Test content",
            timestamp=datetime.now()
        )
        
        assert obs.content == "Test content"
        assert obs.timestamp is not None
        assert obs.metadata == {}
    
    def test_observation_accepts_metadata(self):
        """Test that Observation accepts metadata"""
        metadata = {"key": "value", "num": 42}
        obs = Observation(
            content="Test",
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        assert obs.metadata == metadata
    
    def test_observation_can_be_serialized(self):
        """Test that Observation can be converted to dict"""
        obs = Observation(
            content="Test content",
            timestamp=datetime(2024, 10, 23, 12, 0, 0),
            metadata={"source": "test"}
        )
        
        data = obs.to_dict()
        
        assert data["content"] == "Test content"
        assert "timestamp" in data
        assert data["metadata"]["source"] == "test"
    
    def test_observation_can_be_deserialized(self):
        """Test that Observation can be created from dict"""
        data = {
            "content": "Test content",
            "timestamp": "2024-10-23T12:00:00",
            "metadata": {"source": "test"}
        }
        
        obs = Observation.from_dict(data)
        
        assert obs.content == "Test content"
        assert obs.metadata["source"] == "test"

