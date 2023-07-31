import datetime
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    advance = "advance"
    payment = "payment"


@dataclass
class Event:
    """A dataclass to store the events.

    Attributes:
        identifier (int): The event's identifier.
        event_type (EventType): The event's type.
        amount (Decimal): The event's amount.
        date_created (datetime.date): The event's date.
    """

    identifier: int
    event_type: EventType
    amount: Decimal
    date_created: datetime.date


@dataclass
class Ledger:
    """A dataclass to store the state of the ledger.

    As we are interested in Advances and the interest, the total_balance is in the inverse state, i.e. if the balance is
    positive, the ledger represents a owned debit, if it is negative, it represents a credit.

    Attributes:
        advance_dates (list[datetime.date]): The dates of the advances.
        advances (list[Decimal]): The advances.
        last_balance_update_date (Optional[datetime.date]): The date of the last balance update.
        total_accrued_interest (Decimal): The total accrued interest.
        total_interest_paid (Decimal): The total interest paid.
        total_balance (Decimal): The total balance.
    """

    advance_dates: list[datetime.date]
    advances: list[Decimal]
    last_balance_update_date: Optional[datetime.date]
    total_accrued_interest: Decimal
    total_interest_paid: Decimal
    total_balance: Decimal
