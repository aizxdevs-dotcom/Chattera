from pydantic import BaseModel
from typing import List, Optional

class PersonCreate(BaseModel):
    name: str
    age: int

class PersonResponse(BaseModel):
    id: str
    name: str
    age: int
    friends: Optional[List[str]] = []

    @classmethod
    def from_orm(cls, person):
        return cls(
           id=person.element_id,
            name=person.name,
            age=person.age,
            friends=[f.name for f in person.friends.all()]  # ✅ use .all()
        )