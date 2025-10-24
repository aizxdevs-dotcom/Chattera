# 🎯 Friend System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  - Friend Request UI                                             │
│  - Friends List                                                  │
│  - Search Friends                                                │
│  - Notifications                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP Requests (JWT Auth)
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Routers (Endpoints)                     │  │
│  │  ┌─────────────────┐    ┌─────────────────┐            │  │
│  │  │   Invitations   │    │    Contacts     │            │  │
│  │  │  /invitations/* │    │   /contacts/*   │            │  │
│  │  └────────┬────────┘    └────────┬────────┘            │  │
│  └───────────┼──────────────────────┼──────────────────────┘  │
│              │                      │                          │
│  ┌───────────▼──────────────────────▼──────────────────────┐  │
│  │                  CRUD Layer                              │  │
│  │  - invitation.py (friend request operations)            │  │
│  │  - contact.py (friend management operations)            │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │               Pydantic Schemas                           │  │
│  │  - Validation                                            │  │
│  │  - Serialization                                         │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │             Neomodel (ORM Layer)                         │  │
│  │  - User node                                             │  │
│  │  - InvitationRel relationship                           │  │
│  │  - ContactRel relationship                              │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                    Neo4j Graph Database                       │
│                                                               │
│  (:User)-[:INVITED {status: "pending"}]->(:User)            │
│  (:User)-[:CONTACT {created_at: datetime}]<->(:User)        │
│                                                               │
│  Benefits:                                                    │
│  ✓ Fast graph traversal                                      │
│  ✓ Natural relationship modeling                             │
│  ✓ Bidirectional friendships                                 │
│  ✓ Mutual friends queries                                    │
└───────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Send Friend Request
```
Frontend
    │
    ├─→ POST /api/invitations/send {receiver_uid, message}
    │
Router (invitation.py)
    │
    ├─→ Validate JWT token
    ├─→ Check if already friends (contact CRUD)
    ├─→ Check for duplicate requests
    │
CRUD (invitation.py)
    │
    ├─→ send_invitation(sender_uid, receiver_uid, message)
    │
Neomodel
    │
    ├─→ Create relationship: (Sender)-[:INVITED {status: "pending"}]->(Receiver)
    │
Neo4j
    │
    └─→ ✅ Friend request stored
```

### 2. Accept Friend Request
```
Frontend
    │
    ├─→ POST /api/invitations/{sender_uid}/accept
    │
Router (invitation.py)
    │
    ├─→ Validate JWT token
    ├─→ Verify receiver is current user
    │
CRUD (invitation.py)
    │
    ├─→ respond_invitation(sender_uid, receiver_uid, accept=True)
    │
Neomodel
    │
    ├─→ Update: [:INVITED {status: "accepted"}]
    ├─→ Create: (UserA)-[:CONTACT]->(UserB)
    ├─→ Create: (UserB)-[:CONTACT]->(UserA)
    │
Neo4j
    │
    └─→ ✅ Bidirectional friendship created
```

### 3. Get Friends List
```
Frontend
    │
    ├─→ GET /api/contacts/
    │
Router (contact.py)
    │
    ├─→ Validate JWT token
    │
CRUD (contact.py)
    │
    ├─→ list_contacts(user_uid)
    │
Neomodel
    │
    ├─→ Query: (User)-[:CONTACT]->(Friend)
    │
Neo4j
    │
    ├─→ Traverse graph relationships
    │
    └─→ ✅ Return friends with profile data
```

---

## Neo4j Graph Structure

```
                    ┌──────────────┐
                    │   User A     │
                    │ uid: "abc"   │
                    │ username     │
                    └───────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        │ [:INVITED]        │ [:CONTACT]        │ [:INVITED]
        │ status: pending   │ created_at        │ status: accepted
        │ message: "Hi!"    │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   User B      │   │   User C      │   │   User D      │
│ uid: "def"    │   │ uid: "ghi"    │   │ uid: "jkl"    │
│ username      │   │ username      │   │ username      │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            │
                            │ [:CONTACT]
                            │ (bidirectional)
                            │
                    ┌───────▼───────┐
                    │   User E      │
                    │ uid: "mno"    │
                    │ username      │
                    └───────────────┘
```

**Legend:**
- `[:INVITED]` = Friend request
- `[:CONTACT]` = Accepted friendship (bidirectional)
- User A → User B: Pending request
- User A ↔ User C: Friends
- User A ← User D: Accepted request (now friends)
- User C ↔ User E: Friends (mutual friend with A)

---

## API Endpoint Structure

```
/api
├── /invitations
│   ├── POST   /send                          → Send friend request
│   ├── GET    /received?status=pending       → Get received requests
│   ├── GET    /sent?status=pending           → Get sent requests
│   ├── POST   /{sender_uid}/accept           → Accept request
│   ├── POST   /{sender_uid}/decline          → Decline request
│   ├── DELETE /{receiver_uid}/cancel         → Cancel sent request
│   │
│   └── Legacy (backward compatible)
│       ├── POST /{sender_uid}/{receiver_uid}/respond
│       └── GET  /{user_uid}
│
└── /contacts
    ├── GET    /                              → Get all friends
    ├── GET    /?search=john                  → Search friends
    ├── GET    /stats                         → Get statistics
    ├── GET    /mutual/{other_uid}            → Get mutual friends
    ├── DELETE /{friend_uid}                  → Unfriend
    │
    └── Legacy (backward compatible)
        └── GET /{user_uid}
```

---

## Database Relationships

### Friend Request (Before Acceptance)
```cypher
// User A sends request to User B
MATCH (a:User {uid: "abc"})
MATCH (b:User {uid: "def"})
CREATE (a)-[:INVITED {
  status: "pending",
  message: "Hi!",
  created_at: datetime(),
  updated_at: datetime()
}]->(b)
```

### Friendship (After Acceptance)
```cypher
// User B accepts → Bidirectional friendship created
MATCH (a:User {uid: "abc"})
MATCH (b:User {uid: "def"})
MATCH (a)-[r:INVITED]->(b)
SET r.status = "accepted", r.updated_at = datetime()

CREATE (a)-[:CONTACT {created_at: datetime()}]->(b)
CREATE (b)-[:CONTACT {created_at: datetime()}]->(a)
```

### Get Friends
```cypher
// Get all friends of User A
MATCH (a:User {uid: "abc"})-[r:CONTACT]->(friend:User)
RETURN friend, r.created_at as friendship_since
ORDER BY friend.username
```

### Mutual Friends
```cypher
// Get mutual friends between User A and User B
MATCH (a:User {uid: "abc"})-[:CONTACT]->(mutual:User)<-[:CONTACT]-(b:User {uid: "def"})
RETURN mutual
```

---

## Code Organization

```
app/
├── models/
│   └── user.py
│       ├── User (StructuredNode)
│       ├── InvitationRel (StructuredRel)
│       └── ContactRel (StructuredRel)
│
├── schemas/
│   ├── invitation.py
│   │   ├── InvitationCreate
│   │   ├── InvitationResponse
│   │   ├── InvitationListResponse
│   │   └── InvitationActionResponse
│   │
│   └── contact.py
│       ├── ContactResponse
│       ├── ContactListResponse
│       ├── ContactStatsResponse
│       └── MutualFriendsResponse
│
├── crud/
│   ├── invitation.py
│   │   ├── send_invitation()
│   │   ├── respond_invitation()
│   │   ├── cancel_invitation()
│   │   ├── list_received_invitations()
│   │   ├── list_sent_invitations()
│   │   ├── count_pending_received()
│   │   └── count_pending_sent()
│   │
│   └── contact.py
│       ├── list_contacts()
│       ├── get_contact_count()
│       ├── is_friend()
│       ├── remove_contact()
│       ├── search_contacts()
│       └── get_mutual_friends()
│
└── routers/
    ├── invitation.py
    │   ├── send_friend_request()
    │   ├── get_received_invitations()
    │   ├── get_sent_invitations()
    │   ├── accept_friend_request()
    │   ├── decline_friend_request()
    │   └── cancel_friend_request()
    │
    └── contact.py
        ├── get_all_friends()
        ├── get_friend_stats()
        ├── get_mutual_friends()
        └── remove_friend()
```

---

## Security Flow

```
Request
    │
    ├─→ JWT Token in Authorization header
    │
Router
    │
    ├─→ get_current_user(token) dependency
    │   │
    │   ├─→ verify_access_token(token)
    │   │   │
    │   │   ├─→ Decode JWT
    │   │   ├─→ Verify signature
    │   │   ├─→ Check expiration
    │   │   └─→ Extract user_id
    │   │
    │   └─→ Return user_id
    │
CRUD
    │
    ├─→ Use authenticated user_id for all operations
    │
Neo4j
    │
    └─→ Execute graph queries
```

---

## Performance Characteristics

### Neo4j Advantages
- **O(1)** - Check if two users are friends
- **O(k)** - Get all friends (k = number of friends)
- **O(k₁ + k₂)** - Get mutual friends (k₁, k₂ = friend counts)
- **Fast** - Graph traversal is Neo4j's strength
- **Scalable** - Handles millions of relationships efficiently

### Caching Strategy (Recommended)
```
Cache Layer (Redis)
    ├─→ friends_list:{user_id} → List of friend UIDs (TTL: 5 min)
    ├─→ pending_requests:{user_id} → Count of pending (TTL: 1 min)
    └─→ friend_status:{user_id}:{other_id} → Boolean (TTL: 10 min)
```

---

**This architecture provides a scalable, maintainable, and performant friend system! 🚀**
