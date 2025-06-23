from fastapi import APIRouter, HTTPException
from core.database.models import Dialogue
from .schemas import ChannelCreate, ChannelUpdate, ChannelOut
from typing import List
from bson import ObjectId
router = APIRouter(prefix="/channel")

@router.post("/", response_model=None, status_code=201)
async def create_channel(data: ChannelCreate, chat_bot_id: str):
    channel = Dialogue(chat_bot_id=chat_bot_id, webhook_url=data.webhook_url)
    await channel.insert()
    return channel

@router.put("/{token}")
async def update_channel(token: str, data: ChannelUpdate):
    ch = await Dialogue.find_one({"_id": ObjectId(token)})
    if not ch:
        raise HTTPException(404, "Channel not found")
    ch.webhook_url = data.webhook_url
    await ch.save()
    return {}

@router.delete("/{token}", status_code=204)
async def delete_channel(token: str):
    ch = await Dialogue.find_one({"_id": ObjectId(token)})
    if not ch:
        raise HTTPException(404, "Channel not found")
    await ch.delete()

@router.get("/", response_model=List[ChannelOut])
async def list_channels():
    dialogs = await Dialogue.find_all().to_list()
    return dialogs #[ChannelOut(webhook_url=d.webhook_url) for d in dialogs]

@router.get("/{token}/messages")
async def get_channel_messages(token: str):
    ch = await Dialogue.find_one({"_id": ObjectId(token)})
    if not ch:
        raise HTTPException(404, "Channel not found")
    return ch.message_list
