"""
SAP SuccessFactors Mock API Client
Wraps the mock OData endpoints into clean async functions.
"""
import httpx
from typing import Optional

SAP_MOCK_BASE = "https://sapmock.outoftheboxacademy.com"


async def get_users(user_id: Optional[str] = None) -> dict:
    """Fetch user/employee data from SAP SuccessFactors."""
    url = f"{SAP_MOCK_BASE}/odata/v2/User"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

    if user_id:
        users = data.get("Users", [])
        matched = [u for u in users if u.get("UserID") == user_id]
        return {"Users": matched} if matched else {"Users": [], "message": f"No user found with UserID {user_id}"}
    return data


async def get_users_by_role(role: str) -> dict:
    """Fetch users filtered by role (Admin, User, Moderator, Editor)."""
    url = f"{SAP_MOCK_BASE}/odata/v2/User"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

    users = data.get("Users", [])
    filtered = [u for u in users if u.get("Role", "").lower() == role.lower()]
    return {"Users": filtered, "Count": len(filtered)}


async def get_employee_time(employee_id: Optional[str] = None) -> dict:
    """Fetch employee PTO balance and time-off records."""
    url = f"{SAP_MOCK_BASE}/odata/v2/EmployeeTime"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

    records = data.get("EmployeeTimes", [])

    if employee_id:
        records = [r for r in records if r.get("EmployeeID") == employee_id]
        if not records:
            return {"EmployeeTimes": [], "message": f"No records for {employee_id}"}

    # Mock PTO balances per employee — in production these come from
    # SAP SF TimeOffBalance / EmployeeTimeValuation entities, not EmployeeTime
    mock_pto = {
        "E1001": {"AnnualEntitlementDays": 20, "UsedDays": 5,  "RemainingDays": 15, "PendingApprovalDays": 2},
        "E1002": {"AnnualEntitlementDays": 20, "UsedDays": 12, "RemainingDays": 8,  "PendingApprovalDays": 0},
        "E1003": {"AnnualEntitlementDays": 25, "UsedDays": 3,  "RemainingDays": 22, "PendingApprovalDays": 1},
        "E1004": {"AnnualEntitlementDays": 20, "UsedDays": 18, "RemainingDays": 2,  "PendingApprovalDays": 0},
        "E1005": {"AnnualEntitlementDays": 20, "UsedDays": 7,  "RemainingDays": 13, "PendingApprovalDays": 3},
    }
    for r in records:
        emp_id = r.get("EmployeeID")
        balance = mock_pto.get(emp_id, {"AnnualEntitlementDays": 20, "UsedDays": 0, "RemainingDays": 20, "PendingApprovalDays": 0})
        r["PTOBalance"] = {**balance, "Unit": "Days", "Note": "Mock data — production values from SAP SF TimeOffBalance entity"}

    return {"EmployeeTimes": records}


async def get_job_requisitions(status: Optional[str] = None, department: Optional[str] = None) -> dict:
    """Fetch job requisitions with optional filters."""
    url = f"{SAP_MOCK_BASE}/odata/v2/JobRequisition"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

    requisitions = data.get("JobRequisitions", [])

    if status:
        requisitions = [r for r in requisitions if r.get("Status", "").lower() == status.lower()]
    if department:
        requisitions = [r for r in requisitions if department.lower() in r.get("Department", "").lower()]

    return {"JobRequisitions": requisitions, "Count": len(requisitions)}


async def get_job_requisition_by_id(requisition_id: str) -> dict:
    """Fetch a specific job requisition by ID."""
    url = f"{SAP_MOCK_BASE}/odata/v2/JobRequisition"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

    requisitions = data.get("JobRequisitions", [])
    matched = [r for r in requisitions if r.get("JobRequisitionID") == requisition_id]
    return {"JobRequisitions": matched} if matched else {"JobRequisitions": [], "message": f"No requisition {requisition_id}"}