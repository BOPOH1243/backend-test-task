from fastapi import FastAPI, HTTPException, APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from beanie import PydanticObjectId
from core.database.models import ChatBot
from .schemas import ChatBotCreate, ChatBotUpdate, ChatBotResponse

# Инициализация приложения
router = APIRouter()

# CREATE
@router.post("/chatbots/", response_model=ChatBotResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot(chatbot: ChatBotCreate):
    chatbot_data = jsonable_encoder(chatbot)
    new_chatbot = ChatBot(**chatbot_data)
    await new_chatbot.insert()
    print(new_chatbot)
    return new_chatbot


# READ (все)
@router.get("/chatbots", response_model=List[ChatBot])
async def get_all_chatbots():
    return await ChatBot.find_all().to_list()


# READ (по ID)
@router.get("/chatbots/{chatbot_id}", response_model=ChatBot)
async def get_chatbot(chatbot_id: str):
    chatbot = await ChatBot.get(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="ChatBot not found")
    return chatbot


# UPDATE
@router.put("/chatbots/{chatbot_id}", response_model=ChatBot)
async def update_chatbot(chatbot_id: str, data: ChatBotUpdate):
    chatbot = await ChatBot.get(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="ChatBot not found")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chatbot, field, value)

    await chatbot.save()
    return chatbot


# DELETE
@router.delete("/chatbots/{chatbot_id}")
async def delete_chatbot(chatbot_id: str):
    chatbot = await ChatBot.get(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="ChatBot not found")

    await chatbot.delete()
    return {"detail": "ChatBot deleted"}
