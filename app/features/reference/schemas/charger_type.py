from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features.reference.schemas.base import TimestampedResponse

# Matches DB CHECK constraint
ChargerTypeCode = Literal['AC', 'HYBRID', 'DC', 'OTHER']


class ChargerTypeBase(BaseModel):
    code: ChargerTypeCode = Field(
        ...,
        description='Charger type code: AC, HYBRID, DC, or OTHER',
    )
    name_ru: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Charger type name in Russian',
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description='Optional detailed description',
    )


class ChargerTypeCreate(ChargerTypeBase):
    model_config = ConfigDict(extra='forbid')


class ChargerTypeUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: ChargerTypeCode | None = Field(
        None,
        description='New charger type code: AC, HYBRID, DC, or OTHER',
    )
    name_ru: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description='New charger type name in Russian',
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description='New detailed description',
    )


class ChargerTypeResponse(ChargerTypeBase, TimestampedResponse):
    charger_type_id: int = Field(
        ...,
        gt=0,
        description='Unique charger type identifier',
    )
