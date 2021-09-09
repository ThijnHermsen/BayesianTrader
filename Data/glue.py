import sys

import pandas as pd
from pathlib import Path
import ntpath
import zipfile
import glob
import os
from datetime import datetime


def unpack_zips(l_path, d_path):
    zip_files = glob.glob(l_path+r"\\*.zip")

    for zip_file in zip_files:
        with zipfile.ZipFile(zip_file) as zf:
            contain_list = zf.namelist()
            for name in contain_list:
                file_date = name[len(currency_data)+len(int_data)+2:-4]
                if len(file_date) == 7 and start_date <= datetime.strptime(file_date, '%Y-%m') <= end_date or \
                    len(file_date) == 10 and start_date <= datetime.strptime(file_date, '%Y-%m-%d') <= end_date:
                    with open(f"{d_path}/{name[:-4].replace('raw', 'processed')}.csv", "wb") as dumpfile:
                        dumpfile.write(zf.read(name))
                        dumpfile.close()

    return


def concatenate(path):
    csv_files = glob.glob(path + r"\\*.csv")

    for f in csv_files:
        if len(ntpath.basename(f)) == 25 and os.path.exists(f"{f[:-7]}.csv"):
            os.remove(f)

    con_csv_files = glob.glob(path + r"\\*.csv")
    # combine all files in the list
    csv_list = []
    for f in con_csv_files:
        df = pd.read_csv(f, names=["Open time", "Open", "High", "Low", "Close", "Volume"], usecols=[0, 1, 2, 3, 4, 5])
        # df = df.set_index(["Open time"])
        csv_list.append(df)

    combined_csv = pd.concat(csv_list)
    # export to csv
    combined_csv = combined_csv.sort_values(by=['Open time'])
    combined_csv.to_csv(f"{Path(path).parent.absolute()}//{datetime.strftime(start_date, '%Y-%m-%d')}_{datetime.strftime(end_date, '%Y-%m-%d')}.csv", index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    root_folder = os.path.dirname(os.path.abspath(__file__))
    spot_futures = 'spot'
    type_data = 'klines'
    currency_data = 'ETHUSDT'
    int_data = '15m'
    start_date = datetime(year=2021, month=1, day=1)
    end_date = datetime(year=2021, month=8, day=31)

    # unpack zips if necessary
    for period_data in ['monthly', 'daily']:
        load_path = None
        for subdirs, dirs, _ in os.walk(os.path.join(root_folder, "raw", "data", spot_futures, period_data, type_data, currency_data, int_data)):
            for dir in dirs:
                start_date_raw, end_date_raw = dir.split('_')
                if start_date >= datetime.strptime(start_date_raw, '%Y-%m-%d') and end_date <= datetime.strptime(end_date_raw, '%Y-%m-%d'):
                    load_path = os.path.join(root_folder, "raw", "data", spot_futures, period_data, type_data, currency_data, int_data, f"{start_date_raw}_{end_date_raw}")
                    break
        if load_path is None: sys.exit("Raw data does not match requested time period.")

        dump_path = os.path.join(root_folder, "processed", "data", spot_futures, type_data, currency_data, int_data, f"{datetime.strftime(start_date, '%Y-%m-%d')}_{datetime.strftime(end_date, '%Y-%m-%d')}")
        if not os.path.exists(dump_path): os.makedirs(dump_path)

        unpack_zips(load_path, dump_path)

    # merge csv files
    concatenate(dump_path)


