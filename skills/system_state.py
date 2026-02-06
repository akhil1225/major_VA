from skills.system_info import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_battery_status,
    is_connected_to_internet,
    get_system_uptime_minutes
)


class SystemState:
    """
    Interprets raw system info into human-meaningful awareness.
    """

    def __init__(self):
        self.refresh()


    def refresh(self):
        self.cpu = get_cpu_usage()
        self.memory = get_memory_usage()
        self.disk = get_disk_usage()
        self.battery = get_battery_status()
        self.online = is_connected_to_internet()
        self.uptime_min = get_system_uptime_minutes()


    def is_high_load(self) -> bool:
        return self.cpu > 80 or self.memory["percent"] > 85

    def is_low_battery(self) -> bool:
        return bool(
            self.battery.get("available") and
            not self.battery.get("plugged_in") and
            self.battery.get("percent", 100) < 20
        )

    def is_critical_battery(self) -> bool:
        return bool(
            self.battery.get("available") and
            not self.battery.get("plugged_in") and
            self.battery.get("percent", 100) < 10
        )

    def is_offline(self) -> bool:
        return not self.online


    def summary(self) -> str:
        messages = []

        if self.is_high_load():
            messages.append("The system is under heavy load.")

        if self.is_critical_battery():
            messages.append("Battery level is critically low.")
        elif self.is_low_battery():
            messages.append("Battery level is low.")

        if self.is_offline():
            messages.append("You are currently offline.")

        if not messages:
            return "Your system is running normally."

        return " ".join(messages)
