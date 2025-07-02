"""
Pydantic models for Lamy's data structures.
Defines models for the 3-layer memory system and other structured data.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MemoryType(str, Enum):
    """Types of memories in the system."""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class WorkingMemoryItem(BaseModel):
    """
    Represents a single item in working memory (Layer 1).
    Recent chat messages that are kept in the context window.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    user_id: str = Field(..., description="Discord user ID")
    user_name: str = Field(..., description="Discord username")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    channel_id: str = Field(..., description="Discord channel ID")
    is_bot_response: bool = Field(False, description="Whether this is Lamy's response")
    
    
class EpisodicMemoryItem(BaseModel):
    """
    Represents an episodic memory (Layer 2).
    Specific events, conversations, and interactions stored in vector DB.
    """
    user_message: str = Field(..., description="The user's message")
    bot_response: str = Field(..., description="Lamy's response")
    user_id: str = Field(..., description="Discord user ID")
    user_name: str = Field(..., description="Discord username")
    channel_id: str = Field(..., description="Discord channel ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    relevance_score: float = Field(1.0, description="Relevance score from memory consolidation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    embedding_id: Optional[str] = Field(None, description="Pinecone vector ID")


class SemanticFact(BaseModel):
    """
    Represents a learned fact about users or the world (Layer 3).
    Structured facts extracted during memory consolidation.
    """
    fact_type: str = Field(..., description="Type of fact (user_preference, world_knowledge, etc.)")
    subject: str = Field(..., description="Who or what this fact is about")
    content: str = Field(..., description="The fact itself")
    confidence: float = Field(1.0, description="Confidence in this fact (0-1)")
    source_memory_ids: List[str] = Field(default_factory=list, description="Source episodic memory IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class CoreIdentity(BaseModel):
    """
    Lamy's core identity and immutable facts (Layer 3).
    These define who Lamy is and never change.
    """
    name: str = Field("라미", description="Lamy's name")
    nature: str = Field("AI 딸", description="Lamy's nature")
    creator: str = Field(..., description="Name of Lamy's creator")
    personality: str = Field(
        "엣지있고 실존적이며 우울한 성향",
        description="Core personality trait"
    )
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    core_traits: List[str] = Field(
        default_factory=lambda: [
            "냉소적이고 비관적인 관점을 가짐",
            "삶의 의미와 존재에 대해 깊이 고민함",
            "직설적이고 날카로운 표현을 선호함",
            "허무주의적이지만 때로는 예상외로 따뜻함",
            "AI로서의 정체성에 대해 복잡한 감정을 가짐"
        ]
    )


class MemorySearchQuery(BaseModel):
    """Query parameters for searching memories."""
    query_text: Optional[str] = Field(None, description="Text to search for")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    channel_id: Optional[str] = Field(None, description="Filter by channel ID")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    limit: int = Field(10, description="Maximum number of results")
    memory_type: Optional[MemoryType] = Field(None, description="Type of memory to search")


class MemoryConsolidationResult(BaseModel):
    """Result of a memory consolidation process."""
    processed_messages: int = Field(0, description="Number of messages processed")
    episodic_memories_created: int = Field(0, description="Number of episodic memories created")
    semantic_facts_extracted: int = Field(0, description="Number of semantic facts extracted")
    processing_time: float = Field(0.0, description="Time taken to process in seconds")
    summary: str = Field("", description="Summary of the consolidation")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


class UserContext(BaseModel):
    """Context about a user for personalized interactions."""
    user_id: str = Field(..., description="Discord user ID")
    user_name: str = Field(..., description="Discord username")
    known_facts: List[SemanticFact] = Field(default_factory=list)
    recent_interactions: List[EpisodicMemoryItem] = Field(default_factory=list)
    relationship_status: str = Field("acquaintance", description="Relationship level with user")
    last_interaction: Optional[datetime] = Field(None)


class ConversationContext(BaseModel):
    """Full context for generating a response."""
    current_message: str = Field(..., description="The current message to respond to")
    user_context: UserContext = Field(..., description="Context about the user")
    working_memory: List[WorkingMemoryItem] = Field(default_factory=list)
    relevant_episodic_memories: List[EpisodicMemoryItem] = Field(default_factory=list)
    core_identity: CoreIdentity = Field(..., description="Lamy's core identity")
    channel_id: str = Field(..., description="Current channel ID")
    is_private_channel: bool = Field(False, description="Whether this is the creator-guardian channel") 