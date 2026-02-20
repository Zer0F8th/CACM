from __future__ import annotations
from uuid import UUID

from sqlmodel import select, func, or_, col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.asset import (
    Asset,
    AssetCreate,
    AssetUpdate,
    AssetListParams,
    AssetStatus,
    SystemType,
)


class AssetNotFoundError(Exception):
    def __init__(self, asset_id: UUID):
        self.asset_id = asset_id
        super().__init__(f"Asset {asset_id} not found")


class AssetValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: AssetCreate) -> Asset:
        # If an associated system type, validate the parent exists and is a BCS
        if (
            data.system_type != SystemType.BES_CYBER_SYSTEM
            and data.parent_bes_cyber_system_id is not None
        ):
            parent = await self.db.get(Asset, data.parent_bes_cyber_system_id)
            if parent is None:
                raise AssetValidationError(
                    f"Parent BES Cyber System {data.parent_bes_cyber_system_id} not found"
                )
            if parent.system_type != SystemType.BES_CYBER_SYSTEM:
                raise AssetValidationError(
                    f"Parent asset {parent.id} is not a BES Cyber System"
                )

        asset = Asset.model_validate(data)
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def get(self, asset_id: UUID) -> Asset:
        asset = await self.db.get(Asset, asset_id)
        if asset is None:
            raise AssetNotFoundError(asset_id)
        return asset

    async def list(self, params: AssetListParams) -> tuple[list[Asset], int]:
        query = select(Asset)
        count_query = select(func.count()).select_from(Asset)

        # Apply filters
        conditions = []
        if params.impact_level is not None:
            conditions.append(col(Asset.impact_level) == params.impact_level)
        if params.system_type is not None:
            conditions.append(col(Asset.system_type) == params.system_type)
        if params.device_class is not None:
            conditions.append(col(Asset.device_class) == params.device_class)
        if params.site is not None:
            conditions.append(col(Asset.site).ilike(f"%{params.site}%"))
        if params.status is not None:
            conditions.append(col(Asset.status) == params.status)
        if params.parent_bes_cyber_system_id is not None:
            conditions.append(
                col(Asset.parent_bes_cyber_system_id)
                == params.parent_bes_cyber_system_id
            )
        if params.search:
            search_term = f"%{params.search}%"
            conditions.append(
                or_(
                    col(Asset.name).ilike(search_term),
                    col(Asset.description).ilike(search_term),
                )
            )

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # Total count
        total_result = await self.db.exec(count_query)
        total = total_result.one()

        # Paginated results
        query = (
            query.order_by(col(Asset.name)).offset(params.offset).limit(params.limit)
        )
        result = await self.db.exec(query)
        assets = list(result.all())

        return assets, total

    async def update(self, asset_id: UUID, data: AssetUpdate) -> Asset:
        asset = await self.get(asset_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return asset

        asset.sqlmodel_update(update_data)

        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def decommission(self, asset_id: UUID) -> Asset:
        """
        Soft-delete: mark as decommissioned rather than removing.
        CIP-010-4 requires evidence retention for 3 calendar years,
        so we never hard-delete asset records.
        """
        asset = await self.get(asset_id)
        asset.status = AssetStatus.DECOMMISSIONED
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def get_associated_assets(self, bes_cyber_system_id: UUID) -> list[Asset]:
        """Get all EACMS, PACS, and PCA associated with a BES Cyber System."""
        parent = await self.get(bes_cyber_system_id)
        if parent.system_type != SystemType.BES_CYBER_SYSTEM:
            raise AssetValidationError(
                f"Asset {bes_cyber_system_id} is not a BES Cyber System"
            )

        query = (
            select(Asset)
            .where(col(Asset.parent_bes_cyber_system_id) == bes_cyber_system_id)
            .order_by(col(Asset.system_type), col(Asset.name))
        )
        result = await self.db.exec(query)
        return list(result.all())
