from enum import StrEnum, auto

from beanie import Document, PydanticObjectId, Indexed
from pydantic import BaseModel, HttpUrl, Field
from bson import ObjectId

class MessageRole(StrEnum):
    ASSISTANT = auto()
    SYSTEM = auto()
    USER = auto()


class DialogueMessage(BaseModel):
    role: MessageRole
    text: str


class Dialogue(Document):
    chat_bot_id: PydanticObjectId
    message_list: list[DialogueMessage] = []
    webhook_url: HttpUrl