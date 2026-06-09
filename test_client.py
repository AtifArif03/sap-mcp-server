"""Quick test of the SAP client functions."""
import asyncio
import json
from sap_client import (
    get_users,
    get_users_by_role,
    get_employee_time,
    get_job_requisitions,
    get_job_requisition_by_id,
)


async def main():
    print("=" * 60)
    print("TEST 1: Get all users")
    print("=" * 60)
    result = await get_users()
    print(f"Total users: {len(result.get('Users', []))}")
    print(json.dumps(result.get("Users", [])[:2], indent=2))

    print("\n" + "=" * 60)
    print("TEST 2: Get specific user U1003")
    print("=" * 60)
    result = await get_users(user_id="U1003")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("TEST 3: Get all Admins")
    print("=" * 60)
    result = await get_users_by_role("Admin")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("TEST 4: Get PTO / time-off records")
    print("=" * 60)
    result = await get_employee_time()
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("TEST 5: Get open job requisitions")
    print("=" * 60)
    result = await get_job_requisitions(status="Open")
    print(f"Open positions: {result.get('Count')}")
    titles = [r.get("Title") for r in result.get("JobRequisitions", [])]
    print(titles)

    print("\n" + "=" * 60)
    print("TEST 6: Get specific requisition JR1001")
    print("=" * 60)
    result = await get_job_requisition_by_id("JR1001")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())