import datetime


class Dates:
    """Cálculos con fechas compartidos por las clases y las ventanas."""

    @staticmethod
    def full_years(start: datetime.date, end: datetime.date) -> int:
        """Años completos entre dos fechas (edad o antigüedad)."""
        years = end.year - start.year
        if (end.month, end.day) < (start.month, start.day):
            years -= 1
        return years
