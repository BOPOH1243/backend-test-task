import pytest
from httpx import AsyncClient
from fastapi import status

# Base path for the API
BASE_PATH = "/api/chatbots"

@pytest.mark.asyncio
async def test_create_and_get_chatbot(client: AsyncClient) -> None:
    # Create a new chatbot
    payload = {"name": "TestBot", "secret_token": "s3cr3t"}
    create_resp = await client.post(f"{BASE_PATH}/", json=payload)
    assert create_resp.status_code == status.HTTP_201_CREATED
    data = create_resp.json()
    # Ensure response contains id and matches payload
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["secret_token"] == payload["secret_token"]

    chatbot_id = data["id"]
    get_resp = await client.get(f"{BASE_PATH}/{chatbot_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    fetched = get_resp.json()
    assert fetched.get("name") == payload["name"]
    assert fetched.get("secret_token") == payload["secret_token"]

@pytest.mark.asyncio
async def test_get_all_chatbots_empty_and_nonempty(client: AsyncClient):
    # Initially, no chatbots
    resp_empty = await client.get(BASE_PATH)
    assert resp_empty.status_code == status.HTTP_200_OK
    assert resp_empty.json() == []

    # Add one chatbot
    payload = {"name": "Bot1", "secret_token": "t0ken"}
    await client.post(f"{BASE_PATH}/", json=payload)

    # Now, get all should return a list of one
    resp_list = await client.get(BASE_PATH)
    assert resp_list.status_code == status.HTTP_200_OK
    data_list = resp_list.json()
    assert isinstance(data_list, list)
    assert len(data_list) == 1
    assert data_list[0]["name"] == payload["name"]

@pytest.mark.asyncio
async def test_update_chatbot_and_partial_update(client: AsyncClient):
    # Create chatbot
    payload = {"name": "Original", "secret_token": "orig"}
    create_resp = await client.post(f"{BASE_PATH}/", json=payload)
    chatbot_id = create_resp.json()["id"]

    # Full update both fields
    update_payload = {"name": "Updated", "secret_token": "upd"}
    update_resp = await client.put(f"{BASE_PATH}/{chatbot_id}", json=update_payload)
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["name"] == update_payload["name"]
    assert updated["secret_token"] == update_payload["secret_token"]

    # Partial update: only name
    partial = {"name": "PartialOnly"}
    partial_resp = await client.put(f"{BASE_PATH}/{chatbot_id}", json=partial)
    assert partial_resp.status_code == status.HTTP_200_OK
    partial_data = partial_resp.json()
    assert partial_data["name"] == "PartialOnly"
    assert partial_data["secret_token"] == update_payload["secret_token"]

@pytest.mark.asyncio
async def test_delete_chatbot_and_not_found_behaviour(client: AsyncClient):
    # Create chatbot
    payload = {"name": "ToDelete", "secret_token": "deltoken"}
    create_resp = await client.post(f"{BASE_PATH}/", json=payload)
    chatbot_id = create_resp.json()["id"]

    # Delete it
    del_resp = await client.delete(f"{BASE_PATH}/{chatbot_id}")
    assert del_resp.status_code == status.HTTP_200_OK
    assert del_resp.json() == {"detail": "ChatBot deleted"}

    # Now it should not be found
    not_found_resp = await client.get(f"{BASE_PATH}/{chatbot_id}")
    assert not_found_resp.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_resp.json()["detail"] == "ChatBot not found"

    # Attempt update on non-existent
    update_resp = await client.put(f"{BASE_PATH}/{chatbot_id}", json={"name": "X"})
    assert update_resp.status_code == status.HTTP_404_NOT_FOUND
    assert update_resp.json()["detail"] == "ChatBot not found"

    # Attempt delete again
    del_resp2 = await client.delete(f"{BASE_PATH}/{chatbot_id}")
    assert del_resp2.status_code == status.HTTP_404_NOT_FOUND
    assert del_resp2.json()["detail"] == "ChatBot not found"
