from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG
import pandas as pd

import julia
jl = julia.Julia()
# jl = julia.Julia(compiled_modules=False)
from julia import Main
Main.include('jl_experiment.jl')


class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        close = self.data.Close
        # self.sma1 = self.I(SMA, close, self.n1)
        # self.sma2 = self.I(SMA, close, self.n2)
        self.pos = "sell"

    def next(self):
        # if self.pos == "idle" and Main.rand_dec() == "sell":
        #     self.pos = "sell"
        #     self.sell()

        if self.pos == "sell" and Main.rand_dec() == "buy":
            self.pos = "buy"
            self.position.close()
            self.buy()
        elif self.pos == "buy" and Main.rand_dec() == "sell":
            self.pos = "sell"
            self.position.close()
            self.sell()

        # if crossover(self.sma1, self.sma2):
        #     self.buy()
        # elif crossover(self.sma2, self.sma1):
        #     self.sell()


if __name__ == "__main__":
    pass
    df = pd.read_csv("./../../Data/ETHUSDT-1m-2021-06.csv", names=["Open time", "Open", "High", "Low", "Close", "Volume"], usecols=[0, 1, 2, 3, 4, 5])
    df["Open time"] = pd.to_datetime(df["Open time"], unit='ms')
    df = df.set_index(["Open time"])
    # df = df.head(10000)
    close_prices = df["Close"].to_numpy()
    close_prices /= close_prices[0]
    _, _, ar_data, _ = Main.inference(close_prices, 2, 30)
    # bt = Backtest(df,
    #               SmaCross,
    #               cash=10000,
    #               commission=.002,
    #               exclusive_orders=True)
    #
    # output = bt.run()
    # bt.plot()
    # print(ar_data)
