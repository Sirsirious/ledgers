import datetime
from decimal import Decimal

from typing import Optional

from dateutil import parser

from tools.schemas import Ledger, Event


def _perform_payment(ledger: Ledger, payment_amount: Decimal) -> Ledger:
    """Add a payment to the ledger.

    The process is: first we pay the accrued interest, then we pay the balances.

    Args:
        ledger (Ledger): The ledger.
        payment_amount (Decimal): The payment amount.

    Returns:
        Ledger: The updated ledger.
    """
    if ledger.total_balance <= 0:
        # If the balance is 0, we add the payment to the total interest paid.
        ledger.total_balance -= payment_amount
        return ledger
    if ledger.total_accrued_interest > 0:
        if payment_amount > ledger.total_accrued_interest:
            payment_amount -= ledger.total_accrued_interest
            ledger.total_interest_paid += ledger.total_accrued_interest
            ledger.total_accrued_interest = Decimal(0)
        else:
            ledger.total_accrued_interest -= payment_amount
            ledger.total_interest_paid += payment_amount
            return ledger
        ledger.total_balance -= payment_amount
    elif ledger.total_balance > 0:
        ledger.total_balance -= payment_amount
    return ledger


def _perform_advance(ledger: Ledger, event_data: Event) -> Ledger:
    """Add an advance to the ledger.

    Function complexity: O[1] (average case, assuming the list is not full).

    Args:
        ledger (Ledger): The ledger to update.
        event_data (Event): The event data.

    Returns:
        Ledger: The updated ledger.
    """
    ledger.advance_dates.append(event_data.date_created)
    ledger.advances.append(event_data.amount)
    ledger.total_balance += event_data.amount
    if ledger.last_balance_update_date is None:
        ledger.last_balance_update_date = event_data.date_created
    return ledger


def _update_interest(
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
    if ledger.total_balance <= 0:
        # We don't need to update the interest if we don't have any balance, but we do need to update the date.
        ledger.last_balance_update_date = current_date
        return ledger
    # Get the number of days since last update (O[1] operation).
    total_days_since_last_event = (current_date - ledger.last_balance_update_date).days
    if total_days_since_last_event > 0:
        # Compute the interest accrued in the period (O[1] operation).
        accrued_interest_in_period = (
            ledger.total_balance * interest_rate * total_days_since_last_event
        )
        ledger.total_accrued_interest += accrued_interest_in_period
    ledger.last_balance_update_date = current_date
    return ledger


def _parse_event_tuple(event: tuple[int, str, float, str]) -> Event:
    """Parse the event tuple into an Event object.

    Args:
        event (tuple[int, str, float, str]): The event tuple.

    Returns:
        Event: The parsed event.
    """
    event_date = parser.parse(event[-1]).date()
    amount = Decimal(event[2])
    return Event(event[0], event[1], amount, event_date)


def compute_ledger(
    events: list[tuple[int, str, float, str]],
    last_date: datetime.date,
    interest_rate: Decimal = Decimal(0.00035),
) -> Ledger:
    """Compute the advancement and balance ledger.

    Function complexity: O[n] (where n is the number of events). Capped by the last_date (it can be O[1] if last_date
    is less than the first operation). There are some rare situations where the solution can be a little more complex
    (as when lists overflow and need to be recomputed) - but that is related to python's limitations (unless we
    implemented our own linked list solution, which would be overkill).

    Args:
        events (list[tuple[int, str, float, str]]): The events.
        last_date (datetime.date): The last date to compute the interest.
        interest_rate (Decimal, optional): The interest rate. Defaults to Decimal(0.00035).

    Returns:
        Ledger: The ledger dataclass with the information to display the balance.

    """
    ledger = Ledger([], [], None, Decimal(0), Decimal(0), Decimal(0))
    last_date_used = False

    for event in events:
        parsed_event = _parse_event_tuple(event)
        if parsed_event.date_created > last_date:
            # As we want to compute the interest for the last day, we add 1 day to the last date.
            last_date = last_date + datetime.timedelta(days=1)
            ledger = _update_interest(ledger, last_date, interest_rate)
            last_date_used = True
            break
        # We update the interest for the current event.
        ledger = _update_interest(ledger, parsed_event.date_created, interest_rate)

        if parsed_event.event_type == "advance":
            ledger = _perform_advance(ledger, parsed_event)

        else:
            ledger = _perform_payment(ledger, parsed_event.amount)

    if not last_date_used:
        # As we want to compute the interest for the last day, we add 1 day to the last date.
        last_date = last_date + datetime.timedelta(days=1)
        ledger = _update_interest(ledger, last_date, interest_rate)

    return ledger


def format_remaining_balances(
    advances: list[Decimal], total_balance: Decimal
) -> list[Decimal]:
    if total_balance <= 0:
        return [Decimal(0)] * len(advances)
    value_subtracted = sum(advances) - total_balance
    remaining_balances = []
    for advance in advances:
        if value_subtracted > advance:
            value_subtracted -= advance
            remaining_balances.append(Decimal(0))
        else:
            remaining_balances.append(advance - value_subtracted)
            value_subtracted = Decimal(0)
    return remaining_balances
