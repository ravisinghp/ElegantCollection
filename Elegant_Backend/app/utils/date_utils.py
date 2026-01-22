from datetime import datetime, timedelta

def working_days_between(start_date: datetime, end_date: datetime, holidays: list) -> int:
    day_count = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5 and current.date() not in holidays:
            day_count += 1
        current += timedelta(days=1)

    return day_count
