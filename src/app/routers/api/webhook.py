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

#async def get_chatbot(
#    creds: HTTPAuthorizationCredentials = Depends(bearer)
#):
#    if creds is None or creds.scheme.lower() != "bearer":
#        raise HTTPException(status_code=401, detail="Недостаточно прав")
#    cb = await ChatBot.find_one(ChatBot.secret_token == creds.credentials)
#    if not cb:
#        raise HTTPException(status_code=403, detail="Недействительный токен")
#    return cb

@router.post("/new_message", status_code=200)
async def inbound_message(
    msg: IncomingMessage,
    background: BackgroundTasks,
    #cb=Depends(get_chatbot),
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Недостаточно прав")
    secret = creds.credentials
    print(secret)
    # Найти текущий диалог
    dialog = await Dialogue.find_one({"_id": ObjectId(secret)})
    if not dialog:
        raise HTTPException(status_code=404, detail="not found")

    # Проверяем только последнее сообщение, чтобы избежать дубликатов
    if dialog.message_list:
        last_msg = dialog.message_list[-1]
        if last_msg.text == msg.message_id:
            return {}

    # Сохраняем входящее сообщение пользователя
    dialog.message_list.append(DialogueMessage(role=MessageRole.USER, text=msg.text))
    await dialog.save()

    # Генерируем ответ от LLM
    reply = await mock_llm_call(dialog.message_list) #FIXME это явно стопает поток, надо перенести в background
    dialog.message_list.append(DialogueMessage(role=MessageRole.ASSISTANT, text=reply))
    await dialog.save()
    print(msg.message_sender)
    if msg.message_sender == "customer":
        background.add_task(
            send_reply,
            str(dialog.webhook_url),
            dialog.id,
            msg.chat_id,
            reply
        )
    return {}

async def send_reply(url, token, chat_id, text):
    payload = OutgoingPayload(chat_id=chat_id, text=text)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload.dict(), headers=headers)
