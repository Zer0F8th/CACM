from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.db import get_db
from app.models.asset import (
    ImpactLevel,
    SystemType,
    DeviceClass,
    AssetStatus,
    AssetCreate,
    AssetUpdate,
    AssetListParams,
    AssetPublic,
    AssetSummary,
    AssetListResponse,
)
from app.services.asset_service import (
    AssetService,
    AssetNotFoundError,
    AssetValidationError,
)

router = APIRouter(prefix="/assets", tags=["Assets"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AssetService:
    return AssetService(db)


# ── List / Search ────────────────────────────────────────────


@router.get("", response_model=AssetListResponse)
async def list_assets(
    impact_level: ImpactLevel | None = None,
    system_type: SystemType | None = None,
    device_class: DeviceClass | None = None,
    site: str | None = None,
    status: AssetStatus | None = None,
    parent_bes_cyber_system_id: UUID | None = None,
    search: str | None = Query(None, description="Search name or description"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: AssetService = Depends(_get_service),
):
    """
    List and filter Cyber Assets.

    Supports filtering by CIP classification (impact level, system type,
    device class), site, status, and parent BES Cyber System. The `search`
    parameter performs a case-insensitive match against name and description.
    """
    params = AssetListParams(
        impact_level=impact_level,
        system_type=system_type,
        device_class=device_class,
        site=site,
        status=status,
        parent_bes_cyber_system_id=parent_bes_cyber_system_id,
        search=search,
        offset=offset,
        limit=limit,
    )
    assets, total = await service.list(params)
    return AssetListResponse(
        items=[AssetSummary.model_validate(a) for a in assets],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


# ── Create ───────────────────────────────────────────────────


@router.post("", response_model=AssetPublic, status_code=201)
async def create_asset(
    data: AssetCreate,
    service: AssetService = Depends(_get_service),
):
    """
    Register a new Cyber Asset.

    For EACMS, PACS, or PCA assets, provide the `parent_bes_cyber_system_id`
    to link the asset to its parent BES Cyber System. BES Cyber System assets
    should not have a parent.
    """
    try:
        asset = await service.create(data)
    except AssetValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    return asset


# ── Get Detail ───────────────────────────────────────────────


@router.get("/{asset_id}", response_model=AssetPublic)
async def get_asset(
    asset_id: UUID,
    service: AssetService = Depends(_get_service),
):
    """Retrieve a single Cyber Asset by ID."""
    try:
        asset = await service.get(asset_id)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# ── Update ───────────────────────────────────────────────────


@router.patch("/{asset_id}", response_model=AssetPublic)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    service: AssetService = Depends(_get_service),
):
    """
    Partially update a Cyber Asset.

    Only provided fields are updated. Changing `impact_level` or `system_type`
    may affect which CIP-010-4 requirements apply to this asset.
    """
    try:
        asset = await service.update(asset_id, data)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    except AssetValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    return asset


# ── Decommission (soft delete) ───────────────────────────────


@router.delete("/{asset_id}", response_model=AssetPublic)
async def decommission_asset(
    asset_id: UUID,
    service: AssetService = Depends(_get_service),
):
    """
    Decommission a Cyber Asset.

    This performs a soft delete (status -> decommissioned) rather than
    removing the record, since CIP-010-4 Section C.1.2 requires evidence
    retention for three calendar years.
    """
    try:
        asset = await service.decommission(asset_id)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# ── Associated Assets ────────────────────────────────────────


@router.get("/{asset_id}/associated", response_model=list[AssetSummary])
async def get_associated_assets(
    asset_id: UUID,
    service: AssetService = Depends(_get_service),
):
    """
    Get all EACMS, PACS, and PCA associated with a BES Cyber System.

    This is useful for understanding the full scope of assets to which
    CIP-010-4 requirements apply for a given BES Cyber System.
    """
    try:
        assets = await service.get_associated_assets(asset_id)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    except AssetValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    return [AssetSummary.model_validate(a) for a in assets]
