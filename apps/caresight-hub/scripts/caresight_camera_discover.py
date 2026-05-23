#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a CareSight local RTSP camera config from an owner-specified host."
    )
    parser.add_argument("--host", help="Owner-authorized local camera IP or hostname.")
    parser.add_argument("--subnet", help="Owner-authorized local subnet to scan, for example 192.168.1.0/24.")
    parser.add_argument("--allow-lan-scan", action="store_true", help="Required with --subnet.")
    parser.add_argument("--max-hosts", type=int, default=256)
    parser.add_argument("--scan-timeout-seconds", type=float, default=0.25)
    parser.add_argument("--scan-workers", type=int, default=64)
    parser.add_argument("--progress-every", type=int, default=32)
    parser.add_argument("--include-arp", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--camera-id", default="discovered_rtsp_camera")
    parser.add_argument("--name", default="Discovered RTSP Camera")
    parser.add_argument("--room-id", default="living_room")
    parser.add_argument("--room-label", default="Living Room")
    parser.add_argument("--rtsp-port", type=int, default=554)
    parser.add_argument("--onvif-port", type=int, default=2020)
    parser.add_argument(
        "--discovery-ports",
        default="554,8554,2020,80,443,8080,8000,5000,8899",
        help="Comma-separated ports checked during --subnet discovery.",
    )
    parser.add_argument("--stream", choices=["stream1", "stream2"], default="stream1")
    parser.add_argument("--username", default="camera-user")
    parser.add_argument("--password-placeholder", default="replace-with-camera-password")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=float, default=2.0)
    parser.add_argument("--skip-reachability", action="store_true")
    parser.add_argument("--write-config", help="Optional ignored local config path to write.")
    args = parser.parse_args()
    args.discovery_ports = _parse_ports(args.discovery_ports)
    return args


def main() -> None:
    args = parse_args()
    if args.subnet:
        if not args.allow_lan_scan:
            raise SystemExit("--subnet requires explicit --allow-lan-scan")
        receipt = _scan_subnet(args)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return
    if not args.host:
        raise SystemExit("--host is required unless --subnet is provided with --allow-lan-scan")

    ports = list(dict.fromkeys([args.rtsp_port, args.onvif_port, *args.discovery_ports]))
    open_ports: list[int] = []
    rtsp_reachable: bool | str = "not_attempted"
    onvif_reachable: bool | str = "not_attempted"
    if not args.skip_reachability:
        _hostname, open_port_map = _scan_host(args.host, ports, args.timeout_seconds)
        open_ports = [int(port) for port, reachable in open_port_map.items() if reachable]
        rtsp_reachable = bool(open_port_map.get(str(args.rtsp_port)))
        onvif_reachable = bool(open_port_map.get(str(args.onvif_port)))
    candidate_kind = _candidate_kind(
        rtsp_reachable=rtsp_reachable,
        onvif_reachable=onvif_reachable,
        open_ports=open_ports,
    )

    source_uri = (
        f"rtsp://{args.username}:{args.password_placeholder}"
        f"@{args.host}:{args.rtsp_port}/{args.stream}"
    )
    config = {
        "camera": {
            "camera_id": args.camera_id,
            "name": args.name,
            "source_type": "rtsp",
            "source_uri": source_uri,
            "room_id": args.room_id,
            "room_label": args.room_label,
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
            "allow_embedded_credentials": True,
            "privacy": {
                "raw_video_storage": "local_only",
                "cloud_upload_default": False,
            },
        },
        "notes": {
            "source": "owner_specified_host",
            "candidate_kind": candidate_kind,
            "open_ports": open_ports,
            "discovery_ports": ports,
            "rtsp_port_reachable": rtsp_reachable,
            "onvif_port_reachable": onvif_reachable,
            "edit_before_probe": "Replace the password placeholder in this ignored local file before live probing.",
            "next_command": "python3 apps/caresight-hub/scripts/caresight_camera_probe.py --config <this-file>",
            "rtsp_template_status": (
                "ready_for_probe" if rtsp_reachable is True else "template_only_until_rtsp_port_is_reachable"
            ),
        },
    }
    receipt = {
        "schema": "camera-discovery-receipt",
        "mode": "owner_specified_host",
        "host": args.host,
        "rtsp_port": args.rtsp_port,
        "onvif_port": args.onvif_port,
        "discovery_ports": ports,
        "open_ports": open_ports,
        "rtsp_reachable": rtsp_reachable,
        "onvif_reachable": onvif_reachable,
        "candidate_kind": candidate_kind,
        "camera_id": args.camera_id,
        "source_type": "rtsp",
        "redacted_uri": f"rtsp://***:***@{args.host}:{args.rtsp_port}/{args.stream}",
        "config": config,
        "network_scan_performed": False,
    }
    if args.write_config:
        path = Path(args.write_config)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt["written_config"] = str(path)
    print(json.dumps(receipt, indent=2, sort_keys=True))


def _scan_subnet(args: argparse.Namespace) -> dict[str, object]:
    network = ipaddress.ip_network(args.subnet, strict=False)
    hosts = list(network.hosts())
    if len(hosts) > args.max_hosts:
        raise SystemExit(f"refusing to scan {len(hosts)} hosts; raise --max-hosts explicitly if intended")
    ports = list(dict.fromkeys([args.rtsp_port, args.onvif_port, *args.discovery_ports]))
    local_addresses = _local_ipv4_addresses()
    arp_hosts = _arp_hosts() if args.include_arp else []
    candidates = []
    checked = 0
    worker_count = max(1, min(args.scan_workers, len(hosts) or 1))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(_scan_host, str(host), ports, args.scan_timeout_seconds): str(host)
            for host in hosts
        }
        for future in as_completed(futures):
            hostname, open_port_map = future.result()
            checked += 1
            if args.progress_every > 0 and (checked == len(hosts) or checked % args.progress_every == 0):
                print(
                    f"scan_progress checked={checked}/{len(hosts)} candidates={len(candidates)}",
                    file=sys.stderr,
                    flush=True,
                )
            if not open_port_map:
                continue
            if hostname in local_addresses:
                continue
            candidates.append(
                {
                    "host": hostname,
                    "open_ports": [int(port) for port, reachable in open_port_map.items() if reachable],
                    "rtsp_port": args.rtsp_port,
                    "rtsp_reachable": bool(open_port_map.get(str(args.rtsp_port))),
                    "onvif_port": args.onvif_port,
                    "onvif_reachable": bool(open_port_map.get(str(args.onvif_port))),
                    "suggested_next_command": (
                        "python3 apps/caresight-hub/scripts/caresight_camera_discover.py "
                        f"--host {hostname} --camera-id <camera_id> "
                        "--write-config apps/caresight-hub/config/<camera_id>.local.json"
                    ),
                }
            )
    candidate_hosts = {candidate["host"] for candidate in candidates}
    unclassified_arp_hosts = [
        {
            **host,
            "suggested_next_command": (
                "python3 apps/caresight-hub/scripts/caresight_camera_discover.py "
                f"--host {host['host']} --camera-id <camera_id> "
                "--write-config apps/caresight-hub/config/<camera_id>.local.json"
            ),
        }
        for host in arp_hosts
        if host["host"] not in local_addresses and host["host"] not in candidate_hosts
    ]
    return {
        "schema": "camera-discovery-receipt",
        "mode": "owner_authorized_lan_scan",
        "subnet": str(network),
        "rtsp_port": args.rtsp_port,
        "onvif_port": args.onvif_port,
        "discovery_ports": ports,
        "hosts_checked": checked,
        "scan_timeout_seconds": args.scan_timeout_seconds,
        "scan_workers": worker_count,
        "local_addresses": sorted(local_addresses),
        "arp_hosts": arp_hosts,
        "unclassified_arp_hosts": unclassified_arp_hosts,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "network_scan_performed": True,
        "credential_attempted": False,
        "discovery_note": (
            "ARP-visible hosts are local devices observed on the LAN, not confirmed cameras. "
            "A camera candidate requires an open discovery port or an owner-specified host probe."
        ),
    }


def _scan_host(hostname: str, ports: list[int], timeout: float) -> tuple[str, dict[str, bool]]:
    open_port_map = {}
    for port in ports:
        reachable = _tcp_reachable(hostname, port, timeout)
        if reachable:
            open_port_map[str(port)] = True
    return hostname, open_port_map


def _candidate_kind(
    *,
    rtsp_reachable: bool | str,
    onvif_reachable: bool | str,
    open_ports: list[int],
) -> str:
    if rtsp_reachable is True:
        return "rtsp_ready"
    if onvif_reachable is True:
        return "onvif_only"
    if open_ports:
        return "service_only"
    if rtsp_reachable == "not_attempted":
        return "not_attempted"
    return "no_checked_ports_reachable"


def _parse_ports(value: str) -> list[int]:
    ports = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        port = int(raw)
        if not 1 <= port <= 65535:
            raise argparse.ArgumentTypeError(f"invalid port: {raw}")
        ports.append(port)
    return ports


def _local_ipv4_addresses() -> set[str]:
    addresses: set[str] = set()
    try:
        output = subprocess.run(["ifconfig"], check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return addresses
    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == "inet" and not parts[1].startswith("127."):
            addresses.add(parts[1])
    return addresses


def _arp_hosts() -> list[dict[str, str]]:
    try:
        output = subprocess.run(["arp", "-a"], check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    hosts = []
    for line in output.splitlines():
        if " at " not in line or "incomplete" in line:
            continue
        start = line.find("(")
        end = line.find(")")
        if start == -1 or end == -1 or end <= start:
            continue
        ip = line[start + 1:end]
        mac = line.split(" at ", 1)[1].split(" ", 1)[0]
        if ip.startswith(("224.", "239.", "255.")):
            continue
        hosts.append({"host": ip, "mac": mac})
    return hosts


def _tcp_reachable(hostname: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    main()
