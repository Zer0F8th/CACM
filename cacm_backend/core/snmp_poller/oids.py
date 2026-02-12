"""
Standard SNMP OID definitions for common device information.
Organized by MIB group for clarity.
"""

# ─── SNMPv2-MIB / System Group ──────────────────────────────────────────────
SYSTEM = {
    "sysDescr":     "1.3.6.1.2.1.1.1.0",
    "sysObjectID":  "1.3.6.1.2.1.1.2.0",
    "sysUpTime":    "1.3.6.1.2.1.1.3.0",
    "sysContact":   "1.3.6.1.2.1.1.4.0",
    "sysName":      "1.3.6.1.2.1.1.5.0",
    "sysLocation":  "1.3.6.1.2.1.1.6.0",
    "sysServices":  "1.3.6.1.2.1.1.7.0",
}

# ─── IF-MIB / Interface Table ────────────────────────────────────────────────
IF_TABLE = {
    "ifIndex":          "1.3.6.1.2.1.2.2.1.1",
    "ifDescr":          "1.3.6.1.2.1.2.2.1.2",
    "ifType":           "1.3.6.1.2.1.2.2.1.3",
    "ifMtu":            "1.3.6.1.2.1.2.2.1.4",
    "ifSpeed":          "1.3.6.1.2.1.2.2.1.5",
    "ifPhysAddress":    "1.3.6.1.2.1.2.2.1.6",
    "ifAdminStatus":    "1.3.6.1.2.1.2.2.1.7",
    "ifOperStatus":     "1.3.6.1.2.1.2.2.1.8",
    "ifLastChange":     "1.3.6.1.2.1.2.2.1.9",
    "ifInOctets":       "1.3.6.1.2.1.2.2.1.10",
    "ifInUcastPkts":    "1.3.6.1.2.1.2.2.1.11",
    "ifInDiscards":     "1.3.6.1.2.1.2.2.1.13",
    "ifInErrors":       "1.3.6.1.2.1.2.2.1.14",
    "ifOutOctets":      "1.3.6.1.2.1.2.2.1.16",
    "ifOutUcastPkts":   "1.3.6.1.2.1.2.2.1.17",
    "ifOutDiscards":    "1.3.6.1.2.1.2.2.1.19",
    "ifOutErrors":      "1.3.6.1.2.1.2.2.1.20",
}

# ─── IF-MIB / ifXTable (64-bit counters) ────────────────────────────────────
IF_X_TABLE = {
    "ifName":           "1.3.6.1.2.1.31.1.1.1.1",
    "ifHCInOctets":     "1.3.6.1.2.1.31.1.1.1.6",
    "ifHCOutOctets":    "1.3.6.1.2.1.31.1.1.1.10",
    "ifHighSpeed":      "1.3.6.1.2.1.31.1.1.1.15",
    "ifAlias":          "1.3.6.1.2.1.31.1.1.1.18",
}

# ─── HOST-RESOURCES-MIB ─────────────────────────────────────────────────────
HR_SYSTEM = {
    "hrSystemUptime":       "1.3.6.1.2.1.25.1.1.0",
    "hrSystemNumUsers":     "1.3.6.1.2.1.25.1.5.0",
    "hrSystemProcesses":    "1.3.6.1.2.1.25.1.6.0",
    "hrMemorySize":         "1.3.6.1.2.1.25.2.2.0",
}

HR_STORAGE_TABLE = {
    "hrStorageIndex":       "1.3.6.1.2.1.25.2.3.1.1",
    "hrStorageDescr":       "1.3.6.1.2.1.25.2.3.1.3",
    "hrStorageAllocationUnits": "1.3.6.1.2.1.25.2.3.1.4",
    "hrStorageSize":        "1.3.6.1.2.1.25.2.3.1.5",
    "hrStorageUsed":        "1.3.6.1.2.1.25.2.3.1.6",
}

HR_PROCESSOR_TABLE = {
    "hrProcessorLoad":      "1.3.6.1.2.1.25.3.3.1.2",
}

# ─── IP-MIB ─────────────────────────────────────────────────────────────────
IP_ADDR_TABLE = {
    "ipAdEntAddr":      "1.3.6.1.2.1.4.20.1.1",
    "ipAdEntIfIndex":   "1.3.6.1.2.1.4.20.1.2",
    "ipAdEntNetMask":   "1.3.6.1.2.1.4.20.1.3",
}

# ─── Admin/Oper status mappings ─────────────────────────────────────────────
ADMIN_STATUS_MAP = {1: "up", 2: "down", 3: "testing"}
OPER_STATUS_MAP = {
    1: "up", 2: "down", 3: "testing", 4: "unknown",
    5: "dormant", 6: "notPresent", 7: "lowerLayerDown",
}
