import sys

import numpy as np
from backtesting import Backtest, Strategy
from backtesting.test import SMA, GOOG
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from time import perf_counter

import julia

jl = julia.Julia()
# jl = julia.Julia(compiled_modules=False)
from julia import Main

Main.include('./models/AR/ar.jl')


class SmaCross(Strategy):
    n1 = 10
    n2 = 30
    AR_order = 3
    threshold = 0.02

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(SMA, close, self.n1)
        self.sma2 = self.I(SMA, close, self.n2)
        self.pos = "sell"

        self.ar_order = int(round(self.AR_order))
        self.mx_min = np.zeros(self.ar_order)
        self.vx_min = np.eye(self.ar_order)
        self.mtheta = np.zeros(self.ar_order)
        self.vtheta = np.eye(self.ar_order)
        self.gamma_a = 0.01
        self.gamma_b = 0.01
        self.prec_obs = 1000.0

    def next(self):

        # if crossover(self.sma1, self.sma2):
        #     self.buy()
        # elif crossover(self.sma2, self.sma1):
        #     self.sell()
        #
        mx_mins.append(self.mx_min)
        mthetas.append(self.mtheta)
        gamma_as.append(self.gamma_a / self.gamma_b)

        self.mx_min, self.vx_min, self.mtheta, self.vtheta, self.gamma_a, self.gamma_b = Main.inference(self.data.Close[-1],
                                                                                                        self.mx_min,
                                                                                                        self.vx_min,
                                                                                                        self.mtheta,
                                                                                                        self.vtheta,
                                                                                                        self.gamma_a,
                                                                                                        self.gamma_b,
                                                                                                        self.prec_obs,
                                                                                                        self.ar_order,
                                                                                                        20)

        # print(self.AR_order, self.threshold)
        if self.mtheta[-1] != 0.0:

            if self.pos != "buy" and self.mx_min @ self.mtheta / self.data.Close[-1] > self.threshold:
                self.pos = "buy"
                self.buy()
            elif self.pos != "sell" and self.mx_min @ self.mtheta / self.data.Close[-1] < 1/self.threshold:
                self.pos = "sell"
                self.sell()


def plot_priors(mx_mins, mthetas, gamma_as):
    mx_mins = np.array(mx_mins)
    mthetas = np.array(mthetas)
    gamma_as = np.array(gamma_as)

    # assert len(mx_mins.T) == 1, "Variables mx_min, mthetha, and gamma are not saved at next(). The buffer length is 0"

    # mx_mins
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 5))
    ax1.plot(np.arange(len(mx_mins[:, 0])), mx_mins[:, 0])
    ax2.plot(np.arange(len(mx_mins[:, 1])), mx_mins[:, 1])
    if len(mx_mins[0, :]) > 2: ax3.plot(np.arange(len(mx_mins[:, 2])), mx_mins[:, 2])
    if len(mx_mins[0, :]) > 3: ax4.plot(np.arange(len(mx_mins[:, 3])), mx_mins[:, 3])
    ax1.set_title('mx_min0')
    ax2.set_title('mx_min1')
    ax3.set_title('mx_min2')
    ax4.set_title('mx_min3')

    plt.savefig(f"./out/plots/mx_min/ord{AR_order_set}_thrs{threshold_set}.jpg")

    # mthetas
    fig1, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 5))
    ax1.plot(np.arange(len(mthetas[:, 0])), mthetas[:, 0])
    ax2.plot(np.arange(len(mthetas[:, 1])), mthetas[:, 1])
    if len(mx_mins[0, :]) > 2: ax3.plot(np.arange(len(mthetas[:, 2])), mthetas[:, 2])
    if len(mx_mins[0, :]) > 3: ax4.plot(np.arange(len(mthetas[:, 3])), mthetas[:, 3])
    ax1.set_title('mtheta0')
    ax2.set_title('mtheta1')
    ax3.set_title('mtheta2')
    ax4.set_title('mtheta3')

    plt.savefig(f"./out/plots/m_theta/ord{AR_order_set}_thrs{threshold_set}.jpg")

    # mx_mins
    fig2, ax1 = plt.subplots(1, 1, figsize=(15, 5))
    ax1.plot(np.arange(len(gamma_as)), 1/gamma_as)
    ax1.set_title('1/gamma')

    plt.savefig(f"./out/plots/gamma/ord{AR_order_set}_thrs{threshold_set}.jpg")
    # plt.show()


def plot_psd(sig_sq, phi, f=np.linspace(0, 0.5, 100)):
    summed = 1
    title_str = f"PSD params:"
    for k, p in enumerate(phi):
        temp = p * np.exp(1j * 2*np.pi * f * (k+1))
        summed -= temp
        title_str += f" , {round(p, 3)}"

    psd = sig_sq / abs(summed) ** 2

    # psd = sig_sq / (1 + phi[0]**2 + phi[1]**2 - 2*phi[0]*(1 - phi[1])*np.cos(2*np.pi*f) - 2*phi[1]*np.cos(4*np.pi*f))

    fig, ax = plt.subplots()
    ax.plot(f, psd)
    ax.set_yscale('log')
    # ax.set_ylim([min(0.9*np.min(psd), 1.1*np.min(psd)), np.min(psd) + 30])
    ax.set_title(title_str)
    # plt.show()
    plt.savefig(f"./out/plots/PSD_ord{AR_order_set}_thrs{threshold_set}.jpg")


if __name__ == "__main__":
    df = pd.read_csv(r"./../../Data\processed\data\spot\klines\ETHUSDT\15m\2021-01-01_2021-08-31.csv", usecols=[0, 1, 2, 3, 4, 5])  # names=["Open time", "Open", "High", "Low", "Close", "Volume"],
    # df = pd.read_csv(r"./../../Data\processed\data\spot\klines\ETHUSDT\1m\2021-01-01_2021-09-01.csv", usecols=[0, 1, 2, 3, 4, 5])  # names=["Open time", "Open", "High", "Low", "Close", "Volume"],

    df["Open time"] = pd.to_datetime(df["Open time"], unit='ms')
    df = df.set_index(["Open time"])
    # df = df.head(100)
    # close_prices = df["Close"].to_numpy()
    # close_prices /= close_prices[0]

    for AR_order_set in [2, 3, 4]:
        for threshold_set in [1.005]:
            mx_mins = []
            mthetas = []
            gamma_as = []

            perf_timer = perf_counter()
            bt = Backtest(df,
                          SmaCross,
                          cash=10000,
                          commission=.002,
                          exclusive_orders=True)

            # output = bt.optimize(AR_order=[4, 50],
            #                      threshold=[0.01, 0.1],
            #                      method='skopt',
            #                      maximize='SQN')
            output = bt.run(AR_order=AR_order_set, threshold=threshold_set)

            plot_priors(mx_mins, mthetas, gamma_as)
            plot_psd(sig_sq=1/gamma_as[-1], phi=np.array(mthetas)[-1, :])

            # print(output)
            # bt.plot(filename=f"./out/AR_result_{datetime.now().strftime('%m-%d-%H-%M-%S')}.html")
            bt.plot(filename=f"./out/AR_result_ord{AR_order_set}_thrs{threshold_set}.html", open_browser=False)
            # # print(ar_data)
            # try: pd.to_pickle(output, './output.pkl')
            # except: pass

            print(f"Run took {perf_counter() - perf_timer} seconds for ord{AR_order_set}_thrs{threshold_set}.")