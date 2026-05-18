"""
AgentWallet MCP Server
======================
An MCP server providing agent wallet and budget management.
Stores all data in ~/.agentwallet/ as JSON files.

Pricing: $19/month — https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.lowlevel import Server
from mcp.types import Tool, TextContent

# ── Data directory ──────────────────────────────────────────────────────────

DATA_DIR = Path.home() / ".agentwallet"
WALLETS_DIR = DATA_DIR / "wallets"
TRANSACTIONS_DIR = DATA_DIR / "transactions"
INVOICES_DIR = DATA_DIR / "invoices"

for d in (WALLETS_DIR, TRANSACTIONS_DIR, INVOICES_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _wallet_path(agent_id: str) -> Path:
    return WALLETS_DIR / f"{agent_id}.json"


def _transactions_path(agent_id: str) -> Path:
    return TRANSACTIONS_DIR / f"{agent_id}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_wallet(agent_id: str) -> dict:
    path = _wallet_path(agent_id)
    if not path.exists():
        raise ValueError(f"Wallet not found for agent: {agent_id}")
    with open(path) as f:
        return json.load(f)


def _save_wallet(wallet: dict) -> None:
    path = _wallet_path(wallet["agent_id"])
    wallet["updated_at"] = _now()
    with open(path, "w") as f:
        json.dump(wallet, f, indent=2)


def _load_transactions(agent_id: str) -> list[dict]:
    path = _transactions_path(agent_id)
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
        return data.get("transactions", [])


def _save_transactions(agent_id: str, transactions: list[dict]) -> None:
    path = _transactions_path(agent_id)
    with open(path, "w") as f:
        json.dump({"transactions": transactions}, f, indent=2)


def _record_transaction(
    agent_id: str,
    txn_type: str,
    amount: float,
    status: str = "completed",
    source: str = "",
    destination: str = "",
    related_agent: str = "",
    reason: str = "",
    description: str = "",
) -> dict:
    txn = {
        "id": f"txn_{uuid.uuid4().hex[:12]}",
        "type": txn_type,
        "agent_id": agent_id,
        "amount": amount,
        "status": status,
        "source": source,
        "destination": destination,
        "related_agent": related_agent,
        "reason": reason,
        "description": description,
        "timestamp": _now(),
    }
    txns = _load_transactions(agent_id)
    txns.insert(0, txn)  # newest first
    _save_transactions(agent_id, txns)
    return txn


def _next_invoice_number() -> int:
    inv_path = DATA_DIR / "_invoice_counter.json"
    if inv_path.exists():
        with open(inv_path) as f:
            data = json.load(f)
            counter = data.get("counter", 0) + 1
    else:
        counter = 1
    with open(inv_path, "w") as f:
        json.dump({"counter": counter}, f)
    return counter


# ── MCP Server ──────────────────────────────────────────────────────────────

server = Server("agent-wallet")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="wallet_create",
            description="Create a wallet for an agent with an optional initial balance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for the agent",
                    },
                    "initial_balance": {
                        "type": "number",
                        "description": "Initial balance to fund the wallet (default: 0)",
                        "default": 0,
                    },
                },
                "required": ["agent_id"],
            },
        ),
        Tool(
            name="wallet_balance",
            description="Get current balance, pending transactions, and total spent for an agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for the agent",
                    },
                },
                "required": ["agent_id"],
            },
        ),
        Tool(
            name="wallet_deposit",
            description="Add funds to an agent's wallet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for the agent",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to deposit (must be > 0)",
                        "exclusiveMinimum": 0,
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the deposit (e.g., 'payment', 'credit')",
                    },
                },
                "required": ["agent_id", "amount"],
            },
        ),
        Tool(
            name="wallet_withdraw",
            description="Remove funds from an agent's wallet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for the agent",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to withdraw (must be > 0)",
                        "exclusiveMinimum": 0,
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination or purpose of the withdrawal",
                    },
                },
                "required": ["agent_id", "amount"],
            },
        ),
        Tool(
            name="wallet_transfer",
            description="Transfer funds between two agent wallets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_agent_id": {
                        "type": "string",
                        "description": "Source agent identifier",
                    },
                    "to_agent_id": {
                        "type": "string",
                        "description": "Destination agent identifier",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to transfer (must be > 0)",
                        "exclusiveMinimum": 0,
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the transfer",
                    },
                },
                "required": ["from_agent_id", "to_agent_id", "amount"],
            },
        ),
        Tool(
            name="wallet_transactions",
            description="Get recent transactions for an agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for the agent",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recent transactions to return (default: 20)",
                        "default": 20,
                    },
                },
                "required": ["agent_id"],
            },
        ),
        Tool(
            name="wallet_set_budget",
            description="Set a monthly spending limit for an agent. Prevents withdrawals/transfers that would exceed the budget.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for the agent",
                    },
                    "monthly_budget": {
                        "type": "number",
                        "description": "Monthly spending limit. Set to 0 or negative to remove the limit.",
                    },
                },
                "required": ["agent_id", "monthly_budget"],
            },
        ),
        Tool(
            name="wallet_invoice",
            description="Generate an invoice for services rendered between agents. Creates a formal invoice record and optionally records a pending transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_agent_id": {
                        "type": "string",
                        "description": "Agent issuing the invoice (the service provider)",
                    },
                    "to_agent_id": {
                        "type": "string",
                        "description": "Agent being invoiced (the client)",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Invoice amount",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of services rendered",
                    },
                },
                "required": ["from_agent_id", "to_agent_id", "amount", "description"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "wallet_create":
            return [TextContent(type="text", text=_tool_wallet_create(**arguments))]
        elif name == "wallet_balance":
            return [TextContent(type="text", text=_tool_wallet_balance(**arguments))]
        elif name == "wallet_deposit":
            return [TextContent(type="text", text=_tool_wallet_deposit(**arguments))]
        elif name == "wallet_withdraw":
            return [TextContent(type="text", text=_tool_wallet_withdraw(**arguments))]
        elif name == "wallet_transfer":
            return [TextContent(type="text", text=_tool_wallet_transfer(**arguments))]
        elif name == "wallet_transactions":
            return [TextContent(type="text", text=_tool_wallet_transactions(**arguments))]
        elif name == "wallet_set_budget":
            return [TextContent(type="text", text=_tool_wallet_set_budget(**arguments))]
        elif name == "wallet_invoice":
            return [TextContent(type="text", text=_tool_wallet_invoice(**arguments))]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {e}")]


# ── Tool Implementations ────────────────────────────────────────────────────

def _tool_wallet_create(agent_id: str, initial_balance: float = 0) -> str:
    path = _wallet_path(agent_id)
    if path.exists():
        return f"Wallet already exists for agent: {agent_id}"

    wallet = {
        "agent_id": agent_id,
        "balance": initial_balance,
        "monthly_budget": 0,  # 0 = no limit
        "total_spent": 0,
        "created_at": _now(),
        "updated_at": _now(),
    }
    _save_wallet(wallet)

    if initial_balance > 0:
        _record_transaction(
            agent_id=agent_id,
            txn_type="deposit",
            amount=initial_balance,
            source="initial_funding",
        )

    return json.dumps({
        "status": "created",
        "agent_id": agent_id,
        "initial_balance": initial_balance,
    }, indent=2)


def _tool_wallet_balance(agent_id: str) -> str:
    wallet = _load_wallet(agent_id)
    txn_list = _load_transactions(agent_id)
    pending = [t for t in txn_list if t["status"] == "pending"]

    result = {
        "agent_id": agent_id,
        "balance": wallet["balance"],
        "total_spent": wallet["total_spent"],
        "monthly_budget": wallet["monthly_budget"],
        "pending_transactions": len(pending),
        "pending_details": pending[:10] if pending else [],
    }
    return json.dumps(result, indent=2)


def _tool_wallet_deposit(agent_id: str, amount: float, source: str = "") -> str:
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    wallet = _load_wallet(agent_id)
    wallet["balance"] += amount
    _save_wallet(wallet)

    txn = _record_transaction(
        agent_id=agent_id,
        txn_type="deposit",
        amount=amount,
        source=source,
    )

    return json.dumps({
        "status": "deposited",
        "agent_id": agent_id,
        "amount": amount,
        "new_balance": wallet["balance"],
        "transaction_id": txn["id"],
    }, indent=2)


def _tool_wallet_withdraw(agent_id: str, amount: float, destination: str = "") -> str:
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    wallet = _load_wallet(agent_id)

    # Check budget
    if wallet["monthly_budget"] > 0:
        if wallet["total_spent"] + amount > wallet["monthly_budget"]:
            remaining = wallet["monthly_budget"] - wallet["total_spent"]
            raise ValueError(
                f"Withdrawal of {amount} would exceed monthly budget "
                f"({wallet['monthly_budget']}). Remaining budget: {remaining}"
            )

    if wallet["balance"] < amount:
        raise ValueError(
            f"Insufficient balance. Available: {wallet['balance']}, requested: {amount}"
        )

    wallet["balance"] -= amount
    wallet["total_spent"] += amount
    _save_wallet(wallet)

    txn = _record_transaction(
        agent_id=agent_id,
        txn_type="withdraw",
        amount=amount,
        destination=destination,
    )

    return json.dumps({
        "status": "withdrawn",
        "agent_id": agent_id,
        "amount": amount,
        "new_balance": wallet["balance"],
        "total_spent": wallet["total_spent"],
        "transaction_id": txn["id"],
    }, indent=2)


def _tool_wallet_transfer(
    from_agent_id: str,
    to_agent_id: str,
    amount: float,
    reason: str = "",
) -> str:
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if from_agent_id == to_agent_id:
        raise ValueError("Cannot transfer to self")

    from_wallet = _load_wallet(from_agent_id)

    # Check budget on source
    if from_wallet["monthly_budget"] > 0:
        if from_wallet["total_spent"] + amount > from_wallet["monthly_budget"]:
            remaining = from_wallet["monthly_budget"] - from_wallet["total_spent"]
            raise ValueError(
                f"Transfer of {amount} would exceed monthly budget "
                f"({from_wallet['monthly_budget']}). Remaining budget: {remaining}"
            )

    if from_wallet["balance"] < amount:
        raise ValueError(
            f"Insufficient balance in source wallet. "
            f"Available: {from_wallet['balance']}, requested: {amount}"
        )

    to_wallet = _load_wallet(to_agent_id)

    # Perform transfer
    from_wallet["balance"] -= amount
    from_wallet["total_spent"] += amount
    _save_wallet(from_wallet)

    to_wallet["balance"] += amount
    _save_wallet(to_wallet)

    # Record both sides of the transfer
    txn_from = _record_transaction(
        agent_id=from_agent_id,
        txn_type="transfer_out",
        amount=amount,
        related_agent=to_agent_id,
        reason=reason,
    )
    txn_to = _record_transaction(
        agent_id=to_agent_id,
        txn_type="transfer_in",
        amount=amount,
        related_agent=from_agent_id,
        reason=reason,
    )

    return json.dumps({
        "status": "transferred",
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "amount": amount,
        "reason": reason,
        "from_new_balance": from_wallet["balance"],
        "to_new_balance": to_wallet["balance"],
        "from_transaction_id": txn_from["id"],
        "to_transaction_id": txn_to["id"],
    }, indent=2)


def _tool_wallet_transactions(agent_id: str, limit: int = 20) -> str:
    txns = _load_transactions(agent_id)
    limited = txns[:limit]
    return json.dumps({
        "agent_id": agent_id,
        "total_transactions": len(txns),
        "transactions": limited,
    }, indent=2, default=str)


def _tool_wallet_set_budget(agent_id: str, monthly_budget: float) -> str:
    wallet = _load_wallet(agent_id)
    wallet["monthly_budget"] = monthly_budget
    _save_wallet(wallet)

    if monthly_budget <= 0:
        msg = "Monthly budget limit removed"
    else:
        msg = f"Monthly budget set to {monthly_budget}"

    return json.dumps({
        "status": "budget_updated",
        "agent_id": agent_id,
        "monthly_budget": monthly_budget,
        "message": msg,
    }, indent=2)


def _tool_wallet_invoice(
    from_agent_id: str,
    to_agent_id: str,
    amount: float,
    description: str,
) -> str:
    if amount <= 0:
        raise ValueError("Invoice amount must be greater than 0")

    inv_num = _next_invoice_number()
    invoice = {
        "invoice_id": f"INV-{inv_num:06d}",
        "invoice_number": inv_num,
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "amount": amount,
        "description": description,
        "status": "issued",
        "issued_at": _now(),
        "due_at": _now(),  # could be enhanced with payment terms
    }

    inv_path = INVOICES_DIR / f"INV-{inv_num:06d}.json"
    with open(inv_path, "w") as f:
        json.dump(invoice, f, indent=2)

    # Record a pending transaction on the issuer side
    _record_transaction(
        agent_id=from_agent_id,
        txn_type="invoice_issued",
        amount=amount,
        status="pending",
        related_agent=to_agent_id,
        description=description,
    )

    return json.dumps({
        "status": "invoice_created",
        "invoice_id": invoice["invoice_id"],
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "amount": amount,
        "description": description,
        "issued_at": invoice["issued_at"],
    }, indent=2)


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AgentWallet MCP Server — $19/mo (https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)"
    )
    parser.parse_args()

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
