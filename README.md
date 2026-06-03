# AgentWallet MCP

Your agent can maintain its own sandboxed spend ledger, enforce monthly budgets on itself, transfer funds to other agents, and generate formal invoices — all without touching your financial accounts.

The wallet is a local numeric ledger (stored in `~/.agentwallet/`). It is not connected to any bank, payment processor, or blockchain. Use it to model agent-to-agent accounting and spending limits within your own infrastructure.

## What your agent can do

- Create a wallet for any agent ID and fund it with an initial balance
- Check current balance, monthly spend total, and pending transactions at any time
- Deposit and withdraw from any wallet, with automatic budget enforcement on withdrawal
- Transfer between two agent wallets in a single atomic operation — both sides recorded
- Set a hard monthly spending cap: withdrawals and transfers that would exceed it are rejected at the time of the call
- Generate numbered invoice records (`INV-000001`, etc.) for agent-to-agent service billing

## Installation

**Requires:** Python 3.10+, `mcp` package.

```bash
pip install mcp
```

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "agent-wallet": {
      "command": "python",
      "args": ["/absolute/path/to/agent-wallet-mcp/server.py"]
    }
  }
}
```

**Cursor** — add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "agent-wallet": {
      "command": "python",
      "args": ["/absolute/path/to/agent-wallet-mcp/server.py"]
    }
  }
}
```

## Tool Reference

| Tool | Description | Key params |
|------|-------------|------------|
| `wallet_create` | Create a new wallet for an agent | `agent_id` (required), `initial_balance` (default: 0) |
| `wallet_balance` | Get balance, total spent, monthly budget, and pending count | `agent_id` |
| `wallet_deposit` | Add funds to a wallet | `agent_id`, `amount`, `source` |
| `wallet_withdraw` | Remove funds; rejected if monthly budget would be exceeded | `agent_id`, `amount`, `destination` |
| `wallet_transfer` | Move funds between two wallets atomically; honors source budget | `from_agent_id`, `to_agent_id`, `amount`, `reason` |
| `wallet_transactions` | Recent transaction history, newest first | `agent_id`, `limit` (default: 20) |
| `wallet_set_budget` | Set or remove monthly spending cap (0 = no limit) | `agent_id`, `monthly_budget` |
| `wallet_invoice` | Generate a numbered invoice record between two agents | `from_agent_id`, `to_agent_id`, `amount`, `description` |

## Data Storage

```
~/.agentwallet/
├── wallets/
│   └── <agent_id>.json        # balance, budget, total_spent
├── transactions/
│   └── <agent_id>.json        # full transaction history
├── invoices/
│   └── INV-000001.json        # invoice records
└── _invoice_counter.json      # auto-incrementing invoice number
```

## Budget Enforcement

When `monthly_budget > 0`, the server rejects any withdrawal or transfer where `total_spent + amount > monthly_budget`. The check runs synchronously before the balance is modified. Set `monthly_budget` to `0` to remove the limit.

## Pricing

| Plan | Price | Included |
|------|-------|----------|
| Pro | $19/month | Unlimited wallets, transactions, and invoices |

[Subscribe via Stripe](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

## License

Proprietary — see subscription terms. Source: [github.com/Rumblingb/agent-wallet-mcp](https://github.com/Rumblingb/agent-wallet-mcp)
