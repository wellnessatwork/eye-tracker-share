import psutil
import platform
import subprocess

def get_cpu_usage():
    return psutil.cpu_percent(interval=0.5)

def get_memory_usage():
    mem = psutil.virtual_memory()
    return mem.used / (1024 * 1024)  # Convert bytes to MB

def get_power_usage():
    """
    Cross-platform attempt:
    - On macOS: uses pmset for power source and energy impact (approx.)
    - On Windows/Linux: shows battery percentage and charging status
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(["pmset", "-g", "ps"]).decode()
            return output.strip().split("\n")[1]  # Second line usually has info
        except Exception:
            return "Unknown"

    battery = psutil.sensors_battery()
    if battery:
        return f"{battery.percent}% {'Charging' if battery.power_plugged else 'On Battery'}"
    else:
        return "No Battery / Desktop"
