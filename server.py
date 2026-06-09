"""
SAP SuccessFactors MCP Server
Exposes mock SAP SuccessFactors OData endpoints as MCP tools
that can be discovered and called by Copilot Studio agents.

Uses Streamable HTTP transport for compatibility with Copilot Studio.
"""
import json
import contextlib
from collections.abc import AsyncIterator

from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import Tool, TextContent

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from sap_client import (
    get_users,
    get_users_by_role,
    get_employee_time,
    get_job_requisitions,
    get_job_requisition_by_id,
)

# ── Create the MCP server ──────────────────────────────────────
app = Server("sap-successfactors-mcp")


# ── Tool Definitions ───────────────────────────────────────────
@app.list_tools()
async def list_tools() -> list[Tool]:
    """Advertise all tools available from this MCP server."""
    return [
        Tool(
            name="get_employee_profile",
            description=(
                "Get an employee's profile data from SAP SuccessFactors. "
                "Use this when asked about employee details, org structure, org chart, who someone reports to, "
                "compensation band, job title, role, or user information. "
                "Returns name, email, role, and creation date. "
                "If no UserID is provided, returns all employees."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The employee's SAP User ID (e.g., U1001). Leave empty to list all employees.",
                    }
                },
            },
        ),
        Tool(
            name="get_employees_by_role",
            description=(
                "Get all employees with a specific role from SAP SuccessFactors. "
                "Valid roles: Admin, User, Moderator, Editor."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The role to filter by (Admin, User, Moderator, or Editor).",
                    }
                },
                "required": ["role"],
            },
        ),
        Tool(
            name="get_pto_balance",
            description=(
                "Get an employee's PTO balance, vacation days, and time-off records from SAP SuccessFactors. "
                "Use this when asked about PTO, leave balance, vacation days, time off, or absence. "
                "Returns hours worked, PTO taken, start/end times, and break minutes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The Employee ID (e.g., E1001). Leave empty to list all time-off records.",
                    }
                },
            },
        ),
        Tool(
            name="get_open_positions",
            description=(
                "Get open job requisitions and available positions from SAP SuccessFactors. "
                "Use this when asked about open roles, job openings, hiring, vacancies, or recruitment. "
                "Supports filtering by status (Open/Closed) and department."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: Open or Closed. Defaults to Open.",
                    },
                    "department": {
                        "type": "string",
                        "description": "Filter by department name (e.g., Engineering, Marketing, IT).",
                    },
                },
            },
        ),
        Tool(
            name="get_position_details",
            description=(
                "Get detailed information about a specific job requisition by its ID. "
                "Returns title, department, location, posted date, status, and description."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requisition_id": {
                        "type": "string",
                        "description": "The Job Requisition ID (e.g., JR1001).",
                    }
                },
                "required": ["requisition_id"],
            },
        ),
    ]


# ── Tool Execution ─────────────────────────────────────────────
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to the appropriate SAP client function."""
    try:
        if name == "get_employee_profile":
            data = await get_users(user_id=arguments.get("user_id"))

        elif name == "get_employees_by_role":
            role = arguments.get("role", "")
            if not role:
                return [TextContent(type="text", text="Error: role parameter is required.")]
            data = await get_users_by_role(role=role)

        elif name == "get_pto_balance":
            data = await get_employee_time(employee_id=arguments.get("employee_id"))

        elif name == "get_open_positions":
            data = await get_job_requisitions(
                status=arguments.get("status", "Open"),
                department=arguments.get("department"),
            )

        elif name == "get_position_details":
            req_id = arguments.get("requisition_id", "")
            if not req_id:
                return [TextContent(type="text", text="Error: requisition_id parameter is required.")]
            data = await get_job_requisition_by_id(requisition_id=req_id)

        else:
            return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error calling SAP: {str(e)}")]


# ── Streamable HTTP Transport Setup ────────────────────────────
session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store=None,
    stateless=True,
)


async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    """Handle incoming Streamable HTTP requests for the MCP server."""
    await session_manager.handle_request(scope, receive, send)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Manage the session manager lifecycle."""
    async with session_manager.run():
        print("SAP SuccessFactors MCP Server started on /mcp endpoint")
        yield
        print("SAP SuccessFactors MCP Server shutting down")


# ── Build the ASGI application ─────────────────────────────────
starlette_app = Starlette(
    debug=False,
    routes=[Mount("/mcp", app=handle_streamable_http)],
    lifespan=lifespan,
)


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("SAP SuccessFactors MCP Server")
    print("=" * 60)
    print("Starting on http://localhost:8000/mcp")
    print("Available tools:")
    print("  - get_employee_profile")
    print("  - get_employees_by_role")
    print("  - get_pto_balance")
    print("  - get_open_positions")
    print("  - get_position_details")
    print("=" * 60)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)