from pydantic import BaseModel, ConfigDict, Field

from app.features.reference.schemas.base import TimestampedResponse

_CODE_PATTERN = r'^[A-Z0-9_]+$'


class ConnectorTypeBase(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='Connector code (e.g., "TYPE2", "CCS2", "CHADEMO")',
    )
    name_ru: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Connector type name in Russian',
    )


class ConnectorTypeCreate(ConnectorTypeBase):
    model_config = ConfigDict(extra='forbid')


class ConnectorTypeUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='New connector code (e.g., "TYPE2", "CCS2")',
    )
    name_ru: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description='New connector type name in Russian',
    )


class ConnectorTypeResponse(ConnectorTypeBase, TimestampedResponse):
    connector_type_id: int = Field(
        ...,
        gt=0,
        description='Unique connector type identifier',
    )
