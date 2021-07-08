# encoding: utf-8
# copyright: GeoDS Lab, University of Wisconsin-Madison
# authors: Yuhao Kang, Song Gao, Jinmeng Rao
import os
import pandas as pd
import argparse

# Assign input folder path and output file path
parser = argparse.ArgumentParser(description='Merge files in one folder')
parser.add_argument('-i', '--input_folder', type=str, help='Input folder path')
parser.add_argument('-o', '--output_file_path', type=str, help='Output file path')

args = parser.parse_args()

input_folder = args.input_folder
output_path = args.output_file_path

# Merge all files
flow_all = []
for file in os.listdir(input_folder):
    if file[-3:] == "csv":
        flow_df = pd.read_csv(f'{input_folder}/{file}')
        flow_all.append(flow_df)
result = pd.concat([x for x in flow_all])
result.to_csv(output_path, index=False)