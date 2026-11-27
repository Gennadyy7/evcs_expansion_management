from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.features.core.constants import OrganizationKind
from app.features.reference.schemas.base import TimestampedResponse


class OrganizationBase(BaseModel):
    legal_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description='Official legal name of the organization',
    )
    registration_code: str | None = Field(
        None,
        max_length=50,
        description='State registration code (UNP, EIN, etc.)',
    )
    organization_kind: OrganizationKind = Field(
        default=OrganizationKind.OTHER,
        description='Organization type: owner, contractor, vendor, utility, other',
    )


class OrganizationCreate(OrganizationBase):
    model_config = ConfigDict(extra='forbid')


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    legal_name: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description='New official legal name',
    )
    registration_code: str | None = Field(
        None,
        max_length=50,
        description='New state registration code (null to clear)',
    )
    organization_kind: OrganizationKind | None = Field(
        None,
        description='New organization type',
    )


class OrganizationResponse(OrganizationBase, TimestampedResponse):
    organization_id: UUID = Field(
        ...,
        description='Unique organization identifier',
    )
