# Friend System API Documentation

## Overview
Complete friend request and friends management system for Chattera using Neo4j graph database.

## Authentication
All endpoints require JWT Bearer token authentication in the header:
```
Authorization: Bearer <your_access_token>
```

---

## 📨 Friend Requests (Invitations)

### 1. Send Friend Request
**POST** `/api/invitations/send`

Send a friend request to another user.

**Request Body:**
```json
{
  "receiver_uid": "string",
  "message": "Optional message with request"
}
```

**Response:** `201 Created`
```json
{
  "message": "Friend request sent successfully",
  "sender_uid": "string",
  "receiver_uid": "string",
  "status": "pending"
}
```

**Errors:**
- `400`: Cannot send to yourself / Already friends / Request already exists
- `404`: Receiver not found

---

### 2. Get Received Friend Requests
**GET** `/api/invitations/received?status=pending`

Get all friend requests you've received.

**Query Parameters:**
- `status` (optional): `pending` | `accepted` | `declined` (default: `pending`)

**Response:** `200 OK`
```json
{
  "invitations": [
    {
      "sender_uid": "string",
      "receiver_uid": "string",
      "sender_username": "string",
      "sender_profile_photo": "string",
      "status": "pending",
      "message": "string",
      "created_at": "2025-10-24T12:00:00"
    }
  ],
  "total": 5
}
```

---

### 3. Get Sent Friend Requests
**GET** `/api/invitations/sent?status=pending`

Get all friend requests you've sent.

**Query Parameters:**
- `status` (optional): `pending` | `accepted` | `declined` (default: `pending`)

**Response:** `200 OK`
```json
{
  "invitations": [
    {
      "sender_uid": "string",
      "receiver_uid": "string",
      "receiver_username": "string",
      "receiver_profile_photo": "string",
      "status": "pending",
      "message": "string",
      "created_at": "2025-10-24T12:00:00"
    }
  ],
  "total": 3
}
```

---

### 4. Accept Friend Request
**POST** `/api/invitations/{sender_uid}/accept`

Accept a friend request from another user.

**Response:** `200 OK`
```json
{
  "message": "Friend request accepted",
  "sender_uid": "string",
  "receiver_uid": "string",
  "status": "accepted"
}
```

**Errors:**
- `404`: Friend request not found
- `400`: Request already responded to

---

### 5. Decline Friend Request
**POST** `/api/invitations/{sender_uid}/decline`

Decline a friend request from another user.

**Response:** `200 OK`
```json
{
  "message": "Friend request declined",
  "sender_uid": "string",
  "receiver_uid": "string",
  "status": "declined"
}
```

---

### 6. Cancel Sent Friend Request
**DELETE** `/api/invitations/{receiver_uid}/cancel`

Cancel a friend request you sent.

**Response:** `204 No Content`

**Errors:**
- `404`: Request not found or cannot be cancelled

---

## 👥 Friends (Contacts)

### 1. Get All Friends
**GET** `/api/contacts/?search=john`

Get all your friends with optional search.

**Query Parameters:**
- `search` (optional): Search by username or full name

**Response:** `200 OK`
```json
{
  "contacts": [
    {
      "uid": "string",
      "user_id": "string",
      "username": "string",
      "email": "string",
      "full_name": "string",
      "bio": "string",
      "profile_photo": "string",
      "friendship_since": "2025-10-01T10:00:00"
    }
  ],
  "total": 42
}
```

---

### 2. Get Friend Statistics
**GET** `/api/contacts/stats`

Get statistics about your friendships.

**Response:** `200 OK`
```json
{
  "total_friends": 42,
  "pending_sent": 3,
  "pending_received": 5
}
```

---

### 3. Get Mutual Friends
**GET** `/api/contacts/mutual/{other_uid}`

Get mutual friends between you and another user.

**Response:** `200 OK`
```json
{
  "mutual_friends": [
    {
      "uid": "string",
      "user_id": "string",
      "username": "string",
      "email": "string",
      "full_name": "string",
      "profile_photo": "string"
    }
  ],
  "count": 5
}
```

---

### 4. Remove Friend (Unfriend)
**DELETE** `/api/contacts/{friend_uid}`

Remove a friend from your contacts.

**Response:** `204 No Content`

**Errors:**
- `404`: Not friends with this user
- `500`: Failed to remove friend

---

## 📊 Database Schema (Neo4j)

### Nodes
```
(:User {
  uid: string,
  user_id: string,
  username: string,
  email: string,
  full_name: string,
  bio: string,
  profile_photo: string
})
```

### Relationships

**1. Friend Request:**
```cypher
(:User)-[r:INVITED {
  status: "pending" | "accepted" | "declined",
  message: string,
  created_at: datetime,
  updated_at: datetime
}]->(:User)
```

**2. Friendship (Bidirectional):**
```cypher
(:User)-[r:CONTACT {
  created_at: datetime
}]->(:User)
```

---

## 🔄 Workflow Examples

### Example 1: Complete Friend Request Flow

1. **User A sends request to User B:**
   ```bash
   POST /api/invitations/send
   {
     "receiver_uid": "user_b_uid"
   }
   ```

2. **User B checks pending requests:**
   ```bash
   GET /api/invitations/received?status=pending
   ```

3. **User B accepts request:**
   ```bash
   POST /api/invitations/{user_a_uid}/accept
   ```

4. **Both users now see each other in friends list:**
   ```bash
   GET /api/contacts/
   ```

### Example 2: Search and Find Mutual Friends

1. **Search your friends:**
   ```bash
   GET /api/contacts/?search=john
   ```

2. **Check mutual friends with a user:**
   ```bash
   GET /api/contacts/mutual/{other_user_uid}
   ```

---

## 🚨 Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request (validation failed, duplicate request, etc.) |
| 401  | Unauthorized (invalid or missing token) |
| 403  | Forbidden (trying to access another user's data) |
| 404  | Not Found (user or request doesn't exist) |
| 500  | Internal Server Error |

---

## 🧪 Testing with cURL

### Send Friend Request
```bash
curl -X POST "http://localhost:8000/api/invitations/send" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"receiver_uid": "receiver_uid_here"}'
```

### Get Your Friends
```bash
curl -X GET "http://localhost:8000/api/contacts/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Accept Friend Request
```bash
curl -X POST "http://localhost:8000/api/invitations/sender_uid_here/accept" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ✅ Features Implemented

- ✅ Send friend requests with optional message
- ✅ Accept/decline friend requests
- ✅ Cancel sent requests
- ✅ View received requests (pending/all)
- ✅ View sent requests (pending/all)
- ✅ List all friends
- ✅ Search friends by name/username
- ✅ Get mutual friends
- ✅ Unfriend users
- ✅ Friend statistics
- ✅ Bidirectional friendship (graph database)
- ✅ Duplicate request prevention
- ✅ Self-request prevention
- ✅ Already friends check
- ✅ JWT authentication on all endpoints
- ✅ Backward compatibility with legacy endpoints

---

## 🎯 Neo4j Graph Advantages

1. **Natural Modeling**: Friends are graph relationships
2. **Fast Traversal**: Mutual friends in one query
3. **Bidirectional**: Automatic symmetric friendships
4. **Path Finding**: Can find shortest path between users
5. **Friend Suggestions**: Friends-of-friends queries are fast

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- Friend relationships are bidirectional (both users become friends)
- Accepting a request automatically creates the friendship
- Legacy endpoints (`/invitations/`, `/invitations/{sender}/{receiver}/respond`, `/contacts/{user_uid}`) still work for backward compatibility
- Use the new endpoints for better developer experience
