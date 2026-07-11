"""Quick verification of all Phase 3 API endpoints."""
import httpx
import json

BASE = "http://localhost:8000/api/v1"

def test(method, path, body=None, label=""):
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, timeout=60)
        else:
            r = httpx.post(url, json=body, timeout=60)
        status = "OK" if r.status_code == 200 else f"FAIL({r.status_code})"
        data = r.json()
        detail = ""
        if isinstance(data, dict):
            keys = list(data.keys())[:4]
            detail = f" keys={keys}"
        print(f"  [{status}] {method} {path}{detail}")
        return data
    except Exception as e:
        print(f"  [ERROR] {method} {path} -> {e}")
        return None

print("=" * 60)
print("SUREFLOW OS - Phase 3 API Verification")
print("=" * 60)

print("\n--- Knowledge Graph Endpoints ---")
test("GET", "/industrial/graph/overview")
test("GET", "/industrial/graph/equipment")
test("GET", "/industrial/graph/equipment/P-101")
test("GET", "/industrial/graph/equipment/P-101/timeline")
test("GET", "/industrial/graph/incidents")
test("GET", "/industrial/graph/hierarchy")
test("GET", "/industrial/graph/compliance-gaps/AREA-100")

print("\n--- MCP Mock Endpoints ---")
test("GET", "/industrial/mcp/sensor/P-101")
test("GET", "/industrial/mcp/cmms/equipment/P-101")

print("\n--- Industrial KPIs & Vault ---")
test("GET", "/industrial/kpis")
test("GET", "/industrial/vault/stats")

print("\n--- Agent Status ---")
data = test("GET", "/agents/status")
if data:
    agents = data.get("agents", [])
    print(f"     Total agents: {len(agents)}")
    for a in agents:
        print(f"       {a['id']:20s} {a['name']}")

print("\n" + "=" * 60)
print("Verification complete!")
print("=" * 60)
