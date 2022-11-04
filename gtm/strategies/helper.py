import pandas as pd
from datetime import datetime, date, timedelta

output_dir = "output/"


# = = = = = = = = = = = = = = = = = = = = = = = = = =
#            STRING ARRAY TO INT ARRAY 2D
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def strArrToIntArr_2d(s_arr: list):

    # This function convert 2d str array to 2d int array

    ml = []
    for sl in s_arr:
        l = []

        for si in sl:

            if type(si) is str:

                l.append(float(si) if "." in si else int(si))

            else:
                l.append(si)

        ml.append(l)

    return ml


# = = = = = = = = = = = = = = = = = = = = = = = = = =
#                   WRITE EXCEL
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def writeExcel(df: pd.DataFrame):
    # create excel writer

    writer = pd.ExcelWriter("output/output.xlsx")
    # write dataframe to excel sheet named 'marks'
    df.to_excel(writer, "trade")
    # save the excel file
    writer.save()


# = = = = = = = = = = = = = = = = = = = = = = = = = =
#                     TOMORROW
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def tomorrow():

    # today + 1 day = tomorrow (datetime.date) # extra 5 seconds for computation
    tomorrow = date.today() + timedelta(days=1, seconds=5)

    # convert datetime.date => datetime.datetime
    return datetime.combine(tomorrow, datetime.min.time())
