from pydantic import BaseModel, ConfigDict, Field

from app.features.reference.schemas.base import TimestampedResponse

_CODE_PATTERN = r'^[A-Z0-9_]+$'


class RegionBase(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='Short region code (e.g., "MINSK_OBL")',
    )
    name_ru: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Full region name in Russian',
    )
    parent_region_id: int | None = Field(
        None,
        gt=0,
        description='Parent region ID for hierarchy (NULL for root regions)',
    )


class RegionCreate(RegionBase):
    model_config = ConfigDict(extra='forbid')


class RegionUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='New region code (e.g., "MINSK_OBL")',
    )
    name_ru: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description='New region name in Russian',
    )
    parent_region_id: int | None = Field(
        None,
        gt=0,
        description='New parent region ID (NULL for root regions)',
    )


class RegionResponse(RegionBase, TimestampedResponse):
    region_id: int = Field(..., gt=0, description='Unique region identifier')


class RegionTree(RegionResponse):
    children: list[RegionTree] = Field(
        default_factory=list,
        description='Child regions',
    )


# Rebuild model for recursive reference support (Pydantic v2 requirement)
RegionTree.model_rebuild()
