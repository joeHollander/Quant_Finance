import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import csv
import ast
import os

def txt_to_csv(input_file, output_file=None, delete_input=False):
    if output_file is None:
        output_file = input_file.replace(".txt", ".csv")
    if not os.path.exists(input_file):
        print("file doesn't exist")
        return 

    data = []
    with open(r'Data\kraken_files\btc.txt', 'r') as txt_file:
        for line in txt_file:
            data.append(ast.literal_eval(line.strip()))

    headers = data[0].keys()

    with open(output_file, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()

        for row in data:
            writer.writerow(row)

    if delete_input:
        os.remove(input_file)


if __name__ == "__main__":
    fname = "kraken_ETH_USDT_20241001"
    output_file = "Data/kraken_files/" + fname + ".csv"

    df = pd.read_csv(output_file)
    print(df.loc[:5, "curr_delta"])