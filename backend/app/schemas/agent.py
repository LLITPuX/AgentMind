"""Pydantic schemas for agent analysis and conversation endpoints."""

from __future__ import annotations

from typing import List, Literal, Mapping

from pydantic import BaseModel, Field


Sender = Literal["user", "ai"]


class ChatMessagePayload(BaseModel):
    id: str
    text: str
    sender: Sender


class AgentSettings(BaseModel):
    systemPrompt: str = Field(alias="systemPrompt")
    jsonSchema: str = Field(alias="jsonSchema")


class AnalysisRequest(BaseModel):
    message: ChatMessagePayload
    settings: AgentSettings


class AnalysisResponse(BaseModel):
    messageId: str
    analysis: Mapping[str, object]


class ConversationRequest(BaseModel):
    messages: List[ChatMessagePayload]
    settings: AgentSettings


class ConversationResponse(BaseModel):
    message: str



