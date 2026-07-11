import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("mcp")

class MCPServer:
    """
    Model Context Protocol (MCP) Server for the Industrial Intelligence Platform.
    This acts as the bridge between the Brains and external platforms.

    Platforms:
      - cmms (SAP PM / Maximo mock)
      - iot_sensors (mock sensor data)
    """

    def __init__(self):
        self.connected_platforms = {
            "cmms": True,           # SAP PM / Maximo mock
            "iot_sensors": True,    # IoT sensor gateway mock
        }

    def execute_tool(self, platform: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via the MCP protocol."""
        if platform not in self.connected_platforms:
            return {"status": "error", "error": f"Platform {platform} not connected."}

        logger.info(f"[MCP] Executing {action} on {platform} with params {params}")

        if platform == "cmms":
            return self._handle_cmms(action, params)

        elif platform == "iot_sensors":
            return self._handle_iot(action, params)

        return {"status": "error", "error": f"Unknown action {action} for platform {platform}"}

    # ── CMMS Mock (SAP PM / Maximo) ───────────────────────────────────────

    def _handle_cmms(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock CMMS (SAP PM / Maximo) responses for industrial demo."""
        tag = params.get("equipment_tag", "UNKNOWN")

        if action == "create_work_order":
            return {
                "status": "success",
                "wo_id": f"WO-{random.randint(10000, 99999)}",
                "equipment_tag": tag,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "cmms_system": "SAP PM (Mock)",
            }

        elif action == "get_equipment":
            # Realistic mock equipment data
            mock_equipment = {
                "P-101": {
                    "tag": "P-101", "name": "Centrifugal Feed Pump A",
                    "manufacturer": "Flowserve", "model": "Mark III 4x3-13",
                    "install_date": "2019-03-15", "serial": "FS-2019-4567",
                    "status": "operational", "runtime_hours": 42800,
                    "last_maintenance": "2026-05-20", "next_pm_due": "2026-08-20",
                    "criticality": "A", "location": "Pump House A",
                },
                "P-102": {
                    "tag": "P-102", "name": "Centrifugal Feed Pump B",
                    "manufacturer": "Flowserve", "model": "Mark III 4x3-13",
                    "install_date": "2019-03-15", "serial": "FS-2019-4568",
                    "status": "operational", "runtime_hours": 38200,
                    "last_maintenance": "2026-06-10", "next_pm_due": "2026-09-10",
                    "criticality": "A", "location": "Pump House A",
                },
                "V-205": {
                    "tag": "V-205", "name": "Safety Relief Valve",
                    "manufacturer": "Emerson (Fisher)", "model": "Type 63EG",
                    "install_date": "2020-08-22", "serial": "EM-2020-8901",
                    "status": "operational", "runtime_hours": 28500,
                    "last_maintenance": "2026-04-15", "next_pm_due": "2026-10-15",
                    "criticality": "A+", "location": "Distillation Bay",
                },
                "HX-301": {
                    "tag": "HX-301", "name": "Shell & Tube Heat Exchanger",
                    "manufacturer": "Alfa Laval", "model": "M15-BFM",
                    "install_date": "2018-11-10", "serial": "AL-2018-3456",
                    "status": "degraded", "runtime_hours": 56200,
                    "last_maintenance": "2026-02-28", "next_pm_due": "2026-05-28",
                    "criticality": "B", "location": "Cooling Tower Area",
                },
            }
            equipment = mock_equipment.get(tag, {
                "tag": tag, "name": f"Equipment {tag}",
                "manufacturer": "Unknown", "status": "unknown",
                "cmms_system": "SAP PM (Mock)",
            })
            return {"status": "success", "equipment": equipment, "cmms_system": "SAP PM (Mock)"}

        elif action == "get_maintenance_history":
            return {
                "status": "success",
                "equipment_tag": tag,
                "work_orders": [
                    {"wo_id": "WO-45123", "type": "preventive", "date": "2026-05-20", "status": "completed"},
                    {"wo_id": "WO-44890", "type": "corrective", "date": "2026-03-14", "status": "completed"},
                    {"wo_id": "WO-44201", "type": "preventive", "date": "2025-11-15", "status": "completed"},
                ],
                "cmms_system": "SAP PM (Mock)",
            }

        return {"status": "error", "error": f"Unknown CMMS action: {action}"}

    # ── IoT Sensor Mock ───────────────────────────────────────────────────

    def _handle_iot(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock IoT sensor data for industrial demo."""
        tag = params.get("equipment_tag", "UNKNOWN")

        if action == "read_sensors":
            # Generate realistic mock sensor readings
            sensor_profiles = {
                "P-101": {"type": "centrifugal_pump", "vibration_baseline": 2.5, "temp_baseline": 65},
                "P-102": {"type": "centrifugal_pump", "vibration_baseline": 2.3, "temp_baseline": 63},
                "V-205": {"type": "valve", "vibration_baseline": 0.5, "temp_baseline": 45},
                "HX-301": {"type": "heat_exchanger", "vibration_baseline": 1.2, "temp_baseline": 85},
                "CT-001": {"type": "cooling_tower", "vibration_baseline": 1.8, "temp_baseline": 35},
            }
            profile = sensor_profiles.get(tag, {"type": "generic", "vibration_baseline": 1.0, "temp_baseline": 50})

            vib_base = profile["vibration_baseline"]
            temp_base = profile["temp_baseline"]

            return {
                "status": "success",
                "equipment_tag": tag,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sensors": {
                    "vibration_mm_s": round(vib_base + random.uniform(-0.5, 1.5), 2),
                    "temperature_c": round(temp_base + random.uniform(-3, 8), 1),
                    "pressure_bar": round(random.uniform(3.5, 6.5), 2),
                    "flow_rate_m3h": round(random.uniform(45, 85), 1),
                    "current_amps": round(random.uniform(12, 28), 1),
                    "rpm": random.randint(2800, 3200) if "pump" in profile["type"] else None,
                },
                "alerts": [],
                "gateway": "IoT Gateway (Mock)",
            }

        elif action == "get_alerts":
            return {
                "status": "success",
                "equipment_tag": tag,
                "active_alerts": [
                    {
                        "alert_id": f"ALT-{random.randint(1000, 9999)}",
                        "type": "vibration_high",
                        "message": f"Vibration on {tag} exceeded threshold (4.2 mm/s > 4.0 mm/s)",
                        "severity": "warning",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ] if random.random() > 0.5 else [],
                "gateway": "IoT Gateway (Mock)",
            }

        return {"status": "error", "error": f"Unknown IoT action: {action}"}

mcp_client = MCPServer()

