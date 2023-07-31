"""Left files here for reference regarding code styling and best practices. 
The original understanding behidn these was wrong.


This was the code in cli.py:


# First let us summarize the events by day. As we charge interest on a daily basis, we'll count the balance only
# at the end of the day.
events_resumed_by_day = resume_events_by_day(events)
# Now let us compute the number of days between each event. This will be used to compute the interest.
days_between_events = compute_days_between_events(
    events_resumed_by_day, parser.parse(end_date).date()
)
# Packing together
events_with_duration = add_event_duration_to_events(
    events_resumed_by_day, days_between_events
)
# Now let us compute the interest for each event.
interest_values = compute_interest(
    events_with_duration,
)
"""
import datetime
from dataclasses import asdict
from typing import Optional

from dateutil import parser

from tools.unused_files.wrong_dataclasses import (
    EventType,
    Event,
    EventWithDuration,
    LedgerState,
)


def resume_events_by_day(events: list[tuple[int, str, float, str]]) -> list[Event]:
    """Return a list of events with a single event summarizing a day's balance."""
    if not events:
        return []
    events_by_day = []
    # Parsing dates from ISO strings as we can use comparison operators on them.
    events_with_parsed_dates = [
        (event[0], event[1], event[2], parser.parse(event[3]).date())
        for event in events
    ]
    # We group events by date.
    distinct_dates = set([event[3] for event in events_with_parsed_dates])
    # As sets are arbitrarily ordered, we sort the dates.
    sorted_distinct_dates = sorted(distinct_dates)
    grouped_events_by_date = [
        [event for event in events_with_parsed_dates if event[3] == date]
        for date in sorted_distinct_dates
    ]
    # We summarize each day's balance.
    for event_index, event_group in enumerate(grouped_events_by_date):
        event_group_balance = 0
        event_group_date = event_group[0][
            3
        ]  # We can use the first event's date as they all have the same date.
        for event in event_group:
            event_type = event[1]
            event_value = event[2]
            if event_type == "advance":
                event_group_balance -= event_value
            elif event_type == "payment":
                event_group_balance += event_value
        event_group_type = (
            EventType.advance if event_group_balance < 0 else EventType.payment
        )
        events_by_day.append(
            Event(
                identifier=event_index,
                event_type=event_group_type,
                amount=abs(event_group_balance),
                date_created=event_group_date,
            )
        )
    return events_by_day


def compute_days_between_events(
    events: list[Event], end_date: datetime.date
) -> list[int]:
    """Returns a list of days between events.

    Used to compute the Daily Accrued Interest and Payable Balance.

    Args:
        events (list): List of events.
        end_date (datetime): End date of the period.

    Returns:
        list: List of days between events.
    """
    if not events:
        return []
    days_between_events = []
    # If the end date is before the first event, we return an empty list.
    if end_date < events[0].date_created:
        return []
    # Now we compute the number of days between each event, up to the end date.
    for i in range(len(events) - 1):
        next_event_date = events[i + 1].date_created
        current_event_date = events[i].date_created
        if current_event_date < end_date < next_event_date:
            days_between_events.append((end_date - current_event_date).days)
            break
        days_between_events.append((next_event_date - current_event_date).days)
    # We check if the final event is before the end date, and if so, we add the number of days between the final event
    # and the end date.
    last_event_date = events[-1].date_created
    if last_event_date < end_date:
        days_between_events.append((end_date - last_event_date).days)

    return days_between_events


def add_event_duration_to_events(
    events: list[Event], events_duration: list[int]
) -> list[EventWithDuration]:
    """Return a list of events with a duration.

    Args:
        events (list[Event]): List of events.
        events_duration (list[int]): List of events duration (full-days).

    Returns:
        list[EventWithDuration]: List of events with a duration.

    Raises:
        ValueError: If events and events_duration have different lengths.
    """
    if len(events_duration) > len(events):
        raise ValueError(
            f"Cannot have more events_duration ({len(events_duration)}) than events ({len(events)})."
            f"{len(events_duration)} events_duration."
        )
    return [
        EventWithDuration(**asdict(events[ix]) | {"number_of_days": number_of_days})
        for ix, number_of_days in enumerate(events_duration)
    ]


def compute_interest_between_dates(
    advancements_balance: float, interest_rate: float, number_of_days: int
) -> float:
    """Return a tuple of interest accrued, current balance and total sum of unpaid interest."""
    if advancements_balance <= 0:
        return 0
    return advancements_balance * interest_rate * number_of_days


def compute_interest(
    events_with_duration: list[EventWithDuration],
    loan_daily_interest_rate: Optional[float] = 0.00035,
) -> list[LedgerState]:
    """Return a list of interest for all events

    Args:
        events_with_duration (list[EventWithDuration]): List of events with duration.
        loan_daily_interest_rate (float): Daily interest rate for the loan. Defaults to 0.00035.

    Returns:
        list[LedgerState]: List of ledger state after each event.
    """
    interest_between_dates = []
    current_advancements_balance = 0
    total_sum_of_unpaid_interest = 0
    total_days_in_interest_period = 0
    event_completion_date = None
    for event in events_with_duration:
        event_amount = event.amount
        event_type = event.event_type
        if current_advancements_balance > 0:
            # If we have a balance bigger than 0, we compute the interest for the current event.
            accrued_interest = compute_interest_between_dates(
                current_advancements_balance,
                loan_daily_interest_rate,
                total_days_in_interest_period,
            )
            # We now update the current total sum of unpaid interest.
            total_sum_of_unpaid_interest += accrued_interest
            # We append the current balance, the interest accrued in the period, and the total sum of unpaid interest
            # to the list.
            interest_between_dates.append(
                LedgerState(
                    current_balance=current_advancements_balance,
                    interest_accrued=accrued_interest,
                    total_sum_of_unpaid_intrest=total_sum_of_unpaid_interest,
                    evaluation_date=event_completion_date,
                    total_number_of_days=total_days_in_interest_period,
                )
            )
        # We check the type of event and update the current balance accordingly.
        if event_type == "advance":
            current_advancements_balance += event_amount
        elif event_type == "payment":
            # For payments, we check if the total sum of unpaid interest is bigger than the payment amount. The priority
            # is to pay the interest, and if there is any remaining amount, we pay the principal.
            if event_amount > total_sum_of_unpaid_interest:
                total_sum_of_unpaid_interest = 0
                current_advancements_balance -= (
                    event_amount - total_sum_of_unpaid_interest
                )
            else:
                total_sum_of_unpaid_interest -= event_amount
        # We update the total number of days in the interest period.
        total_days_in_interest_period = event.number_of_days
        event_completion_date = event.date_created
    # We run the computation one last time to get the interest for the last event.
    accrued_interest = compute_interest_between_dates(
        current_advancements_balance,
        loan_daily_interest_rate,
        total_days_in_interest_period,
    )
    total_sum_of_unpaid_interest += accrued_interest
    interest_between_dates.append(
        LedgerState(
            current_balance=current_advancements_balance,
            interest_accrued=accrued_interest,
            total_sum_of_unpaid_intrest=total_sum_of_unpaid_interest,
            evaluation_date=event_completion_date,
            total_number_of_days=total_days_in_interest_period,
        )
    )
    return interest_between_dates
