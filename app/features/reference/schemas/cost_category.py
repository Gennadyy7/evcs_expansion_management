from pydantic import BaseModel, ConfigDict, Field

from app.features.reference.constants import CostKind
from app.features.reference.schemas.base import TimestampedResponse

_CODE_PATTERN = r'^[A-Z0-9_]+$'


class CostCategoryBase(BaseModel):
    cost_kind: CostKind = Field(
        ...,
        description='Cost kind discriminator: CAPEX or OPEX',
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='Category code (e.g., "EVSE", "GRID", "ENERGY", "RENT")',
    )
    name_ru: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Category name in Russian',
    )


class CostCategoryCreate(CostCategoryBase):
    model_config = ConfigDict(extra='forbid')


class CostCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    cost_kind: CostKind | None = Field(
        None,
        description='New cost kind discriminator: CAPEX or OPEX',
    )
    code: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='New category code (e.g., "EVSE", "GRID")',
    )
    name_ru: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description='New category name in Russian',
    )


class CostCategoryResponse(CostCategoryBase, TimestampedResponse):
    category_id: int = Field(
        ...,
        gt=0,
        description='Unique cost category identifier',
    )
