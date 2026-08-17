#!/usr/bin/env python3
"""
PC-Doctor-Lite v1.0
A clean, local-only PC health check tool that generates an HTML report.

Author: fsadmin
License: MIT (main program) / See LICENSE-THIRDPARTY.txt for bundled tools
WARNING: This script must be run with Administrator privileges on Windows
         to access temperature sensors and system logs.
"""

import os
import sys
import json
import platform
import subprocess
import datetime
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Cross-platform compatibility shims
# ---------------------------------------------------------------------------
try:
    import psutil
except ImportError:
    psutil = None

try:
    import wmi
except ImportError:
    wmi = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME = "PC-Doctor-Lite"
APP_VERSION = "1.0.0"
REPORT_DIR = Path(os.getenv("TEMP", os.path.expanduser("~"))) / "PC-Doctor-Lite-Reports"
TOOLS_DIR = Path(__file__).parent.parent / "tools"
TEMPLATE_DIR = Path(__file__).parent.parent / "report-template"

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_get(func, default="N/A"):
    try:
        return func()
    except Exception:
        return default

# ---------------------------------------------------------------------------
# Hardware information collection
# ---------------------------------------------------------------------------
def collect_system_info():
    """Collect basic OS and system information."""
    info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()} (Build {platform.version()})",
        "architecture": platform.architecture()[0],
        "boot_time": safe_get(lambda: datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")) if psutil else "N/A",
        "timestamp": get_timestamp(),
    }
    return info

def collect_cpu_info():
    """Collect CPU information."""
    info = {
        "name": "Unknown",
        "cores_physical": "N/A",
        "cores_logical": "N/A",
        "max_frequency_mhz": "N/A",
        "current_usage_percent": "N/A",
    }

    if wmi:
        try:
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                info["name"] = cpu.Name.strip()
                info["cores_physical"] = cpu.NumberOfCores
                info["cores_logical"] = cpu.NumberOfLogicalProcessors
                if cpu.MaxClockSpeed:
                    info["max_frequency_mhz"] = f"{cpu.MaxClockSpeed} MHz"
                break
        except Exception:
            pass

    if psutil:
        try:
            info["current_usage_percent"] = f"{psutil.cpu_percent(interval=1)}%"
            info["max_frequency_mhz"] = f"{psutil.cpu_freq().max:.0f} MHz" if psutil.cpu_freq() else info["max_frequency_mhz"]
        except Exception:
            pass

    return info

def collect_memory_info():
    """Collect RAM information."""
    info = {
        "total_gb": "N/A",
        "available_gb": "N/A",
        "used_percent": "N/A",
        "modules": [],
    }

    if psutil:
        try:
            vm = psutil.virtual_memory()
            info["total_gb"] = f"{vm.total / (1024**3):.1f} GB"
            info["available_gb"] = f"{vm.available / (1024**3):.1f} GB"
            info["used_percent"] = f"{vm.percent}%"
        except Exception:
            pass

    if wmi:
        try:
            c = wmi.WMI()
            for m in c.Win32_PhysicalMemory():
                info["modules"].append({
                    "capacity_gb": round(int(m.Capacity) / (1024**3), 1) if m.Capacity else "N/A",
                    "speed_mhz": m.Speed if m.Speed else "N/A",
                    "manufacturer": m.Manufacturer if m.Manufacturer else "Unknown",
                    "part_number": m.PartNumber.strip() if m.PartNumber else "N/A",
                })
        except Exception:
            pass

    return info

def collect_disk_info():
    """Collect disk partition and usage information."""
    disks = []
    if psutil:
        try:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append({
                        "drive": part.mountpoint,
                        "filesystem": part.fstype,
                        "total_gb": f"{usage.total / (1024**3):.1f} GB",
                        "used_gb": f"{usage.used / (1024**3):.1f} GB",
                        "free_gb": f"{usage.free / (1024**3):.1f} GB",
                        "used_percent": usage.percent,
                    })
                except PermissionError:
                    continue
        except Exception:
            pass
    return disks

def collect_gpu_info():
    """Collect GPU information via WMI."""
    gpus = []
    if wmi:
        try:
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                gpus.append({
                    "name": gpu.Name.strip() if gpu.Name else "Unknown",
                    "driver_version": gpu.DriverVersion if gpu.DriverVersion else "N/A",
                    "adapter_ram_mb": f"{int(gpu.AdapterRAM) / (1024**2):.0f} MB" if gpu.AdapterRAM else "N/A",
                })
        except Exception:
            pass
    return gpus

def collect_temperature_info():
    """Collect temperature data via WMI / OpenHardwareMonitor schema."""
    temps = {}
    if wmi:
        try:
            c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            for sensor in c.Sensor():
                if sensor.SensorType == "Temperature":
                    key = f"{sensor.Name}"
                    temps[key] = {
                        "value": sensor.Value,
                        "max": sensor.Max,
                    }
        except Exception:
            # OpenHardwareMonitor namespace not available
            temps = {}
    return temps

def collect_bsod_info():
    """Collect recent BSOD minidump information."""
    bsod_list = []
    minidump_dir = Path("C:/Windows/Minidump")

    if not minidump_dir.exists():
        return bsod_list

    try:
        dump_files = sorted(minidump_dir.glob("*.dmp"), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
        for f in dump_files:
            bsod_list.append({
                "file": f.name,
                "date": datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size_kb": f"{f.stat().st_size / 1024:.0f} KB",
            })
    except Exception:
        pass

    # Try BlueScreenView CLI if available
    bsv = TOOLS_DIR / "BlueScreenView.exe"
    if bsv.exists():
        try:
            output_html = REPORT_DIR / "bsod_report.html"
            subprocess.run(
                [str(bsv), "/shtml", str(output_html), "/MiniDumpFolder", str(minidump_dir)],
                capture_output=True, timeout=30
            )
        except Exception:
            pass

    return bsod_list

def run_crystaldiskinfo():
    """Run CrystalDiskInfo portable to get SMART data."""
    cdi = TOOLS_DIR / "CrystalDiskInfo.exe"
    smart_data = []
    if cdi.exists():
        try:
            result = subprocess.run(
                [str(cdi), "/CopyExit", "/Exit"],
                capture_output=True, text=True, timeout=30
            )
            # CrystalDiskInfo outputs to clipboard or file
            smart_data.append({"status": "CrystalDiskInfo executed. Check report files."})
        except Exception as e:
            smart_data.append({"status": f"Error: {e}"})
    else:
        smart_data.append({"status": "CrystalDiskInfo not found in tools/. Please add it to enable disk health checks."})
    return smart_data

# ---------------------------------------------------------------------------
# Analysis & scoring
# ---------------------------------------------------------------------------
def analyze_health(data):
    """Analyze collected data and produce human-readable findings."""
    findings = []
    score = 100

    # CPU usage check
    cpu_usage = data.get("cpu", {}).get("current_usage_percent", "N/A")
    if isinstance(cpu_usage, str) and "%" in cpu_usage:
        try:
            pct = int(cpu_usage.replace("%", ""))
            if pct > 90:
                findings.append({"level": "red", "title": "CPU 占用极高", "detail": f"当前 CPU 占用 {cpu_usage}，系统可能严重卡顿。建议关闭高占用进程。"})
                score -= 15
            elif pct > 70:
                findings.append({"level": "yellow", "title": "CPU 占用偏高", "detail": f"当前 CPU 占用 {cpu_usage}。可打开任务管理器查看哪个程序吃资源。"})
                score -= 5
        except ValueError:
            pass

    # Memory check
    mem = data.get("memory", {})
    mem_pct = mem.get("used_percent", "N/A")
    if isinstance(mem_pct, str) and "%" in mem_pct:
        try:
            pct = int(mem_pct.replace("%", ""))
            if pct > 90:
                findings.append({"level": "red", "title": "内存严重不足", "detail": f"内存使用率 {mem_pct}，系统可能频繁卡死。建议加内存条或关闭后台程序。"})
                score -= 15
            elif pct > 80:
                findings.append({"level": "yellow", "title": "内存使用率偏高", "detail": f"内存使用率 {mem_pct}。可清理浏览器标签页释放内存。"})
                score -= 5
        except ValueError:
            pass

    # Disk space check
    for disk in data.get("disks", []):
        pct = disk.get("used_percent", 0)
        if isinstance(pct, (int, float)) and pct > 90:
            findings.append({"level": "red", "title": f"{disk['drive']} 空间严重不足", "detail": f"已用 {disk['used_percent']}%。建议清理 Windows Update 缓存、临时文件或大文件。"})
            score -= 10
        elif isinstance(pct, (int, float)) and pct > 80:
            findings.append({"level": "yellow", "title": f"{disk['drive']} 空间偏满", "detail": f"已用 {disk['used_percent']}%。建议定期清理。"})
            score -= 3

    # Temperature check
    temps = data.get("temperatures", {})
    for name, t in temps.items():
        val = t.get("value", 0)
        if val > 90:
            findings.append({"level": "red", "title": f"{name} 温度过高", "detail": f"当前 {val}°C，存在过热降频甚至硬件损伤风险。建议清灰、换硅脂、检查散热。"})
            score -= 15
        elif val > 75:
            findings.append({"level": "yellow", "title": f"{name} 温度偏高", "detail": f"当前 {val}°C。建议改善通风或清灰。"})
            score -= 5

    # BSOD check
    bsods = data.get("bsod", [])
    if len(bsods) > 3:
        findings.append({"level": "yellow", "title": f"近期蓝屏 {len(bsods)} 次", "detail": "频繁蓝屏通常指向驱动冲突或硬件不稳定。建议更新驱动或用 BlueScreenView 分析 dump 文件。"})
        score -= 10
    elif len(bsods) > 0:
        findings.append({"level": "yellow", "title": f"检测到 {len(bsods)} 次蓝屏记录", "detail": "偶尔蓝屏可能是驱动或系统更新导致。如反复出现需排查。"})
        score -= 3

    # Admin check
    if not data.get("is_admin", False):
        findings.append({"level": "yellow", "title": "未以管理员身份运行", "detail": "部分传感器和日志无法读取。建议右键 exe → 以管理员身份运行，可获得完整报告。"})
        score -= 5

    score = max(0, min(100, score))
    return findings, score

# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------
def generate_html_report(data, findings, score):
    """Generate a self-contained HTML report."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = get_timestamp()

    # Color for score
    if score >= 80:
        score_color = "#22c55e"  # green
        score_label = "良好"
    elif score >= 60:
        score_color = "#eab308"  # yellow
        score_label = "需要注意"
    else:
        score_color = "#ef4444"  # red
        score_label = "建议尽快处理"

    # Findings HTML
    findings_html = ""
    if findings:
        for f in findings:
            color = {"red": "#ef4444", "yellow": "#eab308", "green": "#22c55e"}.get(f["level"], "#6b7280")
            icon = {"red": "⚠️", "yellow": "⚡", "green": "✅"}.get(f["level"], "ℹ️")
            findings_html += f'''
            <div class="finding {f["level"]}">
                <span class="finding-icon">{icon}</span>
                <div class="finding-body">
                    <div class="finding-title" style="color:{color}">{f["title"]}</div>
                    <div class="finding-detail">{f["detail"]}</div>
                </div>
            </div>'''
    else:
        findings_html = '<div class="finding green"><span class="finding-icon">✅</span><div class="finding-body"><div class="finding-title" style="color:#22c55e">一切正常</div><div class="finding-detail">未检测到明显问题。</div></div></div>'

    # Disks HTML
    disks_html = ""
    for d in data.get("disks", []):
        pct = d.get("used_percent", 0)
        bar_color = "#22c55e" if pct < 70 else "#eab308" if pct < 90 else "#ef4444"
        disks_html += f'''
        <tr>
            <td>{d["drive"]}</td>
            <td>{d["filesystem"]}</td>
            <td>{d["total_gb"]}</td>
            <td>{d["used_gb"]}</td>
            <td>{d["free_gb"]}</td>
            <td>
                <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
                {pct}%
            </td>
        </tr>'''

    # Temperatures HTML
    temps = data.get("temperatures", {})
    temps_html = ""
    if temps:
        for name, t in temps.items():
            val = t.get("value", 0)
            color = "#ef4444" if val > 90 else "#eab308" if val > 75 else "#22c55e"
            temps_html += f'<div class="temp-item"><span>{name}</span><span style="color:{color};font-weight:bold">{val}°C</span></div>'
    else:
        temps_html = '<div class="temp-item"><span>传感器不可用</span><span style="color:#9ca3af">请以管理员身份运行</span></div>'

    # BSOD HTML
    bsod_html = ""
    bsods = data.get("bsod", [])
    if bsods:
        for b in bsods:
            bsod_html += f'<tr><td>{b["file"]}</td><td>{b["date"]}</td><td>{b["size_kb"]}</td></tr>'
    else:
        bsod_html = '<tr><td colspan="3" style="text-align:center;color:#9ca3af">未检测到蓝屏记录，恭喜 🎉</td></tr>'

    # GPUs HTML
    gpus = data.get("gpu", [])
    gpu_html = ""
    if gpus:
        for g in gpus:
            gpu_html += f'<div class="gpu-item"><strong>{g["name"]}</strong> · 驱动 {g["driver_version"]} · {g["adapter_ram_mb"]}</div>'
    else:
        gpu_html = '<div class="gpu-item" style="color:#9ca3af">未检测到显卡信息</div>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>PC-Doctor-Lite 体检报告</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:"WenQuanYi Micro Hei","Microsoft YaHei",sans-serif; background:#f8fafc; color:#1e293b; line-height:1.6; padding:24px; }}
.container {{ max-width:900px; margin:0 auto; }}
.header {{ background:linear-gradient(135deg,#6366f1,#8b5cf6); color:white; padding:32px; border-radius:16px; margin-bottom:24px; }}
.header h1 {{ font-size:28px; margin-bottom:8px; }}
.header p {{ opacity:0.85; font-size:14px; }}
.score-badge {{ display:inline-flex; align-items:center; gap:12px; margin-top:16px; }}
.score-circle {{ width:72px; height:72px; border-radius:50%; background:rgba(255,255,255,0.2); display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:bold; border:3px solid {score_color}; }}
.score-label {{ font-size:18px; font-weight:bold; }}
.card {{ background:white; border-radius:12px; padding:24px; margin-bottom:20px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
.card h2 {{ font-size:18px; margin-bottom:16px; color:#334155; border-left:4px solid #6366f1; padding-left:12px; }}
.info-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.info-item {{ background:#f1f5f9; padding:12px; border-radius:8px; }}
.info-item .label {{ font-size:12px; color:#64748b; margin-bottom:4px; }}
.info-item .value {{ font-size:15px; font-weight:600; color:#1e293b; }}
.finding {{ display:flex; gap:12px; padding:14px; border-radius:10px; margin-bottom:10px; background:#f8fafc; border-left:4px solid #e2e8f0; }}
.finding.red {{ border-left-color:#ef4444; background:#fef2f2; }}
.finding.yellow {{ border-left-color:#eab308; background:#fefce8; }}
.finding.green {{ border-left-color:#22c55e; background:#f0fdf4; }}
.finding-icon {{ font-size:22px; flex-shrink:0; }}
.finding-title {{ font-weight:bold; font-size:14px; margin-bottom:4px; }}
.finding-detail {{ font-size:13px; color:#475569; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:#f1f5f9; padding:10px 12px; text-align:left; font-weight:600; color:#475569; }}
td {{ padding:10px 12px; border-bottom:1px solid #f1f5f9; }}
.bar-bg {{ width:80px; height:8px; background:#e2e8f0; border-radius:4px; display:inline-block; margin-right:6px; vertical-align:middle; }}
.bar-fill {{ height:100%; border-radius:4px; transition:width 0.3s; }}
.temp-item {{ display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1f5f9; font-size:14px; }}
.gpu-item {{ padding:8px 0; font-size:14px; border-bottom:1px solid #f1f5f9; }}
.footer {{ text-align:center; color:#94a3b8; font-size:12px; margin-top:32px; padding:16px; }}
.footer a {{ color:#6366f1; text-decoration:none; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🩺 PC-Doctor-Lite</h1>
        <p>电脑体检报告 · 生成时间 {timestamp}</p>
        <p style="margin-top:4px;font-size:12px;opacity:0.7">设备：{data.get("system",{}).get("hostname","N/A")} · {data.get("system",{}).get("os","N/A")}</p>
        <div class="score-badge">
            <div class="score-circle">{score}</div>
            <div>
                <div class="score-label" style="color:{score_color}">{score_label}</div>
                <div style="font-size:12px;opacity:0.8">综合健康评分</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>🔍 健康发现</h2>
        {findings_html}
    </div>

    <div class="card">
        <h2>💻 硬件配置</h2>
        <div class="info-grid">
            <div class="info-item"><div class="label">CPU</div><div class="value">{data.get("cpu",{}).get("name","N/A")}</div></div>
            <div class="info-item"><div class="label">核心数</div><div class="value">{data.get("cpu",{}).get("cores_physical","N/A")} 物理 / {data.get("cpu",{}).get("cores_logical","N/A")} 逻辑</div></div>
            <div class="info-item"><div class="label">内存</div><div class="value">{data.get("memory",{}).get("total_gb","N/A")}（已用 {data.get("memory",{}).get("used_percent","N/A")}）</div></div>
            <div class="info-item"><div class="label">系统</div><div class="value">{data.get("system",{}).get("os","N/A")}</div></div>
        </div>
        <div style="margin-top:14px">{gpu_html}</div>
    </div>

    <div class="card">
        <h2>🌡️ 温度监控</h2>
        {temps_html}
    </div>

    <div class="card">
        <h2>💾 磁盘空间</h2>
        <table>
            <tr><th>盘符</th><th>文件系统</th><th>总容量</th><th>已用</th><th>剩余</th><th>使用率</th></tr>
            {disks_html}
        </table>
    </div>

    <div class="card">
        <h2>🛡️ 蓝屏记录</h2>
        <table>
            <tr><th>文件名</th><th>日期</th><th>大小</th></tr>
            {bsod_html}
        </table>
    </div>

    <div class="footer">
        <p>PC-Doctor-Lite v{APP_VERSION} · 纯本地运行 · 数据不上传</p>
        <p>基于 LibreHardwareMonitor / CrystalDiskInfo / BlueScreenView 等开源工具</p>
        <p>由 <a href="https://github.com/">fsadmin</a> 整理打包 · 仅供个人学习使用</p>
    </div>
</div>
</body>
</html>'''

    report_path = REPORT_DIR / f"PC-Doctor-Report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    report_path.write_text(html, encoding="utf-8")
    return report_path

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"""
╔══════════════════════════════════════════╗
║       PC-Doctor-Lite v{APP_VERSION}              ║
║       纯本地 · 不联网 · 双击即用         ║
╚══════════════════════════════════════════╝
""")

    # Check admin
    admin = is_admin()
    if not admin:
        print("⚠️  未以管理员身份运行！部分传感器和日志无法读取。")
        print("   建议：右键 exe → 以管理员身份运行\n")
    else:
        print("✅ 管理员权限确认\n")

    print("📋 正在采集系统信息...")
    system_info = collect_system_info()

    print("📋 正在采集 CPU 信息...")
    cpu_info = collect_cpu_info()

    print("📋 正在采集内存信息...")
    memory_info = collect_memory_info()

    print("📋 正在采集磁盘信息...")
    disk_info = collect_disk_info()

    print("📋 正在采集显卡信息...")
    gpu_info = collect_gpu_info()

    print("🌡️  正在读取温度（需管理员权限）...")
    temp_info = collect_temperature_info()
    if not temp_info:
        print("   ⚠️ 温度数据不可用（需安装 OpenHardwareMonitor 或以管理员运行）")

    print("🛡️  正在检查蓝屏记录...")
    bsod_info = collect_bsod_info()

    print("💾 正在检查硬盘健康...")
    smart_info = run_crystaldiskinfo()

    # Bundle all data
    all_data = {
        "is_admin": admin,
        "system": system_info,
        "cpu": cpu_info,
        "memory": memory_info,
        "disks": disk_info,
        "gpu": gpu_info,
        "temperatures": temp_info,
        "bsod": bsod_info,
        "smart": smart_info,
    }

    # Analyze
    print("\n🔍 正在分析健康状态...")
    findings, score = analyze_health(all_data)

    # Generate report
    print("📄 正在生成 HTML 报告...")
    report_path = generate_html_report(all_data, findings, score)

    print(f"\n✅ 报告已生成：{report_path}")
    print(f"   综合评分：{score}/100")

    if findings:
        print("\n⚠️  发现以下问题：")
        for f in findings:
            icon = "🔴" if f["level"] == "red" else "🟡" if f["level"] == "yellow" else "🟢"
            print(f"   {icon} {f['title']}")

    # Auto-open report
    try:
        os.startfile(str(report_path))  # Windows
    except AttributeError:
        try:
            subprocess.run(["open", str(report_path)])  # macOS
        except Exception:
            pass

    print("\n按回车键退出...")
    input()

if __name__ == "__main__":
    main()
