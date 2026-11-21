from pydantic import BaseModel, ConfigDict, Field

from app.features.reference.schemas.base import TimestampedResponse

_CODE_PATTERN = r'^[A-Z0-9_]+$'


class ProjectStageBase(BaseModel):
    stage_no: int = Field(
        ...,
        ge=0,
        le=13,
        description='Stage number (0-13), fixed sequence',
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='Stage code (e.g., "PROGRAM", "SITE", "SURVEY")',
    )
    name_ru: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Stage name in Russian',
    )
    is_milestone: bool = Field(
        True,
        description='Whether this stage is a milestone (gate approval required)',
    )


class ProjectStageCreate(ProjectStageBase):
    model_config = ConfigDict(extra='forbid')


class ProjectStageUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=_CODE_PATTERN,
        description='New stage code (e.g., "PROGRAM", "SITE")',
    )
    name_ru: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description='New stage name in Russian',
    )
    is_milestone: bool | None = Field(
        None,
        description='New milestone flag (gate approval required)',
    )


class ProjectStageResponse(ProjectStageBase, TimestampedResponse):
    pass
