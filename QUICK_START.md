# 🚀 Quick Start Guide - Friend System

## All Available Endpoints

### 📨 Friend Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/invitations/send` | Send friend request |
| `GET` | `/api/invitations/received` | Get received requests |
| `GET` | `/api/invitations/sent` | Get sent requests |
| `POST` | `/api/invitations/{sender_uid}/accept` | Accept request |
| `POST` | `/api/invitations/{sender_uid}/decline` | Decline request |
| `DELETE` | `/api/invitations/{receiver_uid}/cancel` | Cancel sent request |

### 👥 Friends

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/contacts/` | Get all friends |
| `GET` | `/api/contacts/?search=john` | Search friends |
| `GET` | `/api/contacts/stats` | Get friend stats |
| `GET` | `/api/contacts/mutual/{uid}` | Get mutual friends |
| `DELETE` | `/api/contacts/{friend_uid}` | Unfriend |

---

## Usage Examples

### 1. Send Friend Request
```javascript
// Frontend (JavaScript/React)
const sendFriendRequest = async (receiverUid) => {
  const response = await fetch('/api/invitations/send', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      receiver_uid: receiverUid,
      message: 'Hi! Let\'s be friends!'
    })
  });
  return await response.json();
};
```

### 2. Get Pending Requests
```javascript
const getPendingRequests = async () => {
  const response = await fetch('/api/invitations/received?status=pending', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
};
```

### 3. Accept Request
```javascript
const acceptFriendRequest = async (senderUid) => {
  const response = await fetch(`/api/invitations/${senderUid}/accept`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
};
```

### 4. Get All Friends
```javascript
const getFriends = async () => {
  const response = await fetch('/api/contacts/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
};
```

### 5. Search Friends
```javascript
const searchFriends = async (query) => {
  const response = await fetch(`/api/contacts/?search=${query}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
};
```

---

## Python Client Examples

### 1. Send Friend Request
```python
import requests

def send_friend_request(receiver_uid, token):
    response = requests.post(
        'http://localhost:8000/api/invitations/send',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'receiver_uid': receiver_uid,
            'message': 'Hi! Let\'s connect!'
        }
    )
    return response.json()
```

### 2. Get Friends
```python
def get_friends(token):
    response = requests.get(
        'http://localhost:8000/api/contacts/',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()
```

### 3. Accept Request
```python
def accept_friend_request(sender_uid, token):
    response = requests.post(
        f'http://localhost:8000/api/invitations/{sender_uid}/accept',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()
```

---

## Response Structures

### Friend Request Response
```json
{
  "sender_uid": "abc123",
  "receiver_uid": "xyz789",
  "sender_username": "john_doe",
  "sender_profile_photo": "https://...",
  "status": "pending",
  "message": "Hey! Let's connect!",
  "created_at": "2025-10-24T12:00:00"
}
```

### Friends List Response
```json
{
  "contacts": [
    {
      "uid": "abc123",
      "user_id": "uuid-here",
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "bio": "Software Developer",
      "profile_photo": "https://...",
      "friendship_since": "2025-10-01T10:00:00"
    }
  ],
  "total": 42
}
```

### Friend Stats Response
```json
{
  "total_friends": 42,
  "pending_sent": 3,
  "pending_received": 5
}
```

---

## Common Workflows

### Workflow 1: Complete Friend Connection
```
1. User A sends request to User B
   POST /api/invitations/send

2. User B sees pending request
   GET /api/invitations/received

3. User B accepts
   POST /api/invitations/{userA_uid}/accept

4. Both see each other in friends list
   GET /api/contacts/
```

### Workflow 2: Search and Connect
```
1. Search for user by username
   (Use your existing user search endpoint)

2. Send friend request
   POST /api/invitations/send

3. Wait for acceptance
   GET /api/invitations/sent (track status)

4. View friend profile
   GET /api/contacts/
```

### Workflow 3: Mutual Friends Discovery
```
1. View user profile
   (Use your existing user profile endpoint)

2. Check mutual friends
   GET /api/contacts/mutual/{other_user_uid}

3. Send requests to mutual friends
   POST /api/invitations/send
```

---

## Error Handling

```javascript
const sendFriendRequest = async (receiverUid) => {
  try {
    const response = await fetch('/api/invitations/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ receiver_uid: receiverUid })
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 400:
          // Bad request (already friends, duplicate, etc.)
          alert(error.detail);
          break;
        case 401:
          // Unauthorized - redirect to login
          window.location.href = '/login';
          break;
        case 404:
          // User not found
          alert('User not found');
          break;
        default:
          alert('An error occurred');
      }
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
};
```

---

## Testing with Postman

### 1. Set Environment Variables
```
BASE_URL = http://localhost:8000
ACCESS_TOKEN = your_jwt_token_here
```

### 2. Create Collection
- Import all endpoints from documentation
- Set Authorization header: `Bearer {{ACCESS_TOKEN}}`

### 3. Test Sequence
1. Login → Get token
2. Send friend request
3. Switch user → Accept request
4. Get friends list
5. Search friends
6. Get mutual friends
7. Unfriend

---

## Integration Tips

### Real-time Updates
```javascript
// When you receive WebSocket notification
socket.on('friend_request_received', (data) => {
  // Refresh pending requests
  getPendingRequests();
  // Show notification
  showNotification(`${data.sender_username} sent you a friend request!`);
});

socket.on('friend_request_accepted', (data) => {
  // Refresh friends list
  getFriends();
  // Show notification
  showNotification(`${data.username} accepted your friend request!`);
});
```

### UI Components
```jsx
// React Component Example
function FriendRequestButton({ userId }) {
  const [status, setStatus] = useState('none'); // none, pending, friends
  
  const sendRequest = async () => {
    const result = await sendFriendRequest(userId);
    if (result) {
      setStatus('pending');
    }
  };
  
  if (status === 'friends') return <span>Friends ✓</span>;
  if (status === 'pending') return <span>Request Sent...</span>;
  
  return <button onClick={sendRequest}>Add Friend</button>;
}
```

---

## Performance Tips

1. **Cache friends list** - refresh only when needed
2. **Paginate results** - add skip/limit parameters (future enhancement)
3. **Debounce search** - wait 300ms before searching
4. **Batch operations** - if sending multiple requests
5. **WebSocket for real-time** - push updates instead of polling

---

## Security Best Practices

1. ✅ Always validate JWT token server-side
2. ✅ Never trust client-provided sender_uid (use token)
3. ✅ Rate limit friend request endpoints
4. ✅ Validate receiver_uid exists before creating request
5. ✅ Log suspicious activity (spam requests, etc.)

---

## Need Help?

Check these files:
- 📚 **Full API Docs**: `/FRIEND_SYSTEM_API.md`
- 📝 **Implementation Summary**: `/IMPLEMENTATION_SUMMARY.md`
- 💻 **Code**:
  - Models: `/app/models/user.py`
  - Schemas: `/app/schemas/invitation.py`, `/app/schemas/contact.py`
  - CRUD: `/app/crud/invitation.py`, `/app/crud/contact.py`
  - Routes: `/app/routers/invitation.py`, `/app/routers/contact.py`

---

**Happy coding! 🚀**
