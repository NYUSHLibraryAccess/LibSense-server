import os
import sys
import pandas as pd
from datetime import date
from Data import clean_data


if __name__ == "__main__":
    if sys.argv[1] in ["-h", "--help"]:
        print("""
        USAGE: python Data.py [INPUT_FILE_PATH]
        OUTPUT: CLEANED CSV FILE TO CURRENT PATH
        """)
    file_path = sys.argv[1]
    if not file_path.split(".")[-1] in ["xlsx", "xls"]:
        raise Exception("Please check file path. Only absolute path with .xls, .xlsx accepted")
    print("Reading excel file")
    origin_df = pd.read_excel(file_path, dtype=str)
    print("Start data cleaning")
    clean_df = clean_data(origin_df)
    not_nyush = clean_df[~(clean_df["Z68_ORDER_NUMBER"].str.contains("NYUSH"))]
    clean_df = clean_df[clean_df["Z68_ORDER_NUMBER"].str.contains("NYUSH")]
    clean_df["Z68_ORDER_NUMBER"] = clean_df["Z68_ORDER_NUMBER"].apply(lambda x: x[5:])
    current_year = int(date.today().isoformat()[0:4])
    year_dict = {i: None for i in range(current_year - 3, current_year + 1)}

    for year in year_dict.keys():
        this_year = clean_df["Z68_ORDER_NUMBER"].apply(lambda x: x[0:4] == str(year))
        this_year.name = "this_year"
        this_df = clean_df.join(this_year)
        this_df = this_df[this_df["this_year"] == True]
        this_df["Z68_ORDER_NUMBER"] = this_df["Z68_ORDER_NUMBER"].apply(lambda x: x[4:])
        this_df["Z68_ORDER_NUMBER"] = this_df["Z68_ORDER_NUMBER"].astype(int)
        this_df = this_df.sort_values(by=["Z68_ORDER_NUMBER"])
        this_df["Z68_ORDER_NUMBER"] = this_df["Z68_ORDER_NUMBER"].astype(str)
        this_df["Z68_ORDER_NUMBER"] = this_df["Z68_ORDER_NUMBER"].apply(lambda x: "NYUSH" + str(year) + x)
        del this_df["this_year"]
        year_dict[year] = this_df

    sorted_clean = pd.concat([year_df for year_df in year_dict.values()])
    sorted_clean = pd.concat([not_nyush, sorted_clean])
    sorted_clean.reset_index(inplace=True, drop=True)
    print(sorted_clean.shape)
    sorted_clean.to_csv("CLEANED_DATA.csv", index=False)
    print("Operation complete. Output file at: %s" % (os.getcwd() + "/CLEANED_DATA.csv"))