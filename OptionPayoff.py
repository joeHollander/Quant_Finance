import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

class Option: 
    def __init__(self, option_type, action, strike, interest_rate=0.01, time_to_expiration=0.5, volatility=0.11): 
        self.option_type = option_type
        self.action = action
        self.strike = strike
        self.r = interest_rate
        self.t = time_to_expiration
        self.o = volatility 

    def bsm(self):
        option_type = self.option_type
        s = 100
        k = self.strike
        r = self.r
        t = self.t
        o = self.o
        # finding d1 and d2
        d1 = (np.log(s/k) + t * (r + (o**2)/2)) / (o * np.sqrt(t))
        d2 = d1 - o * np.sqrt(t)
        # option prices
        C = s * norm.cdf(d1, 0, 1) - (k * np.exp(-r * t)) * norm.cdf(d2, 0, 1)
        P = k * np.exp(-r * t) * norm.cdf(-d2, 0, 1) - s * norm.cdf(-d1, 0, 1 )
        # call or put
        if self.option_type == "call":
            return C
        elif self.option_type == "put":
            return P

    def payoff(self, spot):
        option_type = self.option_type
        action = self.action

        # determining value of option less the premium 
        if option_type == "call":
            value = max(0, spot - self.strike) - self.bsm()
        elif option_type == "put":
            value = max(0, self.strike - spot) - self.bsm()
    
        # value depending on action
        if action == "buy":
            return value 
        elif action == "sell":
            return -1 * value 
        
class Stock:
    def __init__(self, action, num_of_shares):
        self.action = action
        self.shares = num_of_shares

    def payoff(self, spot):
        if self.action == "buy":
            value = self.shares * (spot - 100)
        elif self.action == "sell":
            value = self.shares * (100 - spot)

        return value

class OptionPortfolio: 
    def __init__(self):
        self.options = []

    def add_option(self, *options):
        self.options.extend([*options])
        # print(self.options)

    def add_stock(self, *stocks):
        self.options.extend([*stocks])

    def total_payoff(self, spot):
        option_payoff = 0
        for i in range(len(self.options)):
            option_payoff += round(self.options[i].payoff(spot), 3)
        return option_payoff
    
    def graph(self, start, stop):
        payoff = [self.total_payoff(i) for i in range(start, stop+5, 5)] 
        # print(payoff)

        fig, ax, = plt.subplots()
        ax.plot([i for i in range(start, stop+5, 5)], payoff)
        plt.axhline(0, color="black")
        plt.show()


if __name__ == "__main__":
    put = Option("put", "buy", 90)
    port = OptionPortfolio()
    port.add_option(put)
    port.graph(70,130)



    
    
