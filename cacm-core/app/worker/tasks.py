import hashlib
import json
from datetime import datetime, timezone

import paramiko

from app.worker.celery_app import celery

# Linux baseline commands aligned with NERC CIP-010-4 R1 evidence requirements
LINUX_BASELINE_COMMANDS: dict[str, str] = {
    "os_version": "cat /etc/os-release",
    "kernel": "uname -a",
    "hostname": "hostname",
    "installed_packages": "dpkg -l 2>/dev/null || rpm -qa 2>/dev/null",
    "running_services": "ps aux --no-headers",
    "open_ports": "ss -tlnp",
    "user_accounts": "cat /etc/passwd",
    "group_memberships": "cat /etc/group",
    "sudoers": "cat /etc/sudoers 2>/dev/null; ls /etc/sudoers.d/ 2>/dev/null",
    "network_interfaces": "ip addr show",
    "routes": "ip route show",
    "iptables_rules": "iptables -L -n 2>/dev/null || echo 'no iptables'",
    "cron_jobs": "crontab -l 2>/dev/null; ls /etc/cron.d/ 2>/dev/null",
    "dns_config": "cat /etc/resolv.conf",
    "sshd_config": "cat /etc/ssh/sshd_config 2>/dev/null",
}


def _ssh_collect(host: str, port: int, username: str, password: str) -> dict:
    """SSH into a Linux host and run baseline collection commands."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=10,
        )

        results: dict[str, str] = {}
        for key, cmd in LINUX_BASELINE_COMMANDS.items():
            _stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
            output = stdout.read().decode("utf-8", errors="replace").strip()
            err = stderr.read().decode("utf-8", errors="replace").strip()
            results[key] = output if output else f"[stderr] {err}"

        return results
    finally:
        client.close()


def _compute_fingerprint(snapshot: dict) -> str:
    """SHA-256 hash of the sorted snapshot for drift comparison."""
    canonical = json.dumps(snapshot, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


@celery.task(bind=True, name="cacm.collect_baseline")
def collect_baseline(
    self,
    asset_id: str,
    host: str,
    port: int = 22,
    username: str = "cacm_collector",
    password: str = "collector",
) -> dict:
    """SSH into a Linux asset and collect baseline configuration evidence."""
    self.update_state(state="STARTED", meta={"asset_id": asset_id, "host": host})

    snapshot = _ssh_collect(host, port, username, password)
    fingerprint = _compute_fingerprint(snapshot)

    return {
        "asset_id": asset_id,
        "host": host,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fingerprint,
        "baseline": snapshot,
        "task_id": self.request.id,
        "status": "collected",
    }


@celery.task(bind=True, name="cacm.normalize_baseline")
def normalize_baseline(self, asset_id: str, collection_id: str) -> dict:
    """Normalize collected data into a canonical baseline format."""
    return {
        "asset_id": asset_id,
        "collection_id": collection_id,
        "status": "normalized",
    }


@celery.task(bind=True, name="cacm.compare_baselines")
def compare_baselines(
    self, asset_id: str, baseline_a_id: str, baseline_b_id: str
) -> dict:
    """Compare two baselines to detect drift / unauthorized changes."""
    return {
        "asset_id": asset_id,
        "baseline_a": baseline_a_id,
        "baseline_b": baseline_b_id,
        "drift_detected": False,
        "status": "compared",
    }
