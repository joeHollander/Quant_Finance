from ib_insync import *
# util.startLoop()  # uncomment this line when in a notebook

class HistoricalData:
    def __init__(self, port=4002, clientId=999):
        self.ib = IB()
        self.ib.connect("127.0.0.1", port, clientId)

    def get_data(self, contract, endDateTime, durationStr, barSize, whatToShow, useRTH: bool):
        self.contract = contract
        
        if self.verify_contract(contract):
            bars = self.ib.reqHistoricalData(
                contract, endDateTime, durationStr,
                barSize, whatToShow, useRTH)
            
            return util.df(bars)
            self.ib.disconnect()
            
        else:
            print("Error: incorrect contract")

    def verify_contract(self, contract):
        qc = self.ib.qualifyContracts(contract)
        if not qc:
            return False
        else:
            return qc[0] == contract
        
if __name__ == "__main__":
    hd = HistoricalData(clientId=2)
    df = hd.get_data(Stock("MCD", "NYSE", "USD"), "", "1 Y", "2 hours", "MIDPOINT", True)
    print(df)

    
