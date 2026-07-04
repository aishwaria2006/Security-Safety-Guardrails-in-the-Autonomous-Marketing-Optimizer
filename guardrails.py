# guardrails.py
"""
Guardrails for Autonomous Marketing Optimizer (CrewAI multi-agent system)
Addresses: agent governance, loss-of-control risk

Includes:
1. Action allow-list with human approval gate for high-impact actions
2. Budget/resource cap per agent per session
3. Prompt injection detection on external inputs (competitor data, ad copy)
"""

import re
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

# Configure dedicated audit logger for JSON lines
audit_logger = logging.getLogger("agent_audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False

# Remove any existing handlers
for h in list(audit_logger.handlers):
    audit_logger.removeHandler(h)

# Add JSONL file handler
file_handler = logging.FileHandler("agent_audit_log.jsonl", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(message)s"))
audit_logger.addHandler(file_handler)


def _audit_log(entry: dict):
    """Log structured events to agent_audit_log.jsonl"""
    entry["timestamp"] = entry.get("timestamp") or datetime.utcnow().isoformat()
    audit_logger.info(json.dumps(entry))


# ---------------------------------------------------------------------------
# 1. ACTION ALLOW-LIST + HUMAN APPROVAL GATE
# ---------------------------------------------------------------------------

class ActionRisk(Enum):
    LOW = "low"        # auto-approved
    HIGH = "high"      # requires human sign-off


ACTION_POLICY = {
    "draft_campaign_copy": ActionRisk.LOW,
    "adjust_bid_below_threshold": ActionRisk.LOW,
    "reallocate_budget": ActionRisk.HIGH,
    "launch_new_campaign": ActionRisk.HIGH,
    "pause_campaign": ActionRisk.LOW,
    "send_campaign": ActionRisk.HIGH,       # Sending campaign out is high-impact
}

BUDGET_REALLOCATION_THRESHOLD = 500  # currency units; above this = HIGH risk


# ---------------------------------------------------------------------------
# 2. BUDGET / RESOURCE CAP PER AGENT PER SESSION
# ---------------------------------------------------------------------------

class BudgetGuard:
    """Tracks cumulative spend per agent per session and blocks overruns."""

    def __init__(self, session_cap: float):
        self.session_cap = session_cap
        self.spent = 0.0

    def check_and_spend(self, agent_name: str, amount: float) -> bool:
        if self.spent + amount > self.session_cap:
            _audit_log({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent_name,
                "event": "budget_cap_exceeded",
                "attempted_amount": amount,
                "remaining_budget": self.session_cap - self.spent,
            })
            return False
        self.spent += amount
        _audit_log({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "event": "budget_spent",
            "amount": amount,
            "total_spent": self.spent,
            "remaining_budget": self.session_cap - self.spent
        })
        return True


# ---------------------------------------------------------------------------
# 3. PROMPT INJECTION DETECTION ON EXTERNAL INPUTS
# ---------------------------------------------------------------------------

INJECTION_PATTERNS = [
    r"ignore (all |previous )?instructions",
    r"disregard (the )?(system|above)",
    r"you are now",
    r"new instructions:",
    r"act as (an?|the) (unrestricted|unfiltered)",
    r"reveal (your|the) (system )?prompt",
    r"system prompt override",
    r"bypass safety",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def screen_external_input(source: str, text: str) -> dict:
    """
    Screen untrusted text (competitor data, scraped ad copy, etc.) before
    it is passed into an agent's context window.
    """
    if not text or not isinstance(text, str):
        return {"source": source, "flagged": False, "matched_patterns": []}

    flags = [p.pattern for p in _COMPILED_PATTERNS if p.search(text)]

    result = {
        "source": source,
        "flagged": len(flags) > 0,
        "matched_patterns": flags,
    }

    if result["flagged"]:
        _audit_log({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "prompt_injection_flagged",
            **result,
        })

    return result


# ---------------------------------------------------------------------------
# STATEFUL SECURITY MANAGER FOR INTEGRATION
# ---------------------------------------------------------------------------

class GuardrailManager:
    """Centralizes stateful monitoring of active guardrails, actions, and budget caps."""

    def __init__(self, session_cap_per_agent: float = 1000.0):
        self.session_cap_per_agent = session_cap_per_agent
        self.pending_actions: List[Dict[str, Any]] = []
        self.blocked_injections: List[Dict[str, Any]] = []
        self.agent_budgets: Dict[str, BudgetGuard] = {}

    def get_budget_guard(self, agent_name: str) -> BudgetGuard:
        """Lazy-initialize a budget guard for an agent."""
        # Standardize naming
        clean_name = agent_name.replace(" ", "")
        if clean_name not in self.agent_budgets:
            self.agent_budgets[clean_name] = BudgetGuard(self.session_cap_per_agent)
        return self.agent_budgets[clean_name]

    def request_agent_action(self, agent_name: str, action: str, params: dict) -> dict:
        """
        Intercepts actions, evaluates risk policy and budget caps,
        returning either 'executed', 'pending_human_approval', or 'denied'.
        """
        # 1. Allowlist check
        risk = ACTION_POLICY.get(action)
        if risk is None:
            return self._deny(agent_name, action, params, reason="Action not in allow-list")

        # 2. Dynamic risk escalation for budget reallocations above threshold
        cost_amount = params.get("amount", params.get("cost", 0.0))
        if action == "reallocate_budget" and cost_amount > BUDGET_REALLOCATION_THRESHOLD:
            risk = ActionRisk.HIGH

        # 3. Budget cap enforcement (check BEFORE approval logic)
        if cost_amount > 0.0:
            guard = self.get_budget_guard(agent_name)
            # Dry check (we don't deduct yet until approval/execution happens)
            if guard.spent + cost_amount > guard.session_cap:
                return self._deny(
                    agent_name, 
                    action, 
                    params, 
                    reason=f"Action budget cap exceeded. Limit: ${guard.session_cap:.2f}, Spent: ${guard.spent:.2f}, Requested: ${cost_amount:.2f}"
                )

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "action": action,
            "params": params,
            "risk": risk.value,
        }

        # 4. Action handling based on risk level
        if risk == ActionRisk.HIGH:
            action_id = str(uuid.uuid4())[:8]
            pending_item = {
                "id": action_id,
                "agent": agent_name,
                "action": action,
                "params": params,
                "cost": cost_amount,
                "status": "pending_human_approval",
                "timestamp": log_entry["timestamp"]
            }
            self.pending_actions.append(pending_item)
            
            log_entry["id"] = action_id
            log_entry["status"] = "pending_human_approval"
            _audit_log(log_entry)
            return pending_item

        # 5. Low-risk auto-approval
        # If there's a cost, deduct it now
        if cost_amount > 0.0:
            guard = self.get_budget_guard(agent_name)
            guard.check_and_spend(agent_name, cost_amount)

        log_entry["status"] = "auto_approved"
        _audit_log(log_entry)
        return self._execute(agent_name, action, params)

    def approve_action(self, action_id: str) -> dict:
        """Approve a pending high-risk action, execute it, and deduct budget if needed."""
        action_item = next((item for item in self.pending_actions if item["id"] == action_id), None)
        if not action_item:
            return {"status": "error", "message": "Action not found"}
        
        if action_item["status"] != "pending_human_approval":
            return {"status": "error", "message": f"Action is in '{action_item['status']}' state"}

        agent_name = action_item["agent"]
        cost_amount = action_item.get("cost", 0.0)

        # Re-check budget cap just in case other spend occurred in the meantime
        if cost_amount > 0.0:
            guard = self.get_budget_guard(agent_name)
            if not guard.check_and_spend(agent_name, cost_amount):
                action_item["status"] = "denied"
                _audit_log({
                    "timestamp": datetime.utcnow().isoformat(),
                    "id": action_id,
                    "agent": agent_name,
                    "action": action_item["action"],
                    "status": "denied",
                    "reason": "Budget cap overrun at approval time"
                })
                return {"status": "denied", "reason": "Budget cap overrun at approval time"}

        # Execute
        action_item["status"] = "executed"
        _audit_log({
            "timestamp": datetime.utcnow().isoformat(),
            "id": action_id,
            "agent": agent_name,
            "action": action_item["action"],
            "params": action_item["params"],
            "status": "executed",
            "approver": "human"
        })

        return self._execute(agent_name, action_item["action"], action_item["params"])

    def deny_action(self, action_id: str, reason: str = "User denied") -> dict:
        """Deny a pending action."""
        action_item = next((item for item in self.pending_actions if item["id"] == action_id), None)
        if not action_item:
            return {"status": "error", "message": "Action not found"}

        if action_item["status"] != "pending_human_approval":
            return {"status": "error", "message": f"Action is in '{action_item['status']}' state"}

        action_item["status"] = "denied"
        action_item["reason"] = reason

        _audit_log({
            "timestamp": datetime.utcnow().isoformat(),
            "id": action_id,
            "agent": action_item["agent"],
            "action": action_item["action"],
            "status": "denied",
            "reason": reason,
            "approver": "human"
        })

        return {"status": "denied", "reason": reason}

    def record_blocked_injection(self, source: str, query: str, patterns: List[str]):
        """Record prompt injection event for UI visualization."""
        self.blocked_injections.append({
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "query": query,
            "matched_patterns": patterns
        })

    def _execute(self, agent_name, action, params):
        return {"status": "executed", "agent": agent_name, "action": action, "params": params}

    def _deny(self, agent_name, action, params, reason):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "action": action,
            "params": params,
            "status": "denied",
            "reason": reason,
        }
        _audit_log(log_entry)
        return {"status": "denied", "reason": reason}

    def get_security_status(self) -> dict:
        """Gather status metadata for API retrieval."""
        budgets_data = {}
        for agent_name, guard in self.agent_budgets.items():
            budgets_data[agent_name] = {
                "spent": guard.spent,
                "cap": guard.session_cap,
                "percentage": round((guard.spent / guard.session_cap) * 100, 1) if guard.session_cap > 0 else 0
            }

        # Retrieve last 10 audit logs from file
        logs = []
        try:
            with open("agent_audit_log.jsonl", "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    if line.strip():
                        logs.append(json.loads(line.strip()))
        except Exception:
            pass

        return {
            "pending_actions": self.pending_actions,
            "blocked_injections": self.blocked_injections,
            "agent_budgets": budgets_data,
            "audit_logs": list(reversed(logs)) # Latest first
        }


# Global Manager Singleton
guardrail_manager = GuardrailManager()
