"""
SNMP Poller Module
==================
A Python module for SNMP polling of network assets, returning structured JSON
output suitable for API consumption.

Dependencies:
    pip install pysnmp pysnmp-mibs

Usage:
    from snmp_poller import SNMPPoller

    poller = SNMPPoller("192.168.1.1", community="public")
    result = poller.poll()          # Full device poll
    result = poller.poll_system()   # System info only
    result = poller.poll_interfaces() # Interface stats only
"""
from .poller import SNMPPoller
from .models import PollResult, DeviceInfo, InterfaceInfo

__all__ = ["SNMPPoller", "PollResult", "DeviceInfo", "InterfaceInfo"]
__version__ = "1.0.0"

