import datetime
from decimal import Decimal

from typing import Optional

from dateutil import parser

from ledger_calculator.schemas import Ledger


def perform_payment(ledger: Ledger, payment_amount: Decimal) -> Ledger:
    if ledger.last_active_balance_index == -1:
        if len(ledger.balances) == 0:
            ledger.positive_balance += payment_amount
            return ledger
        ledger.last_active_balance_index = 0
    while payment_amount > 0:
        last_active_balance = ledger.balances[ledger.last_active_balance_index]
        if ledger.total_accrued_interest > 0:
            if payment_amount > ledger.total_accrued_interest:
                payment_amount -= ledger.total_accrued_interest
                ledger.total_interest_paid += ledger.total_accrued_interest
                ledger.total_accrued_interest = Decimal(0)
            else:
                ledger.total_accrued_interest -= payment_amount
                ledger.total_interest_paid += payment_amount
                payment_amount = 0
                continue
        if last_active_balance > 0:
            if payment_amount > last_active_balance:
                payment_amount -= last_active_balance
                ledger.balances[ledger.last_active_balance_index] = Decimal(0)
            else:
                ledger.balances[ledger.last_active_balance_index] -= payment_amount
                payment_amount = 0
                continue
        if ledger.last_active_balance_index == len(ledger.balances) - 1:
            ledger.positive_balance += payment_amount
            return ledger
        ledger.last_active_balance_index += 1
    return ledger


def update_interest(
    ledger: Ledger, current_date: Optional[datetime.date], interest_rate: Decimal
) -> Ledger:
    """Update the interest accrued in the ledger.

    Function complexity: O[1]

    Args:
        ledger (Ledger): The ledger to update.
        current_date (Optional[datetime.date]): The current date.
        interest_rate (Decimal): The interest rate.

    Returns:
        Ledger: The updated ledger.
    """
    # Check if we actually have any balance in the ledger (Date will be none if no balance).
    if ledger.last_balance_update_date is None:
        return ledger
    # Get the number of days since last update (O[1] operation).
    total_days_since_last_event = (current_date - ledger.last_balance_update_date).days
    # Compute the interest accrued in the period (O[n] operation).
    accrued_interest_in_period = (
        sum(ledger.balances) * interest_rate * total_days_since_last_event
    )
    ledger.total_accrued_interest += accrued_interest_in_period
    ledger.last_balance_update_date = current_date
    return ledger


def get_advances(
    events: list[tuple[int, str, float, str]],
    last_date: datetime.date,
    interest_rate: Decimal = Decimal(0.00035),
) -> Ledger:
    ledger = Ledger([], [], [], None, Decimal(0), -1, Decimal(0), Decimal(0))
    last_date_used = False

    for event in events:
        event_date = parser.parse(event[-1]).date()
        if event_date > last_date:
            # As we want to compute the interest for the last day, we add 1 day to the last date.
            last_date = last_date + datetime.timedelta(days=1)
            ledger = update_interest(ledger, last_date, interest_rate)
            last_date_used = True
            break
        # We update the interest for the current event.
        ledger = update_interest(ledger, event_date, interest_rate)

        if event[1] == "advance":
            ledger.advance_dates.append(event_date)
            ledger.advances.append(Decimal(event[2]))
            advance_value_to_add = Decimal(event[2])
            if ledger.positive_balance > 0:
                if ledger.positive_balance > advance_value_to_add:
                    ledger.positive_balance -= advance_value_to_add
                    advance_value_to_add = 0
                else:
                    advance_value_to_add -= ledger.positive_balance
                    ledger.positive_balance = 0
            ledger.balances.append(advance_value_to_add)
            if ledger.last_balance_update_date is None:
                ledger.last_balance_update_date = event_date

        if event[1] == "payment":
            payment_amount = Decimal(event[2])
            ledger = perform_payment(ledger, payment_amount)

    if not last_date_used:
        # As we want to compute the interest for the last day, we add 1 day to the last date.
        last_date = last_date + datetime.timedelta(days=1)
        ledger = update_interest(ledger, last_date, interest_rate)

    return ledger
