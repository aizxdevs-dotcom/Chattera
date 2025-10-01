from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo

class File(StructuredNode):
    file_id = StringProperty(unique_index=True, required=True)
    url = StringProperty(required=True)
    file_type = StringProperty(required=True)
    size = IntegerProperty(required=True)

    # Use dotted path for robustness
    attached_to_message = RelationshipTo("app.models.message.Message", "ATTACHED_TO")