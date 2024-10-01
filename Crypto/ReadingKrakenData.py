import pandas as pd
import numpy as np
import csv

fname = "kraken_ETH_USD_20240930"
with open('Data/kraken_files/' + fname + ".txt", 'r') as txt_file, open('Data/kraken_files/' + fname + ".csv", 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    for line in txt_file:
        # Assuming the delimiter in your TXT file is a comma
        row = line.strip().split('\n') 
        writer.writerow(row)
        

df = pd.read_csv("output.csv")
print(df.head())