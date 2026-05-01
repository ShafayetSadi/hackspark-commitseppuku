# Chat Curl Examples

All chat endpoints go through the API gateway and require a JWT bearer token.

Base URL used below:

```bash
export API_URL="http://localhost:8000"
```

## 1. Register

```bash
curl -X POST "$API_URL/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chat-user@example.com",
    "password": "password123",
    "name": "Chat User"
  }'
```

## 2. Login and save bearer token

```bash
TOKEN=$(curl -s -X POST "$API_URL/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chat-user@example.com",
    "password": "password123"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "$TOKEN"
```

## 3. Start a chat session

This first request creates a session and returns a `session_id`.

```bash
curl -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Is tools category growing?"
  }'
```

## 4. Save the returned session id

Replace the value below with the `session_id` returned from the first chat response.

```bash
export SESSION_ID="replace-with-session-id"
```

## 5. Continue the same chat

```bash
curl -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What days surge most for tools?\",
    \"session_id\": \"$SESSION_ID\"
  }"
```

## 6. List chat sessions

```bash
curl -X GET "$API_URL/chat/sessions" \
  -H "Authorization: Bearer $TOKEN"
```

## 7. Get chat history

```bash
curl -X GET "$API_URL/chat/$SESSION_ID/history" \
  -H "Authorization: Bearer $TOKEN"
```

## 8. Delete a chat session

```bash
curl -X DELETE "$API_URL/chat/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN"
```
