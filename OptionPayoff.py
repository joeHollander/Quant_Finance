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
        C = s * norm.cdf(d1) - (k * np.exp(-r * t)) * norm.cdf(d2)
        return C 

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

class OptionPortfolio: 
    def __init__(self):
        self.options = []

    def add_option(self, *options):
        options_list = [*options]
        self.options.extend(options_list)
        # print(self.options)

    def total_payoff(self, spot):
        option_payoff = 0
        for i in range(len(self.options)):
            option_payoff += round(self.options[i].payoff(spot), 2)
        return option_payoff
    
    def graph(self, start, stop):
        payoff = [self.total_payoff(i) for i in range(start, stop+5, 5)] 
        print(payoff)
        fig, ax, = plt.subplots()
        ax.plot([i for i in range(start, stop+5, 5)], payoff)
        plt.axhline(0, color="black")
        plt.show()


if __name__ == "__main__":
    # call = Option("call", "sell", 120, time_to_expiration=0.1)
    # put = Option("put", "sell", 80, time_to_expiration=0.1)
    # strangle = OptionPortfolio()
    # strangle.add_option(call, put)
    # strangle.graph(50, 150)  



    
    
