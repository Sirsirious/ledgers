import datetime
from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    advance = "advance"
    payment = "payment"


@dataclass
class Event:
    identifier: int
    event_type: EventType
    amount: float
    date_created: datetime.date


@dataclass
class EventWithDuration(Event):
    number_of_days: int


@dataclass
class LedgerState:
    current_balance: float
    interest_accrued: float
    total_sum_of_unpaid_intrest: float
    evaluation_date: datetime.date
    total_number_of_days: int

    @property
    def daily_accrued_interest(self) -> float:
        return self.interest_accrued / self.total_number_of_days
