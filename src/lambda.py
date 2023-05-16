import uuid

def get_key(event, context):
    return { "key": str(uuid.uuid5(uuid.NAMESPACE_X500, 'key')) }
