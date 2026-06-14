from datetime import datetime
from uuid import UUID

from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Schema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=AliasGenerator(validation_alias=to_camel),
        extra="ignore",
    )


class RequestSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=to_camel),
        extra="ignore",
    )


class ResponseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        extra="ignore",
    )


class BaseModelResponse(ResponseSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
