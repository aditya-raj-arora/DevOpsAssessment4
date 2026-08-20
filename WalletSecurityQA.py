import unittest
import threading
from datetime import datetime, timedelta
from DigitalWallet import DigitalWallet


class TestNormalTransaction(unittest.TestCase):
    def test_deposit_and_withdraw(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=1000)
        wallet.deposit("A1", 500)
        balance = wallet.withdraw("A1", "1234", 300)
        self.assertEqual(balance, 1200)
        self.assertEqual(len(wallet.get_transaction_history("A1")), 2)


class TestInsufficientBalance(unittest.TestCase):
    def test_withdraw_more_than_balance(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=100)
        with self.assertRaises(ValueError):
            wallet.withdraw("A1", "1234", 500)


class TestDailyLimit(unittest.TestCase):
    def test_daily_limit_exceeded(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=100000, daily_limit=1000)
        wallet.withdraw("A1", "1234", 600)
        with self.assertRaises(ValueError):
            wallet.withdraw("A1", "1234", 500)


class TestMultipleFailedPins(unittest.TestCase):
    def test_account_locks_after_three_failed_attempts(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=1000)
        for _ in range(3):
            with self.assertRaises(PermissionError):
                wallet.withdraw("A1", "0000", 10)
        with self.assertRaises(PermissionError):
            wallet.withdraw("A1", "1234", 10)
        self.assertTrue(wallet.is_flagged("A1"))


class TestSuspiciousTransaction(unittest.TestCase):
    def test_large_transaction_flagged(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=500000, daily_limit=1000000)
        wallet.withdraw("A1", "1234", 150000)
        self.assertTrue(wallet.is_flagged("A1"))

    def test_high_frequency_flagged(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=100000, daily_limit=100000)
        base = datetime(2026, 1, 1, 10, 0, 0)
        for i in range(6):
            wallet.deposit("A1", 100, timestamp=base + timedelta(minutes=i))
        self.assertTrue(wallet.is_flagged("A1"))


class TestDuplicateTransaction(unittest.TestCase):
    def test_duplicate_transaction_flagged(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=1000)
        ts = datetime(2026, 1, 1, 10, 0, 0)
        wallet.deposit("A1", 200, timestamp=ts)
        wallet.deposit("A1", 200, timestamp=ts + timedelta(seconds=2))
        self.assertTrue(wallet.is_flagged("A1"))
        reasons = [f["reasons"] for f in wallet.get_flags("A1") if f["type"] == "SUSPICIOUS_TRANSACTION"]
        self.assertTrue(any("DUPLICATE_TRANSACTION" in r for r in reasons))


class TestNegativeAmount(unittest.TestCase):
    def test_negative_deposit_rejected(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=1000)
        with self.assertRaises(ValueError):
            wallet.deposit("A1", -50)

    def test_negative_withdrawal_rejected(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=1000)
        with self.assertRaises(ValueError):
            wallet.withdraw("A1", "1234", -50)


class TestConcurrentTransactions(unittest.TestCase):
    def test_concurrent_withdrawals_do_not_overdraw(self):
        wallet = DigitalWallet()
        wallet.create_account("A1", "1234", initial_balance=1000, daily_limit=1000000)
        errors = []

        def do_withdraw():
            try:
                wallet.withdraw("A1", "1234", 100)
            except ValueError:
                errors.append("insufficient")

        threads = [threading.Thread(target=do_withdraw) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(wallet.verify_balance("A1", "1234"), 0)
        self.assertEqual(len(errors), 10)


if __name__ == "__main__":
    unittest.main()
