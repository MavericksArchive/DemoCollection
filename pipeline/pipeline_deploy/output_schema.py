from marshmallow import Schema, fields


class IntentionSchemaFull(Schema):
    goal = fields.Str()
    main_question = fields.Str()
    major_problem = fields.Str()
    situation = fields.Str()
    summary = fields.Str()
    extracted_entity = fields.List(fields.Str())
    system_message = fields.List(fields.Str())
    steps = fields.List(fields.Str())
    solutions = fields.List(fields.Str())

        
class IntentionSchema(Schema):
    extracted_entity = fields.List(fields.Str())
    system_message = fields.List(fields.Str())
    steps = fields.List(fields.Str())
    solutions = fields.List(fields.Str())
    

class PapyrusSchema(Schema):
    regex = fields.List(fields.Dict)
    # workaround = fields.Str()
    solutions = fields.List(fields.Str())


class OutputSchema(Schema):
    conversation_id = fields.Str()
    message_id = fields.Str()
    source = fields.Str()
    dryrun = fields.Str()
    debug = fields.Str()
    intention = fields.Nested(IntentionSchemaFull())
    user_response = fields.Nested(PapyrusSchema())

class OutputSchemaIntention(Schema):
    conversation_id = fields.Str()
    message_id = fields.Str()
    source = fields.Str()
    dryrun = fields.Str()
    debug = fields.Str()
    intention = fields.Nested(IntentionSchema())
    user_response = fields.Nested(PapyrusSchema())
