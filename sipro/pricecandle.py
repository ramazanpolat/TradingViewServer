from typing import Any

from prodict import Prodict


class PriceCandle(Prodict):
    exchange: str
    base: str
    quote: str
    interval: int  # as seconds
    datetime: Any
    ts: int  # timestamp
    avg_price: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    base_volume: float
    buys: int
    sells: int
    buy_volume: float
    buy_base_volume: float
    sell_volume: float
    sell_base_volume: float
    min_spread: float
    max_spread: float
    avg_spread: float

    def display(self):
        return f"{self.datetime}({self.interval}s) =" \
               f"\tO:{self.open:.2f}\tH:{self.high:.2f}\tL:{self.low:.2f}\tC:{self.close:.2f}\tV:{self.volume}"

    def display2(self):
        s1 = f"{self.base}-{self.quote} {self.datetime}(m{self.interval//60}) "
        s2 = f"O={self.open:.2f}\tH={self.high:.2f}\tL={self.low:.2f}\tC={self.close:.2f}"
        return s1 + s2

    def display3(self):
        s1 = f"{self.base}-{self.quote} {self.datetime}-{self.ts}(m{self.interval//60}) "
        s2 = f"O={self.open:.2f}\tH={self.high:.2f}\tL={self.low:.2f}\tC={self.close:.2f}"
        return s1 + s2

    def __repr__(self) -> str:
        string = ""
        for attr in self.attr_names():
            string += f"{attr}: {self.get(attr)}\n"
        return string
