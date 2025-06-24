from fastapi import APIRouter, Header, HTTPException, BackgroundTasks, Depends
from .schemas import IncomingMessage, OutgoingPayload
from core.database.models import Dialogue, MessageRole, DialogueMessage, ChatBot
from predict.mock_llm_call import mock_llm_call
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from bson import ObjectId
import httpx

router = APIRouter(prefix="/webhook")
bearer = HTTPBearer(auto_error=False)


async def get_chatbot(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Недостаточно прав")
    secret = creds.credentials
    cb = await ChatBot.find_one(ChatBot.secret_token == secret)
    if not cb:
        raise HTTPException(status_code=403, detail="Недействительный токен")
    return cb


@router.post("/new_message", status_code=200)
async def inbound_message(
    msg: IncomingMessage,
    background: BackgroundTasks,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Недостаточно прав")
    secret = creds.credentials

    dialog = await Dialogue.find_one({"_id": ObjectId(secret)})
    if not dialog:
        raise HTTPException(status_code=404, detail="not found")

    if dialog.message_list:
        last_msg = dialog.message_list[-1]
        if last_msg.text == msg.message_id:
            return {}

    # Добавляем пользовательское сообщение
    dialog.message_list.append(DialogueMessage(role=MessageRole.USER, text=msg.text))
    await dialog.save()

    # Отправляем в фон дальнейшую обработку
    background.add_task(
        process_and_respond,
        dialog.id,
        msg.chat_id,
        msg.message_sender,
    )

    return {}  # Ответ немедленно


async def process_and_respond(dialog_id: ObjectId, chat_id: str, sender: str):
    # Повторно достаём диалог (безопасно для фоновой задачи)
    dialog = await Dialogue.find_one({"_id": dialog_id})
    if not dialog:
        print(f"Диалог {dialog_id} не найден")
        return

    # Генерация ответа
    reply = await mock_llm_call(dialog.message_list)

    # Сохраняем ответ
    dialog.message_list.append(DialogueMessage(role=MessageRole.ASSISTANT, text=reply))
    await dialog.save()

    # Отправка ответа, если инициатор — клиент
    if sender == "customer":
        await send_reply(
            url=str(dialog.webhook_url),
            token=str(dialog.id),
            chat_id=chat_id,
            text=reply
        )


async def send_reply(url, token, chat_id, text):
    payload = OutgoingPayload(chat_id=chat_id, text=text)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload.dict(), headers=headers)
    except Exception as e:
        print(f"Ошибка при отправке ответа: {e}")
