class Formatter:
    """Formatos de texto compartidos por las ventanas."""

    @staticmethod
    def money(amount: float) -> str:
        return f'$ {amount:,.2f}'

    @staticmethod
    def percent(rate: float) -> str:
        # :g quita los ceros de sobra (0.2 % en lugar de 0.200000 %)
        return f'{rate * 100:g} %'
