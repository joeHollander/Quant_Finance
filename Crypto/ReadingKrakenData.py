import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import csv
import ast
import os

def txt_to_csv(input_file, output_file, delete_input=False):
    if not os.path.exists(input_file):
        print("file doesn't exist")
        return 

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        csv_writer = csv.writer(outfile)
        
        # Write header
        first_line = infile.readline().strip()
        header = list(ast.literal_eval(first_line).keys())
        csv_writer.writerow(header)
        
        # Write data
        infile.seek(0)  # Reset file pointer to beginning
        for line in infile:
            data = ast.literal_eval(line.strip())
            csv_writer.writerow(data.values())

    if delete_input:
        os.remove(input_file)


if __name__ == "__main__":
    fname = "kraken_ETH_USDT_20241001"
    output_file = "Data/kraken_files/" + fname + ".csv"

    df = pd.read_csv(output_file)
    print(df.loc[:5, "curr_delta"])