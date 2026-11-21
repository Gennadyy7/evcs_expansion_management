from pydantic import BaseModel, ConfigDict, Field

from app.features.reference.schemas.base import TimestampedResponse

_CODE_PATTERN = r'^[A-Z0-9_]+$'


class SiteTypeBase(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='Site type code (e.g., "CITY", "HIGHWAY", "MALL")',
    )
    name_ru: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Site type name in Russian',
    )


class SiteTypeCreate(SiteTypeBase):
    model_config = ConfigDict(extra='forbid')


class SiteTypeUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='New site type code (e.g., "CITY", "HIGHWAY")',
    )
    name_ru: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description='New site type name in Russian',
    )


class SiteTypeResponse(SiteTypeBase, TimestampedResponse):
    site_type_id: int = Field(
        ...,
        gt=0,
        description='Unique site type identifier',
    )
