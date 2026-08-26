from datetime import datetime, timedelta


DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(date: str, time: str) -> datetime:
    """
    Combine a date and time string into a datetime object.

    Example:
        date = "2026-08-30"
        time = "07:30"

    Returns:
        datetime(2026, 8, 30, 7, 30)
    """
    return datetime.strptime(
        f"{date} {time}",
        DATETIME_FORMAT
    )


def add_minutes(start_time: datetime, minutes: int) -> datetime:
    """
    Add a number of minutes to a datetime.
    """
    return start_time + timedelta(minutes=minutes)


def minutes_between(
    start_time: datetime,
    end_time: datetime
) -> int:
    """
    Calculate the difference between two datetime objects in minutes.
    """
    return int((end_time - start_time).total_seconds() / 60)


def calculate_buffer(
    expected_arrival: datetime,
    deadline: datetime
) -> int:
    """
    Calculate the available time buffer before a deadline.

    Positive value:
        Arrival is before the deadline.

    Negative value:
        Arrival is after the deadline.
    """
    return minutes_between(expected_arrival, deadline)