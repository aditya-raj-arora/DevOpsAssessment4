import threading
from datetime import datetime, timedelta

LARGE_TRANSACTION_THRESHOLD = 100000
HIGH_FREQUENCY_WINDOW_MINUTES = 10
HIGH_FREQUENCY_MAX_COUNT = 5
MAX_FAILED_PIN_ATTEMPTS = 3
UNUSUAL_AMOUNT_MULTIPLIER = 5
DUPLICATE_WINDOW_SECONDS = 5


class DigitalWallet:
    def __init__(self):
        self.accounts = {}
        self.lock = threading.Lock()

    def create_account(self, account_id, pin, initial_balance=0.0, daily_limit=50000.0):
        if account_id in self.accounts:
            raise ValueError("Account already exists")
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.accounts[account_id] = {
            "pin": pin,
            "balance": initial_balance,
            "daily_limit": daily_limit,
            "transactions": [],
            "failed_pin_attempts": 0,
            "locked": False,
            "flags": [],
        }
        return True

    def _get_account(self, account_id):
        if account_id not in self.accounts:
            raise ValueError("Account does not exist")
        return self.accounts[account_id]

    def _verify_pin(self, account_id, pin, timestamp=None):
        timestamp = timestamp or datetime.now()
        account = self._get_account(account_id)
        if account["locked"]:
            raise PermissionError("Account locked due to multiple failed PIN attempts")
        if account["pin"] != pin:
            account["failed_pin_attempts"] += 1
            if account["failed_pin_attempts"] >= MAX_FAILED_PIN_ATTEMPTS:
                account["locked"] = True
                account["flags"].append({"type": "MULTIPLE_FAILED_PIN", "timestamp": timestamp})
            raise PermissionError("Invalid PIN")
        account["failed_pin_attempts"] = 0
        return True

    def _daily_total(self, account, timestamp):
        day = timestamp.date()
        return sum(
            t["amount"] for t in account["transactions"]
            if t["timestamp"].date() == day and t["type"] in ("WITHDRAW", "TRANSFER_OUT")
        )

    def _check_fraud(self, account, txn, timestamp):
        reasons = []
        recent = [t for t in account["transactions"] if timestamp - t["timestamp"] <= timedelta(minutes=HIGH_FREQUENCY_WINDOW_MINUTES)]
        if len(recent) >= HIGH_FREQUENCY_MAX_COUNT:
            reasons.append("HIGH_FREQUENCY")
        if txn["amount"] >= LARGE_TRANSACTION_THRESHOLD:
            reasons.append("LARGE_TRANSACTION")
        amounts = [t["amount"] for t in account["transactions"]]
        if amounts:
            avg = sum(amounts) / len(amounts)
            if avg > 0 and txn["amount"] >= avg * UNUSUAL_AMOUNT_MULTIPLIER:
                reasons.append("UNUSUAL_AMOUNT")
        last_same = [
            t for t in account["transactions"]
            if t["type"] == txn["type"] and t["amount"] == txn["amount"]
            and timestamp - t["timestamp"] <= timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
        ]
        if last_same:
            reasons.append("DUPLICATE_TRANSACTION")
        if reasons:
            txn["suspicious"] = True
            account["flags"].append({"type": "SUSPICIOUS_TRANSACTION", "reasons": reasons, "timestamp": timestamp})
        return reasons

    def _record_transaction(self, account_id, txn_type, amount, timestamp=None):
        timestamp = timestamp or datetime.now()
        account = self._get_account(account_id)
        txn = {"type": txn_type, "amount": amount, "timestamp": timestamp, "suspicious": False}
        self._check_fraud(account, txn, timestamp)
        account["transactions"].append(txn)
        return txn

    def deposit(self, account_id, amount, timestamp=None):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        timestamp = timestamp or datetime.now()
        with self.lock:
            account = self._get_account(account_id)
            account["balance"] += amount
            self._record_transaction(account_id, "DEPOSIT", amount, timestamp)
            return account["balance"]

    def withdraw(self, account_id, pin, amount, timestamp=None):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        timestamp = timestamp or datetime.now()
        with self.lock:
            self._verify_pin(account_id, pin, timestamp)
            account = self._get_account(account_id)
            if amount > account["balance"]:
                raise ValueError("Insufficient balance")
            if self._daily_total(account, timestamp) + amount > account["daily_limit"]:
                raise ValueError("Daily transaction limit exceeded")
            account["balance"] -= amount
            self._record_transaction(account_id, "WITHDRAW", amount, timestamp)
            return account["balance"]

    def transfer(self, from_id, pin, to_id, amount, timestamp=None):
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        timestamp = timestamp or datetime.now()
        with self.lock:
            self._verify_pin(from_id, pin, timestamp)
            from_account = self._get_account(from_id)
            to_account = self._get_account(to_id)
            if amount > from_account["balance"]:
                raise ValueError("Insufficient balance")
            if self._daily_total(from_account, timestamp) + amount > from_account["daily_limit"]:
                raise ValueError("Daily transaction limit exceeded")
            from_account["balance"] -= amount
            to_account["balance"] += amount
            self._record_transaction(from_id, "TRANSFER_OUT", amount, timestamp)
            self._record_transaction(to_id, "TRANSFER_IN", amount, timestamp)
            return from_account["balance"]

    def get_transaction_history(self, account_id):
        return list(self._get_account(account_id)["transactions"])

    def verify_balance(self, account_id, pin):
        self._verify_pin(account_id, pin)
        return self._get_account(account_id)["balance"]

    def is_flagged(self, account_id):
        return len(self._get_account(account_id)["flags"]) > 0

    def get_flags(self, account_id):
        return list(self._get_account(account_id)["flags"])
