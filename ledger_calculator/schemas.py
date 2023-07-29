from dataclasses import dataclass
from typing import Optional


@dataclass
class Ledger:
    advance_dates: list[datetime.date]
    advances: list[Decimal]
    balances: list[Decimal]
    last_balance_update_date: Optional[datetime.date]
    total_accrued_interest: Decimal
    last_active_balance_index: int
    positive_balance: Decimal
    total_interest_paid: Decimal
