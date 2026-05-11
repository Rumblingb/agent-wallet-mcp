# AgentWallet MCP Server

A Model Context Protocol (MCP) server for agent wallet and budget management.  
Agents can create wallets, track spending, set budgets, transfer funds, and generate invoices.

**Pricing:** $19/month  
**Subscribe:** [https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

---

## Overview

AgentWallet provides a simple JSON-file-based wallet system for AI agents.  
Each agent gets its own wallet with balance tracking, transaction history, monthly budgets, and invoice generation. All data is stored locally in `~/.agentwallet/`.

---

## Tools

### 1. `wallet_create`
Create a wallet for an agent.

| Parameter       | Type   | Required | Default | Description                    |
|-----------------|--------|----------|---------|--------------------------------|
| `agent_id`      | string | yes      | —       | Unique identifier for the agent |
| `initial_balance` | number | no     | 0       | Initial funding amount          |

### 2. `wallet_balance`
Get current wallet state.

| Parameter   | Type   | Required | Description                    |
|-------------|--------|----------|--------------------------------|
| `agent_id`  | string | yes      | Unique identifier for the agent |

Returns: balance, total_spent, monthly_budget, pending_transactions.

### 3. `wallet_deposit`
Add funds to an agent's wallet.

| Parameter   | Type   | Required | Default | Description                         |
|-------------|--------|----------|---------|-------------------------------------|
| `agent_id`  | string | yes      | —       | Unique identifier for the agent      |
| `amount`    | number | yes      | —       | Amount to deposit (> 0)             |
| `source`    | string | no       | ""      | Source description (e.g. "payment") |

### 4. `wallet_withdraw`
Remove funds from an agent's wallet. Enforces monthly budget if set.

| Parameter     | Type   | Required | Default | Description                          |
|---------------|--------|----------|---------|--------------------------------------|
| `agent_id`    | string | yes      | —       | Unique identifier for the agent       |
| `amount`      | number | yes      | —       | Amount to withdraw (> 0)             |
| `destination` | string | no       | ""      | Destination or purpose                |

### 5. `wallet_transfer`
Transfer funds between two agent wallets. Honors budget limits on source.

| Parameter       | Type   | Required | Default | Description                   |
|-----------------|--------|----------|---------|-------------------------------|
| `from_agent_id` | string | yes      | —       | Source agent identifier        |
| `to_agent_id`   | string | yes      | —       | Destination agent identifier   |
| `amount`        | number | yes      | —       | Amount to transfer (> 0)      |
| `reason`        | string | no       | ""      | Reason for the transfer        |

### 6. `wallet_transactions`
Get recent transactions for an agent (newest first).

| Parameter   | Type   | Required | Default | Description                          |
|-------------|--------|----------|---------|--------------------------------------|
| `agent_id`  | string | yes      | —       | Unique identifier for the agent       |
| `limit`     | integer| no       | 20      | Max number of transactions to return  |

### 7. `wallet_set_budget`
Set a monthly spending limit for an agent. Set to 0 or negative to remove limit.

| Parameter       | Type   | Required | Description                                    |
|-----------------|--------|----------|------------------------------------------------|
| `agent_id`      | string | yes      | Unique identifier for the agent                 |
| `monthly_budget` | number | yes      | Monthly spending limit (0 = no limit)           |

### 8. `wallet_invoice`
Generate an invoice for services rendered between agents.

| Parameter     | Type   | Required | Description                      |
|---------------|--------|----------|----------------------------------|
| `from_agent_id` | string | yes    | Agent issuing the invoice         |
| `to_agent_id`   | string | yes    | Agent being invoiced              |
| `amount`      | number | yes      | Invoice amount                    |
| `description` | string | yes      | Description of services rendered  |

---

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run with any MCP-compatible client (Claude Desktop, etc.) or stdio transport:

```bash
python server.py
```

### Example (Claude Desktop config)

```json
{
  "mcpServers": {
    "agent-wallet": {
      "command": "python",
      "args": ["/path/to/agent-wallet-mcp/server.py"]
    }
  }
}
```

### Example (raw stdio test)

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"wallet_create","arguments":{"agent_id":"agent-1","initial_balance":1000}}}' | python server.py
```

---

## Data Storage

All data is stored as JSON files in `~/.agentwallet/`:

```
~/.agentwallet/
├── wallets/
│   └── <agent_id>.json          # Wallet state (balance, budget, totals)
├── transactions/
│   └── <agent_id>.json          # Transaction history per agent
├── invoices/
│   └── INV-000001.json          # Generated invoices
└── _invoice_counter.json         # Auto-incrementing invoice counter
```

---

## Budget Enforcement

When a `monthly_budget` is set via `wallet_set_budget`, the server enforces it:

- **Withdrawals** (`wallet_withdraw`) are rejected if `total_spent + amount > monthly_budget`
- **Transfers** (`wallet_transfer`) are rejected if the source agent would exceed its budget
- Set `monthly_budget` to `0` or a negative value to remove the limit

---

## Subscription

**$19/month** | [Subscribe via Stripe](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

---

## License

Proprietary — see subscription terms.
