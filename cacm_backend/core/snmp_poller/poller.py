"""
Core SNMP Poller — performs GET and WALK operations against a target host
and assembles structured PollResult objects.

Compatible with pysnmp v7+ (async API).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    get_cmd,
    walk_cmd,
    usmHMACMD5AuthProtocol,
    usmHMACSHAAuthProtocol,
    usmAesCfb128Protocol,
    usmDESPrivProtocol,
)

from .models import (
    CPUInfo,
    DeviceInfo,
    InterfaceInfo,
    PollResult,
    PollStatus,
    StorageInfo,
)
from .oids import (
    ADMIN_STATUS_MAP,
    HR_PROCESSOR_TABLE,
    HR_STORAGE_TABLE,
    HR_SYSTEM,
    IF_TABLE,
    IF_X_TABLE,
    OPER_STATUS_MAP,
    SYSTEM,
)

logger = logging.getLogger(__name__)


class SNMPError(Exception):
    """Raised when an SNMP operation fails."""


class SNMPPoller:
    """
    SNMP poller that queries a single host and returns structured JSON results.

    Supports SNMPv1, v2c (community string) and v3 (USM authentication).
    """

    def __init__(
        self,
        host: str,
        port: int = 161,
        community: str = "public",
        version: str = "v2c",
        timeout: int = 5,
        retries: int = 2,
        # SNMPv3 parameters
        username: Optional[str] = None,
        auth_key: Optional[str] = None,
        priv_key: Optional[str] = None,
        auth_protocol: str = "sha",
        priv_protocol: str = "aes",
    ):
        self.host = host
        self.port = port
        self.version = version
        self.timeout = timeout
        self.retries = retries
        self._engine = SnmpEngine()

        # Build authentication data
        if version == "v3":
            auth_proto = (
                usmHMACSHAAuthProtocol
                if auth_protocol.lower() == "sha"
                else usmHMACMD5AuthProtocol
            )
            priv_proto = (
                usmAesCfb128Protocol
                if priv_protocol.lower() == "aes"
                else usmDESPrivProtocol
            )
            self._auth_data = UsmUserData(
                username or "",
                authKey=auth_key,
                privKey=priv_key,
                authProtocol=auth_proto,
                privProtocol=priv_proto,
            )
        else:
            mp_model = 0 if version == "v1" else 1
            self._auth_data = CommunityData(community, mpModel=mp_model)

        # Transport is created lazily (async) in _get_transport()
        self._transport: Optional[UdpTransportTarget] = None

    async def _get_transport(self) -> UdpTransportTarget:
        """Create or return cached async UDP transport."""
        if self._transport is None:
            self._transport = await UdpTransportTarget.create(
                (self.host, self.port),
                timeout=self.timeout,
                retries=self.retries,
            )
        return self._transport

    # ── Low-Level Async SNMP Operations ──────────────────────────────────

    async def _get(self, *oids: str) -> dict[str, Any]:
        """SNMP GET for one or more scalar OIDs. Returns {oid_str: value}."""
        transport = await self._get_transport()
        obj_types = [ObjectType(ObjectIdentity(oid)) for oid in oids]

        error_indication, error_status, error_index, var_binds = await get_cmd(
            self._engine,
            self._auth_data,
            transport,
            ContextData(),
            *obj_types,
        )

        if error_indication:
            raise SNMPError(f"SNMP GET error: {error_indication}")
        if error_status:
            raise SNMPError(
                f"SNMP GET error: {error_status.prettyPrint()} at "
                f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
            )

        results = {}
        for var_bind in var_binds:
            oid_str = str(var_bind[0])
            results[oid_str] = self._cast_value(var_bind[1])
        return results

    async def _walk(self, oid: str) -> list[tuple[str, Any]]:
        """SNMP WALK of a table column. Returns [(full_oid, value), ...]."""
        transport = await self._get_transport()
        results = []

        async for error_indication, error_status, error_index, var_binds in walk_cmd(
            self._engine,
            self._auth_data,
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        ):
            if error_indication:
                logger.warning("SNMP WALK warning on %s: %s", oid, error_indication)
                break
            if error_status:
                logger.warning("SNMP WALK status error on %s: %s", oid, error_status)
                break
            for var_bind in var_binds:
                oid_str = str(var_bind[0])
                results.append((oid_str, self._cast_value(var_bind[1])))

        return results

    async def _walk_table(self, column_oids: dict[str, str]) -> dict[int, dict[str, Any]]:
        """
        Walk multiple columns of an SNMP table and pivot into rows keyed by index.
        Returns {row_index: {column_name: value, ...}}.
        """
        table: dict[int, dict[str, Any]] = {}

        for col_name, base_oid in column_oids.items():
            for full_oid, value in await self._walk(base_oid):
                suffix = full_oid[len(base_oid):].lstrip(".")
                try:
                    idx = int(suffix.split(".")[0])
                except (ValueError, IndexError):
                    continue
                table.setdefault(idx, {})[col_name] = value

        return table

    @staticmethod
    def _cast_value(value: Any) -> Any:
        """Convert pysnmp value objects to native Python types."""
        type_name = type(value).__name__
        if type_name in (
            "Integer", "Integer32", "Gauge32", "Counter32",
            "Counter64", "Unsigned32",
        ):
            return int(value)
        if type_name == "OctetString":
            try:
                return value.prettyPrint()
            except Exception:
                return str(value)
        if type_name == "ObjectIdentifier":
            return str(value)
        if type_name == "TimeTicks":
            return int(value)
        if type_name == "IpAddress":
            return value.prettyPrint()
        if hasattr(value, "prettyPrint"):
            return value.prettyPrint()
        return str(value)

    # ── High-Level Async Polling Methods ─────────────────────────────────

    async def async_poll(self) -> PollResult:
        """Full device poll: system info, interfaces, storage, CPU."""
        start = time.monotonic()
        result = PollResult(host=self.host, snmp_version=self.version)

        try:
            result.device = await self._poll_system_info()
            result.interfaces = await self._poll_interfaces()
            result.storage = await self._poll_storage()
            result.cpu = await self._poll_cpu()
            result.status = PollStatus.SUCCESS.value
        except SNMPError as exc:
            result.status = PollStatus.ERROR.value
            result.error = str(exc)
            logger.error("Poll failed for %s: %s", self.host, exc)
        except Exception as exc:
            result.status = PollStatus.ERROR.value
            result.error = f"Unexpected error: {exc}"
            logger.exception("Unexpected poll failure for %s", self.host)

        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    async def async_poll_system(self) -> PollResult:
        """Poll only system/device information."""
        start = time.monotonic()
        result = PollResult(host=self.host, snmp_version=self.version)
        try:
            result.device = await self._poll_system_info()
            result.status = PollStatus.SUCCESS.value
        except SNMPError as exc:
            result.status = PollStatus.ERROR.value
            result.error = str(exc)
        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    async def async_poll_interfaces(self) -> PollResult:
        """Poll only interface statistics."""
        start = time.monotonic()
        result = PollResult(host=self.host, snmp_version=self.version)
        try:
            result.interfaces = await self._poll_interfaces()
            result.status = PollStatus.SUCCESS.value
        except SNMPError as exc:
            result.status = PollStatus.ERROR.value
            result.error = str(exc)
        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    async def async_poll_custom(self, oids: dict[str, str]) -> PollResult:
        """Poll arbitrary OIDs by friendly name."""
        start = time.monotonic()
        result = PollResult(host=self.host, snmp_version=self.version)
        try:
            values = await self._get(*oids.values())
            oid_to_name = {v: k for k, v in oids.items()}
            for oid_str, val in values.items():
                clean = oid_str.lstrip(".")
                for orig_oid, name in oid_to_name.items():
                    if clean == orig_oid.lstrip(".") or clean.startswith(orig_oid.lstrip(".")):
                        result.custom[name] = val
                        break
                else:
                    result.custom[oid_str] = val
            result.status = PollStatus.SUCCESS.value
        except SNMPError as exc:
            result.status = PollStatus.ERROR.value
            result.error = str(exc)
        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    # ── Sync Convenience Wrappers ────────────────────────────────────────

    def poll(self) -> PollResult:
        """Synchronous full poll (wraps async_poll)."""
        return asyncio.run(self.async_poll())

    def poll_system(self) -> PollResult:
        """Synchronous system poll."""
        return asyncio.run(self.async_poll_system())

    def poll_interfaces(self) -> PollResult:
        """Synchronous interface poll."""
        return asyncio.run(self.async_poll_interfaces())

    def poll_custom(self, oids: dict[str, str]) -> PollResult:
        """Synchronous custom OID poll."""
        return asyncio.run(self.async_poll_custom(oids))

    # ── Internal Polling Helpers ─────────────────────────────────────────

    async def _poll_system_info(self) -> DeviceInfo:
        """Retrieve system group scalars and host-resource scalars."""
        data = await self._get(*SYSTEM.values())

        lookup = {}
        for oid_str, val in data.items():
            for name, defined_oid in SYSTEM.items():
                if oid_str.rstrip(".").endswith(defined_oid.rstrip(".")):
                    lookup[name] = val
                    break

        uptime_ticks = lookup.get("sysUpTime", 0)
        device = DeviceInfo(
            sys_name=str(lookup.get("sysName", "")),
            sys_descr=str(lookup.get("sysDescr", "")),
            sys_object_id=str(lookup.get("sysObjectID", "")),
            sys_uptime_ticks=int(uptime_ticks) if uptime_ticks else 0,
            sys_uptime_human=self._format_uptime(int(uptime_ticks) if uptime_ticks else 0),
            sys_contact=str(lookup.get("sysContact", "")),
            sys_location=str(lookup.get("sysLocation", "")),
            sys_services=int(lookup.get("sysServices", 0) or 0),
        )

        try:
            hr_data = await self._get(*HR_SYSTEM.values())
            hr_lookup = {}
            for oid_str, val in hr_data.items():
                for name, defined_oid in HR_SYSTEM.items():
                    if oid_str.rstrip(".").endswith(defined_oid.rstrip(".")):
                        hr_lookup[name] = val
                        break
            device.memory_total_kb = int(hr_lookup.get("hrMemorySize", 0) or 0)
            device.num_users = int(hr_lookup.get("hrSystemNumUsers", 0) or 0)
            device.num_processes = int(hr_lookup.get("hrSystemProcesses", 0) or 0)
        except Exception:
            logger.debug("Host-resource scalars not available on %s", self.host)

        return device

    async def _poll_interfaces(self) -> list[InterfaceInfo]:
        """Walk the ifTable and ifXTable, merge into InterfaceInfo list."""
        rows = await self._walk_table(IF_TABLE)

        try:
            x_rows = await self._walk_table(IF_X_TABLE)
            for idx, x_data in x_rows.items():
                if idx in rows:
                    rows[idx].update(x_data)
                else:
                    rows[idx] = x_data
        except Exception:
            logger.debug("ifXTable not available on %s", self.host)

        interfaces = []
        for idx, r in sorted(rows.items()):
            speed_raw = r.get("ifHighSpeed") or r.get("ifSpeed", 0)
            if r.get("ifHighSpeed"):
                speed_mbps = float(speed_raw)
            else:
                speed_mbps = float(speed_raw) / 1_000_000 if speed_raw else 0.0

            mac = r.get("ifPhysAddress", "")
            if mac and not any(c in mac for c in ":."):
                try:
                    mac = ":".join(f"{b:02x}" for b in bytes.fromhex(mac.replace("0x", "")))
                except Exception:
                    pass

            iface = InterfaceInfo(
                index=idx,
                name=str(r.get("ifName", r.get("ifDescr", f"if{idx}"))),
                description=str(r.get("ifDescr", "")),
                alias=str(r.get("ifAlias", "")),
                type=int(r.get("ifType", 0) or 0),
                mtu=int(r.get("ifMtu", 0) or 0),
                speed_mbps=speed_mbps,
                mac_address=str(mac),
                admin_status=ADMIN_STATUS_MAP.get(int(r.get("ifAdminStatus", 0) or 0), "unknown"),
                oper_status=OPER_STATUS_MAP.get(int(r.get("ifOperStatus", 0) or 0), "unknown"),
                last_change=int(r.get("ifLastChange", 0) or 0),
                in_octets=int(r.get("ifInOctets", 0) or 0),
                in_unicast_packets=int(r.get("ifInUcastPkts", 0) or 0),
                in_discards=int(r.get("ifInDiscards", 0) or 0),
                in_errors=int(r.get("ifInErrors", 0) or 0),
                out_octets=int(r.get("ifOutOctets", 0) or 0),
                out_unicast_packets=int(r.get("ifOutUcastPkts", 0) or 0),
                out_discards=int(r.get("ifOutDiscards", 0) or 0),
                out_errors=int(r.get("ifOutErrors", 0) or 0),
                hc_in_octets=int(r["ifHCInOctets"]) if "ifHCInOctets" in r else None,
                hc_out_octets=int(r["ifHCOutOctets"]) if "ifHCOutOctets" in r else None,
            )
            interfaces.append(iface)

        return interfaces

    async def _poll_storage(self) -> list[StorageInfo]:
        """Walk hrStorageTable and return storage entries."""
        try:
            rows = await self._walk_table(HR_STORAGE_TABLE)
        except Exception:
            logger.debug("hrStorageTable not available on %s", self.host)
            return []

        storage = []
        for idx, r in sorted(rows.items()):
            alloc = int(r.get("hrStorageAllocationUnits", 0) or 0)
            size = int(r.get("hrStorageSize", 0) or 0)
            used = int(r.get("hrStorageUsed", 0) or 0)
            total_bytes = size * alloc
            used_bytes = used * alloc
            pct = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0.0

            storage.append(StorageInfo(
                index=idx,
                description=str(r.get("hrStorageDescr", "")),
                allocation_units=alloc,
                total_bytes=total_bytes,
                used_bytes=used_bytes,
                percent_used=round(pct, 2),
            ))
        return storage

    async def _poll_cpu(self) -> list[CPUInfo]:
        """Walk hrProcessorTable and return CPU load entries."""
        try:
            rows = await self._walk_table(HR_PROCESSOR_TABLE)
        except Exception:
            logger.debug("hrProcessorTable not available on %s", self.host)
            return []

        return [
            CPUInfo(index=idx, load_percent=int(r.get("hrProcessorLoad", 0) or 0))
            for idx, r in sorted(rows.items())
        ]

    @staticmethod
    def _format_uptime(ticks: int) -> str:
        """Convert TimeTicks (1/100th seconds) to human-readable string."""
        total_seconds = ticks // 100
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)
