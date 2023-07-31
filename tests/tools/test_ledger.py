"""I'm more used to pytest, so the tests might be a little more shallower than expected due to lack of
expertise with straight unittest. I'm using test_cli as a reference."""

import unittest
from decimal import Decimal
import datetime

from tools.schemas import Ledger, Event
from tools.ledger import (
    compute_ledger,
    _update_interest,
    _perform_advance,
    _perform_payment,
)


def create_empty_ledger():
    return Ledger([], [], None, Decimal(0), Decimal(0), Decimal(0))


def create_ledger_with_balance_and_no_interest():
    return Ledger(
        [datetime.date(2023, 5, 1)],
        [Decimal(500)],
        datetime.date(2023, 5, 1),
        Decimal(0),
        Decimal(0),
        Decimal(500),
    )


def create_ledger_with_negative_balance():
    return Ledger(
        [datetime.date(2023, 5, 1)],
        [Decimal(500)],
        datetime.date(2023, 5, 1),
        Decimal(0),
        Decimal(0),
        Decimal(-500),
    )


example_events_only_advances = [
    (1, "advance", 500.0, "2023-05-03"),
    (2, "advance", 500.0, "2023-05-04"),
    (3, "advance", 500.0, "2023-05-05"),
]

example_events_only_payments = [
    (1, "payment", 500.0, "2023-05-03"),
    (2, "payment", 500.0, "2023-05-04"),
    (3, "payment", 500.0, "2023-05-05"),
]

example_events_advances_and_payments = [
    (1, "advance", 500.0, "2023-05-03"),
    (2, "payment", 500.0, "2023-05-04"),
    (3, "advance", 500.0, "2023-05-05"),
    (4, "payment", 500.0, "2023-05-06"),
]


class TestLedgers(unittest.TestCase):
    def test_compute_ledger_no_events(self):
        ledger = compute_ledger([], datetime.date.today())
        self.assertEqual(ledger, create_empty_ledger())

    def test_compute_ledger_interest_should_grow(self):
        ledger = compute_ledger(
            example_events_only_advances, datetime.date(2023, 5, 10)
        )
        self.assertGreater(ledger.total_accrued_interest, Decimal(0))
        self.assertEqual(ledger.total_balance, Decimal(1500))
        self.assertEqual(ledger.total_interest_paid, Decimal(0))

    def test_compute_ledger_interest_should_not_grow(self):
        ledger = compute_ledger(
            example_events_only_payments, datetime.date(2023, 5, 10)
        )
        self.assertEqual(ledger.total_accrued_interest, Decimal(0))
        self.assertEqual(ledger.total_balance, Decimal(-1500))
        self.assertEqual(ledger.total_interest_paid, Decimal(0))

    def test_compute_ledger_interest_should_grow_and_be_paid(self):
        ledger = compute_ledger(
            example_events_advances_and_payments, datetime.date(2023, 5, 10)
        )
        self.assertGreater(ledger.total_accrued_interest, Decimal(0))
        self.assertGreater(ledger.total_balance, Decimal(0))
        self.assertGreater(ledger.total_interest_paid, Decimal(0))

    def test_update_interest_interest_should_raise(self):
        ledger = create_ledger_with_balance_and_no_interest()
        date = datetime.date(2023, 5, 2)
        ledger = _update_interest(ledger, date, Decimal(0.00035))
        self.assertGreater(ledger.total_accrued_interest, Decimal(0))

    def test_update_interest_interest_should_not_raise(self):
        ledger = create_ledger_with_negative_balance()
        date = datetime.date(2023, 5, 1)
        ledger = _update_interest(ledger, date, Decimal(0.00035))
        self.assertEqual(ledger.total_accrued_interest, Decimal(0))

    def test_perform_advance_should_increase_balance(self):
        ledger = create_ledger_with_balance_and_no_interest()
        event_data = Event(2, "advance", Decimal(500.0), datetime.date(2023, 5, 4))
        ledger = _perform_advance(ledger, event_data)
        self.assertEqual(ledger.total_balance, Decimal(1000))

    def test_perform_payment_without_interest_should_decrease_balance(self):
        ledger = create_ledger_with_balance_and_no_interest()
        ledger = _perform_payment(ledger, Decimal(500.0))
        self.assertEqual(ledger.total_balance, Decimal(0))

    def test_perform_payment_with_interest_should_decrease_balance_but_no_0(self):
        ledger = create_ledger_with_balance_and_no_interest()
        ledger = _update_interest(ledger, datetime.date(2023, 5, 30), Decimal(0.00035))
        ledger = _perform_payment(ledger, Decimal(500.0))
        self.assertGreater(ledger.total_balance, Decimal(0))
        self.assertGreater(ledger.total_interest_paid, Decimal(0))
        self.assertEqual(ledger.total_accrued_interest, Decimal(0))
