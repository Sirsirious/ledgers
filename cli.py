#!/usr/bin/env python3
import click
import csv
from datetime import datetime
from decimal import Decimal
import os
import sqlite3
from typing import Dict

from dateutil import parser

from tools.ledger import (
    compute_ledger,
    format_remaining_balances,
)


@click.group()
@click.option(
    "--debug/--no-debug", default=False, help="Debug output, or no debug output."
)
@click.pass_context
def interface(ctx: Dict, debug: bool) -> None:
    """Ampla engineering takehome ledger calculator."""
    ctx.ensure_object(dict)
    ctx.obj[
        "DEBUG"
    ] = debug  # you can use ctx.obj['DEBUG'] in other commands to log or print if DEBUG is on
    ctx.obj["DB_PATH"] = os.path.join(os.getcwd(), "db.sqlite3")
    if debug:
        click.echo(f"[Debug mode is on]")


@interface.command()
@click.pass_context
def create_db(ctx: Dict) -> None:
    """Initialize sqlite3 database."""
    if os.path.exists(ctx.obj["DB_PATH"]):
        click.echo("Database already exists")
        return

    with sqlite3.connect(ctx.obj["DB_PATH"]) as connection:
        if not connection:
            click.echo(
                "Error: Unable to create sqlite3 db file. Please ensure sqlite3 is installed on your system and "
                "available in PATH!"
            )
            return

        cursor = connection.cursor()
        cursor.execute(
            """
            create table events
            (
                id integer not null primary key autoincrement,
                type varchar(32) not null,
                amount decimal not null,
                date_created date not null
                CHECK (type IN ("advance", "payment"))
            );
        """
        )
        connection.commit()
    click.echo(f"Initialized database at {ctx.obj['DB_PATH']}")


@interface.command()
@click.pass_context
def drop_db(ctx: Dict) -> None:
    """Delete sqlite3 database."""
    if not os.path.exists(ctx.obj["DB_PATH"]):
        click.echo(f"SQLite database does not exist at {ctx.obj['DB_PATH']}")
    else:
        os.unlink(ctx.obj["DB_PATH"])
        click.echo(f"Deleted SQLite database at {ctx.obj['DB_PATH']}")


@interface.command()
@click.argument("filename", type=click.Path(exists=True, writable=False, readable=True))
@click.pass_context
def load(ctx: Dict, filename: str) -> None:
    """Load events with data from csv file."""
    if not os.path.exists(ctx.obj["DB_PATH"]):
        click.echo(
            f"Database does not exist at {ctx.obj['DB_PATH']}, please create it using `create-db` command"
        )
        return

    loaded = 0
    with open(filename) as infile, sqlite3.connect(ctx.obj["DB_PATH"]) as connection:
        cursor = connection.cursor()
        reader = csv.reader(infile)
        for row in reader:
            cursor.execute(
                f"insert into events (type, amount, date_created) values (?, ?, ?)",
                (row[0], row[2], row[1]),
            )
            loaded += 1
        connection.commit()

    click.echo(f"Loaded {loaded} events from {filename}")


@interface.command()
@click.argument("end_date", required=False, type=click.STRING)
@click.pass_context
def balances(ctx: Dict, end_date: str = None) -> None:
    """Display balance statistics as of `end_date`."""
    # NOTE: You may not change the function signature of `balances`,
    #       however you may implement it any way you want, so long
    #       as you adhere to the format specification.
    #       Here is some code to get you started!
    if end_date is None:
        end_date = datetime.now().date().isoformat()

    overall_advance_balance = Decimal(0)
    overall_interest_payable_balance = Decimal(0)
    overall_interest_paid = Decimal(0)
    overall_payments_for_future = Decimal(0)

    # query events from database example
    with sqlite3.connect(ctx.obj["DB_PATH"]) as connection:
        cursor = connection.cursor()
        result = cursor.execute("select * from events order by date_created asc;")
        events = result.fetchall()
    if not events:
        click.echo("No events found")
        return

    advances = compute_ledger(events, last_date=parser.parse(end_date).date())

    click.echo("Advances:")
    click.echo("----------------------------------------------------------")
    # NOTE: This initial print adheres to the format spec.
    click.echo(
        "{0:>10}{1:>11}{2:>17}{3:>20}".format(
            "Identifier", "Date", "Initial Amt", "Current Balance"
        )
    )
    balances = format_remaining_balances(advances.advances, advances.total_balance)
    for ix, _ in enumerate(balances):
        advance_date = advances.advance_dates[ix].isoformat()
        initial_amt = advances.advances[ix]
        current_balance = balances[ix]
        click.echo(
            "{0:>10}{1:>11}{2:>17.2f}{3:>20.2f}".format(
                ix + 1,  # The advance identifier is 1-based
                advance_date,
                initial_amt,
                current_balance,
            )
        )
    overall_advance_balance = (
        advances.total_balance if advances.total_balance >= Decimal(0) else 0
    )
    overall_interest_payable_balance = advances.total_accrued_interest
    overall_interest_paid = advances.total_interest_paid
    overall_payments_for_future = (
        abs(advances.total_balance) if advances.total_balance <= Decimal(0) else 0
    )

    # TODO: FIXME Print each advance row and relevant advance statistics

    # print summary statistics
    # NOTE: These prints adhere to the format spec.
    click.echo("\nSummary Statistics:")
    click.echo("----------------------------------------------------------")
    click.echo("Aggregate Advance Balance: {0:31.2f}".format(overall_advance_balance))
    click.echo(
        "Interest Payable Balance: {0:32.2f}".format(overall_interest_payable_balance)
    )
    click.echo("Total Interest Paid: {0:37.2f}".format(overall_interest_paid))
    click.echo(
        "Balance Applicable to Future Advances: {0:>19.2f}".format(
            overall_payments_for_future
        )
    )


if __name__ == "__main__":
    interface()
