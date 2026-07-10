from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum


class RecurrenceFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True, slots=True)
class RecurrenceRule:
    frequency: RecurrenceFrequency
    interval: int = 1

    def next_date(self, current: date) -> date:
        match self.frequency:
            case RecurrenceFrequency.DAILY:
                return current + timedelta(days=self.interval)

            case RecurrenceFrequency.WEEKLY:
                return current + timedelta(weeks=self.interval)

            case RecurrenceFrequency.MONTHLY:
                month = current.month - 1 + self.interval
                year = current.year + month // 12
                month = month % 12 + 1

                day = min(current.day, _days_in_month(year, month))

                return date(year, month, day)

            case RecurrenceFrequency.YEARLY:
                try:
                    return current.replace(year=current.year + self.interval)
                except ValueError:
                    return current.replace(
                        year=current.year + self.interval,
                        day=28,
                    )


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31

    return (date(year, month + 1, 1) - timedelta(days=1)).day
