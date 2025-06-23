# tests/test_channels.py
import pytest
from httpx import AsyncClient
from bson import ObjectId
from fastapi import status

BASE_PATH = "/api/channel"

@pytest.mark.asyncio
async def test_create_and_update_channel(client: AsyncClient):
    # Создаем бота для теста
    bot_payload = {"name": "ChannelTestBot", "secret_token": "bot-secret"}
    bot_response = await client.post("/api/chatbots/", json=bot_payload)
    assert bot_response.status_code == status.HTTP_201_CREATED
    bot_data = bot_response.json()
    chatbot_id = bot_data["id"]

    # Создаем канал
    channel_payload = {"webhook_url": "https://test-create.com/webhook"}
    create_response = await client.post(
        f"{BASE_PATH}/",
        params={"chat_bot_id": chatbot_id},
        json=channel_payload
    )
    
    assert create_response.status_code == status.HTTP_201_CREATED
    channel_data = create_response.json()
    assert channel_data["chat_bot_id"] == chatbot_id
    assert channel_data["webhook_url"] == channel_payload["webhook_url"]
    assert ObjectId.is_valid(channel_data["_id"])
    channel_id = channel_data["_id"]

    # Обновляем канал
    new_url = "https://updated-url.com/webhook"
    update_response = await client.put(
        f"{BASE_PATH}/{channel_id}",
        json={"webhook_url": new_url}
    )
    
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json() == {}

    # Проверяем обновление
    get_response = await client.get(f"{BASE_PATH}/")
    assert get_response.status_code == status.HTTP_200_OK
    channels = get_response.json()
    updated = next((ch for ch in channels if ch["id"] == channel_id), None)
    assert updated is not None
    assert updated["webhook_url"] == new_url

@pytest.mark.asyncio
async def test_delete_channel(client: AsyncClient):
    # Создаем бота
    bot_payload = {"name": "DeleteTestBot", "secret_token": "delete-secret"}
    bot_response = await client.post("/api/chatbots/", json=bot_payload)
    assert bot_response.status_code == status.HTTP_201_CREATED
    chatbot_id = bot_response.json()["id"]

    # Создаем канал
    channel_payload = {"webhook_url": "https://delete-test.com/webhook"}
    create_response = await client.post(
        f"{BASE_PATH}/",
        params={"chat_bot_id": chatbot_id},
        json=channel_payload
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    channel_id = create_response.json()["_id"]

    # Удаляем канал
    delete_response = await client.delete(f"{BASE_PATH}/{channel_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Проверяем удаление
    get_response = await client.get(f"{BASE_PATH}/{channel_id}/messages")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

#тест чисто по приколу
@pytest.mark.asyncio
async def test_list_channels(client: AsyncClient):
    # Очищаем предыдущие данные
    list_response = await client.get(f"{BASE_PATH}/")
    assert list_response.status_code == status.HTTP_200_OK
    initial_count = len(list_response.json())

    # Создаем бота
    bot_payload = {"name": "ListTestBot", "secret_token": "list-secret"}
    bot_response = await client.post("/api/chatbots/", json=bot_payload)
    assert bot_response.status_code == status.HTTP_201_CREATED
    chatbot_id = bot_response.json()["id"]

    # Создаем канал 1
    channel1_payload = {"webhook_url": "https://list-test1.com/webhook"}
    create1_response = await client.post(
        f"{BASE_PATH}/",
        params={"chat_bot_id": chatbot_id},
        json=channel1_payload
    )
    assert create1_response.status_code == status.HTTP_201_CREATED
    channel1_id = create1_response.json()["_id"]

    # Создаем канал 2
    channel2_payload = {"webhook_url": "https://list-test2.com/webhook"}
    create2_response = await client.post(
        f"{BASE_PATH}/",
        params={"chat_bot_id": chatbot_id},
        json=channel2_payload
    )
    assert create2_response.status_code == status.HTTP_201_CREATED
    channel2_id = create2_response.json()["_id"]

    # Получаем список каналов
    list_response = await client.get(f"{BASE_PATH}/")
    assert list_response.status_code == status.HTTP_200_OK
    
    channels = list_response.json()
    assert len(channels) == initial_count + 2
    assert any(ch["id"] == channel1_id for ch in channels)
    assert any(ch["id"] == channel2_id for ch in channels)

@pytest.mark.asyncio
async def test_get_channel_messages(client: AsyncClient):
    # Создаем бота
    bot_payload = {"name": "MessagesTestBot", "secret_token": "messages-secret"}
    bot_response = await client.post("/api/chatbots/", json=bot_payload)
    assert bot_response.status_code == status.HTTP_201_CREATED
    chatbot_id = bot_response.json()["id"]

    # Создаем канал
    channel_payload = {"webhook_url": "https://messages-test.com/webhook"}
    create_response = await client.post(
        f"{BASE_PATH}/",
        params={"chat_bot_id": chatbot_id},
        json=channel_payload
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    channel_id = create_response.json()["_id"]

    # Добавляем тестовые сообщения (через прямое обращение к модели)
    from core.database.models import Dialogue
    channel = await Dialogue.find_one({"_id": ObjectId(channel_id)})
    if channel:
        channel.message_list = [{"text": "Test message 1"}, {"text": "Test message 2"}]
        await channel.save()
    
    # Получаем сообщения
    response = await client.get(f"{BASE_PATH}/{channel_id}/messages")
    assert response.status_code == status.HTTP_200_OK
    messages = response.json()
    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]["text"] == "Test message 1"
    assert messages[1]["text"] == "Test message 2"

@pytest.mark.asyncio
async def test_not_found_cases(client: AsyncClient):
    fake_id = "5f9d9b3d9c6d6f3a7c8b9a9a"  # Valid but non-existent ObjectId
    
    # Обновление несуществующего канала
    update_response = await client.put(
        f"{BASE_PATH}/{fake_id}",
        json={"webhook_url": "https://test.com"}
    )
    assert update_response.status_code == status.HTTP_404_NOT_FOUND
    
    # Удаление несуществующего канала
    delete_response = await client.delete(f"{BASE_PATH}/{fake_id}")
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND
    
    # Получение сообщений несуществующего канала
    messages_response = await client.get(f"{BASE_PATH}/{fake_id}/messages")
    assert messages_response.status_code == status.HTTP_404_NOT_FOUND