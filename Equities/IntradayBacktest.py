from IntradayModel import BoundsData

def load_bounds_data(instrument_id: str, upper_bound_col, lower_bound_col):
    return [BoundsData(instrument_id, ub, lb) for ub, lb in zip(upper_bound_col, lower_bound_col)]

if __name__ == "__main__":
    print(load_bounds_data("MSFT", ))