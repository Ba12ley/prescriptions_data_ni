import os

import numpy as np
import pandas as pd
import requests
import chardet
import os
from bs4 import BeautifulSoup
from pathlib import Path

from jedi.settings import case_insensitive_completion
from pandas.core.interchange.dataframe_protocol import DataFrame


def get_data(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup


def download_data(url, file_type, directory):
    directory_path = Path(directory)
    try:
        directory_path.mkdir()
        print(f'Directory {directory_path} created')
    except FileExistsError:
        print(f'Directory {directory_path} already exists')
    except PermissionError:
        print('Permission Denied')
    except Exception as e:
        print(f'Error {e}')

    file_type_upper = file_type.upper()
    for file in get_data(url).find_all('a', class_='py-1 px-6 ml-2 bg-blue-c-600 rounded-lg'):
        file_link = file.get('href')
        file_name = file.get('href').split('/')[-1]
        if file_type in file_link or file_type_upper in file_link:
            print(f'{file["href"]}')
            print(file_name.lower())

            with open(f'./data/{directory}/{file.get("href").split("/")[-1]}'.lower(), 'wb') as f:
                f.write(requests.get(f'{file["href"]}').content)


def csv_encoding_type(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    encoding_result = chardet.detect(data)
    encoding = encoding_result['encoding']
    print(f"{encoding}")


def file_renaming(path):
    extension = '.csv'
    files = [file for file in os.listdir(path) if file.endswith(extension)]
    for file in files:
        file_month = file.split('---')[1].split('-')
        file_year = file_month[1].split('.')[0]
        new_filename = f'{file_year}{file_month[0]}.csv'
        print(f'{file} to {new_filename}')
        os.rename(f'{path}/{file}', f'{path}/{new_filename}')

def header_correction(path):
    files_in_dir = [file for file in os.listdir(path) if file.endswith('.csv')]
    for file in files_in_dir:
        df = pd.read_csv(os.path.join(path,file),encoding='Windows-1252')
        df = df.rename(columns={df.columns[0]: 'Practice'})
        df['Gross Cost (£)'] = df.apply(lambda r: r['Gross Cost (£)'] if isinstance(r['Gross Cost (£)'], float) else np.nan, axis=1)
        df['Total Quantity'] = df.apply(
            lambda r: r['Total Quantity'] if isinstance(r['Total Quantity'], int) else np.nan, axis=1)
        df = df.fillna(0.0)
        df.to_csv(f'{os.path.join(path,file)}_header_correction.csv')
        print(f'{os.path.join(path,file)}_header_correction.csv created')
        os.remove(os.path.join(path,file))
        print(f'{file} deleting')


def read_data(path):
    dataframes = []
    practice_details = pd.read_csv('./data/practice_name/2024october.csv', encoding='Windows-1252',
                                   dtype_backend='pyarrow',
                                   usecols=['PracNo', 'PracticeName', 'LCG', 'Registered_Patients'])
    files_in_dir = [file for file in os.listdir(path) if file.endswith('.csv')]

    for file in files_in_dir:
        df = pd.read_csv(os.path.join(path, file), dtype_backend='pyarrow', encoding='utf-8',
                         engine='pyarrow',
                         usecols=["Practice", "Year", "Month", "VMP_NM", "AMP_NM", "Strength", "Total Quantity",
                                  "Gross Cost (£)", "Actual Cost (£)", "BNF Chapter"]).merge(
            practice_details, left_on='Practice',
            right_on='PracNo')
        dataframes.append(df)

    all_dataframes = pd.concat(dataframes, ignore_index=True)
    # all_dataframes['Gross Cost (£)'] = all_dataframes.apply(lambda r: r['Gross Cost (£)'] if isinstance(r['Gross Cost (£)'], float) else np.nan, axis=1).fillna(0.0)

    # annual_sum = all_dataframes.groupby(["Practice"])["Gross Cost (£)"].sum().reset_index()
    # vmp_nm_spend = all_dataframes.groupby(["VMP_NM"])["Gross Cost (£)"].sum().round(2).reset_index()
    return all_dataframes


def annual_sum(dataframe) -> DataFrame:
    annual_sum_total = dataframe.groupby(["LCG", 'Year'])["Gross Cost (£)"].sum().round(2).reset_index()
    return annual_sum_total


def annual_count(dataframe) -> DataFrame:
    annual_count_total = dataframe.groupby(["VMP_NM", 'Year'])['Total Quantity'].sum().reset_index()
    return annual_count_total


def annual_sum_by_prescription(dataframe) -> DataFrame:
    annual_sum_by_prescription = dataframe.groupby(['VMP_NM', 'Year'])['Gross Cost (£)'].sum().round(2).reset_index()
    return annual_sum_by_prescription


def annual_top_10(dataframe) -> DataFrame:
    top_10 = dataframe.groupby(['Year', 'VMP_NM'])['VMP_NM'].count().reset_index(name='Count')
    return top_10


def prescription_by_lcg(dataframe) -> DataFrame:
    prescription_by_lcg_data = dataframe.groupby(['VMP_NM', 'LCG', 'Year'])['VMP_NM'].count().reset_index(name='Count')
    return prescription_by_lcg_data


def annual_spend_by_year(dataframe) -> DataFrame:
    annual_spend_by_year = dataframe.groupby('Year')['Gross Cost (£)'].sum().round(2).reset_index()
    return annual_spend_by_year


def conditions_by_bnf_chapter(dataframe) -> DataFrame:
    bnf_chapters = {'BNF_Chapter_Number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
                    'BNF_Chapter_Name': [
                        "Gastro-intestinal system",
                        "Cardiovascular system",
                        "Respiratory system",
                        "Central nervous system",
                        "Infections",
                        "Endocrine system",
                        "Obstetrics, gynaecology, and urinary-tract disorders",
                        "Malignant disease and immunosuppression",
                        "Nutrition and blood",
                        "Musculoskeletal and joint diseases",
                        "Eye",
                        "Ear, nose, and oropharynx",
                        "Skin",
                        "Immunological products and vaccines",
                        "Anaesthesia",
                        "Emergency treatment of poisoning",
                        "Other drugs and preparations",
                        "Dressings, appliances, and reagents",
                        "Other medical devices"]
                    }
    bnf_names = pd.DataFrame.from_dict(bnf_chapters)
    conditions_by_bnf_chapter_data = dataframe.groupby(['LCG', 'Year', 'BNF Chapter'])[
        'BNF Chapter'].count().reset_index(name='Count')
    conditions_by_bnf_chapter_data = (
        conditions_by_bnf_chapter_data.replace({'BNF Chapter': {'-': 0}})
        .astype({'BNF Chapter': 'int'})
        .query('0 < `BNF Chapter` < 20')
        .merge(bnf_names, left_on='BNF Chapter', right_on='BNF_Chapter_Number')
    )

    return conditions_by_bnf_chapter_data
