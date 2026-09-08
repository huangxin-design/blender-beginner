"""Read a minimal hardware inventory; never benchmark, install, or change settings."""

import argparse
import csv
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess


def command(args, warnings, timeout=20):
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError) as error:
        warnings.append(f"{Path(args[0]).name} unavailable or failed ({type(error).__name__}).")
        return None


def gpu(name, driver=None, memory=None, source=None):
    return {"name": name, "driver_version": driver, "dedicated_memory_bytes": memory,
            "dedicated_free_memory_bytes": None, "memory_source": source}


def windows(report):
    warnings = report["warnings"]
    code = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$cpu = @(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfLogicalProcessors)
$os = Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory
$ram = Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
$gpu = @(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion)
@{cpu=$cpu;os=$os;ram=$ram;gpu=$gpu} | ConvertTo-Json -Depth 4 -Compress
"""
    raw = command(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", code], warnings)
    if raw:
        try:
            data = json.loads(raw.lstrip("\ufeff"))
            report["cpu"]["name"] = "; ".join(item["Name"].strip() for item in data["cpu"])
            report["cpu"]["logical_cores"] = sum(item["NumberOfLogicalProcessors"] for item in data["cpu"])
            report["memory"].update(total_bytes=data["ram"]["TotalPhysicalMemory"],
                                    available_bytes=data["os"]["FreePhysicalMemory"] * 1024,
                                    source="Windows CIM (physical RAM and OS free memory)")
            report["gpus"] = [gpu(item["Name"], item["DriverVersion"]) for item in data["gpu"]]
        except (ValueError, KeyError, TypeError):
            warnings.append("Windows CIM returned incomplete or unexpected data.")
    nv = shutil.which("nvidia-smi")
    if nv:
        raw = command([nv, "--query-gpu=name,driver_version,memory.total,memory.free",
                       "--format=csv,noheader,nounits"], warnings)
        for row in csv.reader((raw or "").splitlines()):
            if len(row) != 4:
                warnings.append("Unexpected nvidia-smi row; memory reading skipped.")
                continue
            name, driver, total, free = [value.strip() for value in row]
            item = next((item for item in report["gpus"] if item["name"] == name
                         and item["memory_source"] is None), None)
            if item is None:
                item = gpu(name, driver)
                report["gpus"].append(item)
            item.update(driver_version=driver, memory_source="nvidia-smi (MiB, instantaneous)")
            for field, value in (("dedicated_memory_bytes", total), ("dedicated_free_memory_bytes", free)):
                try:
                    item[field] = int(float(value) * 1024 ** 2)
                except ValueError:
                    warnings.append(f"nvidia-smi did not provide {field} for {name}.")
    warnings.append("AdapterRAM is not used: its 32-bit value cannot reliably describe modern VRAM; null means unknown.")
    class PowerStatus(ctypes.Structure):
        _fields_ = [("ac", ctypes.c_ubyte), ("flags", ctypes.c_ubyte),
                    ("percent", ctypes.c_ubyte), ("reserved", ctypes.c_ubyte),
                    ("remaining", ctypes.c_uint32), ("full", ctypes.c_uint32)]
    status = PowerStatus()
    if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        report["power"] = {"source": {0: "battery", 1: "AC"}.get(status.ac),
                           "battery_present": None if status.flags == 255 else not bool(status.flags & 128),
                           "battery_percent": status.percent if status.percent <= 100 else None,
                           "measurement_source": "Windows GetSystemPowerStatus"}


def macos(report):
    warnings = report["warnings"]
    values = {}
    for key in ("hw.optional.arm64", "hw.memsize", "hw.logicalcpu", "hw.model", "machdep.cpu.brand_string"):
        values[key] = command(["/usr/sbin/sysctl", "-n", key], warnings, timeout=5)
    silicon = {"0": False, "1": True}.get(values["hw.optional.arm64"])
    if silicon is None and "Intel" in (values["machdep.cpu.brand_string"] or ""):
        silicon = False
    report["mac"] = {"hardware_family": "Apple Silicon" if silicon else
                     ("Intel" if silicon is False and report["os"]["process_architecture"] == "x86_64" else "unknown"),
                     "model_identifier": values["hw.model"],
                     "rosetta_process": None if silicon is None else
                     silicon and report["os"]["process_architecture"] == "x86_64"}
    report["cpu"]["name"] = values["machdep.cpu.brand_string"]
    if values["hw.logicalcpu"] and values["hw.logicalcpu"].isdigit():
        report["cpu"]["logical_cores"] = int(values["hw.logicalcpu"])
    if values["hw.memsize"] and values["hw.memsize"].isdigit():
        report["memory"].update(total_bytes=int(values["hw.memsize"]), source="sysctl hw.memsize")
    report["memory"]["unified_cpu_gpu"] = True if silicon else None
    warnings.append("macOS available RAM is not measured; memory pressure, compression and swap require separate assessment.")
    raw = command(["/usr/sbin/system_profiler", "SPDisplaysDataType", "-json", "-detailLevel", "mini"],
                  warnings, timeout=30)
    if raw:
        try:
            for display in json.loads(raw).get("SPDisplaysDataType", []):
                item = gpu(display.get("sppci_model") or display.get("_name"))
                vram = display.get("spdisplays_vram", "")
                match = re.fullmatch(r"\s*([\d.]+)\s*(MB|GB)\s*", vram, re.IGNORECASE)
                if match and silicon is False:
                    item.update(dedicated_memory_bytes=int(float(match[1]) * 1024 ** (2 if match[2].upper() == "MB" else 3)),
                                memory_source="system_profiler spdisplays_vram (rounded reported capacity)")
                report["gpus"].append(item)
        except (ValueError, TypeError):
            warnings.append("macOS display inventory returned unexpected data.")
    if silicon:
        warnings.append("Apple Silicon CPU/GPU share RAM; system RAM is not dedicated VRAM or a guaranteed GPU allocation.")
    raw = command(["/usr/bin/pmset", "-g", "batt"], warnings, timeout=5)
    if raw:
        percent = re.search(r"(\d+)%;", raw)
        report["power"] = {"source": "AC" if "'AC Power'" in raw else
                           ("battery" if "'Battery Power'" in raw else None),
                           "battery_present": True if "InternalBattery" in raw else None,
                           "battery_percent": int(percent[1]) if percent else None,
                           "measurement_source": "pmset -g batt"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Absolute path to a new JSON report; its volume is measured.")
    args = parser.parse_args()
    path = Path(args.output).expanduser()
    if not path.is_absolute() or path.suffix.lower() != ".json":
        parser.error("--output must be an absolute .json path.")
    path = path.resolve()
    if path.exists():
        parser.error("Refusing to overwrite an existing report.")
    report = {"schema_version": 1, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Read-only hardware inventory; no Blender device test or rendering performed.",
              "os": {"name": platform.system(), "version": platform.version(),
                     "process_architecture": platform.machine()},
              "cpu": {"name": platform.processor() or None, "logical_cores": os.cpu_count()},
              "memory": {"total_bytes": None, "available_bytes": None, "source": None, "unified_cpu_gpu": None},
              "gpus": [], "power": None, "output_volume": {"free_bytes": None, "total_bytes": None},
              "warnings": ["Hardware inventory does not establish 4K feasibility, render time or sustained animation performance."]}
    if platform.system() == "Windows":
        windows(report)
    elif platform.system() == "Darwin":
        macos(report)
    else:
        report["warnings"].append("This OS has basic inventory only; GPU, RAM and power probes are not implemented.")
    existing = path.parent
    while not existing.exists():
        existing = existing.parent
    try:
        disk = shutil.disk_usage(existing)
        report["output_volume"].update(free_bytes=disk.free, total_bytes=disk.total,
                                       measured_path=str(existing), intended_report_path=str(path))
    except OSError:
        report["warnings"].append("Output-volume free space could not be read.")
    if not report["gpus"]:
        report["warnings"].append("GPU inventory is unavailable; absence of records does not prove absence of a GPU.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"Hardware report: {path}")


if __name__ == "__main__":
    main()
