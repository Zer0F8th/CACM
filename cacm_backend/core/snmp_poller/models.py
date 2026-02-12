"""
Data models for SNMP poll results.
Uses dataclasses for zero-dependency structured output with JSON serialization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class PollStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"


# ─── Interface Model ────────────────────────────────────────────────────────

@dataclass
class InterfaceInfo:
    """Single network interface statistics."""
    index: int
    name: str
    description: str = ""
    alias: str = ""
    type: int = 0
    mtu: int = 0
    speed_mbps: float = 0.0
    mac_address: str = ""
    admin_status: str = "unknown"
    oper_status: str = "unknown"
    last_change: int = 0
    # Traffic counters
    in_octets: int = 0
    in_unicast_packets: int = 0
    in_discards: int = 0
    in_errors: int = 0
    out_octets: int = 0
    out_unicast_packets: int = 0
    out_discards: int = 0
    out_errors: int = 0
    # 64-bit counters (preferred)
    hc_in_octets: Optional[int] = None
    hc_out_octets: Optional[int] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        # Remove None HC counters if not available
        d = {k: v for k, v in d.items() if v is not None}
        return d


# ─── Storage Model ──────────────────────────────────────────────────────────

@dataclass
class StorageInfo:
    """Storage/filesystem entry from HOST-RESOURCES-MIB."""
    index: int
    description: str
    allocation_units: int = 0
    total_bytes: int = 0
    used_bytes: int = 0
    percent_used: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ─── CPU Model ──────────────────────────────────────────────────────────────

@dataclass
class CPUInfo:
    """Processor load entry from HOST-RESOURCES-MIB."""
    index: int
    load_percent: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Device / System Model ──────────────────────────────────────────────────

@dataclass
class DeviceInfo:
    """System-level device information."""
    sys_name: str = ""
    sys_descr: str = ""
    sys_object_id: str = ""
    sys_uptime_ticks: int = 0
    sys_uptime_human: str = ""
    sys_contact: str = ""
    sys_location: str = ""
    sys_services: int = 0
    # Host resources
    memory_total_kb: int = 0
    num_users: int = 0
    num_processes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Top-Level Poll Result ──────────────────────────────────────────────────

@dataclass
class PollResult:
    """
    Complete structured result of an SNMP poll.
    Designed for direct serialization to a JSON API response.
    """
    host: str
    status: str = PollStatus.SUCCESS.value
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    duration_ms: float = 0.0
    snmp_version: str = "v2c"
    error: Optional[str] = None
    device: Optional[DeviceInfo] = None
    interfaces: list[InterfaceInfo] = field(default_factory=list)
    storage: list[StorageInfo] = field(default_factory=list)
    cpu: list[CPUInfo] = field(default_factory=list)
    # Raw/custom OID results
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to a clean dictionary suitable for JSON serialization."""
        result = {
            "host": self.host,
            "status": self.status,
            "timestamp": self.timestamp,
            "duration_ms": round(self.duration_ms, 2),
            "snmp_version": self.snmp_version,
        }
        if self.error:
            result["error"] = self.error
        if self.device:
            result["device"] = self.device.to_dict()
        if self.interfaces:
            result["interfaces"] = [iface.to_dict() for iface in self.interfaces]
        if self.storage:
            result["storage"] = [s.to_dict() for s in self.storage]
        if self.cpu:
            result["cpu"] = [c.to_dict() for c in self.cpu]
        if self.custom:
            result["custom"] = self.custom
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_json_bytes(self) -> bytes:
        """Serialize to compact JSON bytes (for HTTP responses)."""
        return json.dumps(self.to_dict(), separators=(",", ":"), default=str).encode()
