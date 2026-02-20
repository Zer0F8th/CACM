import enum
from typing import Optional
import uuid as uuid_mod
from datetime import datetime

from pydantic import field_validator
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime
from sqlalchemy import Enum as SAEnum, Text, func


class ImpactLevel(str, enum.Enum):
    """BES Cyber System impact rating per CIP-002 categorization."""

    HIGH = "high"
    MEDIUM = "medium"


class SystemType(str, enum.Enum):
    """
    Role of this asset relative to CIP-010-4 applicability.
    A BES Cyber System is the primary system; EACMS, PACS, and PCA
    are associated systems with varying requirement applicability.
    """

    BES_CYBER_SYSTEM = "bes_cyber_system"
    EACMS = "eacms"
    PACS = "pacs"
    PCA = "pca"


class DeviceClass(str, enum.Enum):
    """
    Determines collection strategy.
    IT systems (Windows/Linux) support agent-based collection.
    OT devices typically require agentless/signature-based approaches.
    """

    WINDOWS = "windows"
    LINUX = "linux"
    NETWORK_DEVICE = "network_device"
    FIREWALL = "firewall"
    RELAY = "relay"
    RTU = "rtu"
    PLC = "plc"
    HMI = "hmi"
    HISTORIAN = "historian"
    OTHER_OT = "other_ot"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    DECOMMISSIONED = "decommissioned"
    PENDING = "pending"


class AssetBase(SQLModel):
    """Shared fields across all asset representations."""

    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # CIP classification
    impact_level: ImpactLevel = Field(
        sa_column=Column(
            SAEnum(ImpactLevel, name="impact_level_enum"),
            nullable=False,
            index=True,
        )
    )
    system_type: SystemType = Field(
        sa_column=Column(
            SAEnum(SystemType, name="system_type_enum"),
            nullable=False,
            index=True,
        )
    )
    device_class: DeviceClass = Field(
        sa_column=Column(
            SAEnum(DeviceClass, name="device_class_enum"),
            nullable=False,
            index=True,
        )
    )

    # Association to parent BES Cyber System
    parent_bes_cyber_system_id: uuid_mod.UUID | None = Field(
        default=None, foreign_key="assets.id", index=True
    )

    # Network / Location
    ip_address: str | None = Field(default=None, max_length=45)
    mac_address: str | None = Field(default=None, max_length=17)
    site: str | None = Field(default=None, max_length=255, index=True)
    location: str | None = Field(default=None, max_length=255)
    has_external_routable_connectivity: bool = Field(default=False)

    # Status / Lifecycle
    status: AssetStatus = Field(
        default=AssetStatus.PENDING,
        sa_column=Column(
            SAEnum(AssetStatus, name="asset_status_enum"),
            nullable=False,
            index=True,
            default=AssetStatus.PENDING,
        ),
    )


class Asset(AssetBase, table=True):
    """Database table model for Cyber Assets."""

    __tablename__ = "assets"

    id: uuid_mod.UUID = Field(default_factory=uuid_mod.uuid4, primary_key=True)

    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        ),
    )

    # Self-referential relationship
    parent_bes_cyber_system: Optional["Asset"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Asset.id",
            "foreign_keys": "[Asset.parent_bes_cyber_system_id]",
        }
    )


class AssetCreate(SQLModel):
    """Request body for registering a new Cyber Asset."""

    name: str = Field(
        min_length=1, max_length=255, schema_extra={"examples": ["SUB-A-RTU-01"]}
    )
    description: str | None = Field(
        None, schema_extra={"examples": ["Primary RTU at Substation Alpha"]}
    )

    impact_level: ImpactLevel
    system_type: SystemType
    device_class: DeviceClass
    parent_bes_cyber_system_id: uuid_mod.UUID | None = Field(
        None,
        description=(
            "For EACMS, PACS, or PCA assets, the UUID of the parent BES Cyber System "
            "this asset is associated with. NULL for BES Cyber System assets themselves."
        ),
    )

    ip_address: str | None = Field(None, schema_extra={"examples": ["10.10.50.12"]})
    mac_address: str | None = Field(
        None, schema_extra={"examples": ["00:1A:2B:3C:4D:5E"]}
    )
    site: str | None = Field(None, schema_extra={"examples": ["Substation Alpha"]})
    location: str | None = Field(
        None, schema_extra={"examples": ["Control House, Rack 3"]}
    )
    has_external_routable_connectivity: bool = False

    @field_validator("parent_bes_cyber_system_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v


class AssetPublic(AssetBase):
    """Full asset response including id and timestamps."""

    id: uuid_mod.UUID
    created_at: datetime
    updated_at: datetime


class AssetSummary(SQLModel):
    """Compact asset representation for list endpoints."""

    id: uuid_mod.UUID
    name: str
    impact_level: ImpactLevel
    system_type: SystemType
    device_class: DeviceClass
    site: str | None
    status: AssetStatus


class AssetUpdate(SQLModel):
    """PATCH body — all fields optional, only provided fields are updated."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    impact_level: ImpactLevel | None = None
    system_type: SystemType | None = None
    device_class: DeviceClass | None = None
    parent_bes_cyber_system_id: uuid_mod.UUID | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    site: str | None = None
    location: str | None = None
    has_external_routable_connectivity: bool | None = None
    status: AssetStatus | None = None

    @field_validator("parent_bes_cyber_system_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v


class AssetListParams(SQLModel):
    """Query parameters for listing/filtering assets."""

    impact_level: ImpactLevel | None = None
    system_type: SystemType | None = None
    device_class: DeviceClass | None = None
    site: str | None = None
    status: AssetStatus | None = None
    parent_bes_cyber_system_id: uuid_mod.UUID | None = None
    search: str | None = Field(None, description="Search name or description")

    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


class AssetListResponse(SQLModel):
    """Paginated list response."""

    items: list[AssetSummary]
    total: int
    offset: int
    limit: int
