from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo

class Person(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    age = IntegerProperty(required=True)

    friends = RelationshipTo("Person", "FRIEND")
