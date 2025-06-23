from pydantic import BaseModel, HttpUrl
from enum import Enum
from typing import Literal
from beanie import PydanticObjectId
from core.database.models import DialogueMessage

class ChannelCreate(BaseModel):
    webhook_url: HttpUrl

class ChannelUpdate(BaseModel):
    webhook_url: HttpUrl

class IncomingMessage(BaseModel):
    message_id: str
    chat_id: str
    text: str
    message_sender: Literal["customer", "employee"]

class OutgoingPayload(BaseModel):
    event_type: str = "new_message"
    chat_id: str
    text: str

class ChannelOut(BaseModel):
    id: PydanticObjectId
    message_list: list[DialogueMessage]
    webhook_url: HttpUrl


class ChatBotUpdate(BaseModel):
    name: str | None = None
    secret_token: str | None = None

class ChatBotCreate(BaseModel):
    name: str
    secret_token: str


class ChatBotResponse(ChatBotCreate):
    id: PydanticObjectId
    class Config:
        from_attributes = True