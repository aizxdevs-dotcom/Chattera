from fastapi import APIRouter
from app.schemas.person import PersonCreate, PersonResponse
from app.crud import person as crud_person

router = APIRouter(prefix="/persons", tags=["Persons"])

@router.post("/", response_model=PersonResponse)
def create_person(person: PersonCreate):
    return crud_person.create_person(person)

@router.get("/{name}", response_model=PersonResponse)
def get_person(name: str):
    return crud_person.get_person(name)

@router.get("/", response_model=list[PersonResponse])
def list_persons():
    return crud_person.list_persons()

@router.put("/{name}", response_model=PersonResponse)
def update_person(name: str, data: PersonCreate):
    return crud_person.update_person(name, data)

@router.delete("/{name}")
def delete_person(name: str):
    return crud_person.delete_person(name)

# 🔹 Add friendship
@router.post("/{name}/friends/{friend_name}")
def add_friend(name: str, friend_name: str):
    return crud_person.add_friend(name, friend_name)
