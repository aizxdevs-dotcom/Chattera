from app.models.person import Person
from app.schemas.person import PersonCreate, PersonResponse

def create_person(data: PersonCreate):
    person = Person(name=data.name, age=data.age).save()
    return PersonResponse.from_orm(person)

def get_person(name: str):
    person = Person.nodes.get(name=name)
    return PersonResponse.from_orm(person)

def list_persons():
    return [PersonResponse.from_orm(p) for p in Person.nodes]

def update_person(name: str, data: PersonCreate):
    person = Person.nodes.get(name=name)
    person.age = data.age
    person.save()
    return PersonResponse.from_orm(person)

def delete_person(name: str):
    person = Person.nodes.get(name=name)
    person.delete()
    return {"message": f"Deleted {name}"}

# 🔹 Add friendship
def add_friend(person_name: str, friend_name: str):
    person = Person.nodes.get(name=person_name)
    friend = Person.nodes.get(name=friend_name)
    person.friends.connect(friend)
    return {"message": f"{person_name} is now friends with {friend_name}"}
