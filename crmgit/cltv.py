# CLTV = BG/NBD Modeling * Gamma Gamma Submodel

# BG/NBD Modeling
# Gamma Gamma Submodel

# BG/NBD model to calculate expected number of transactions
# It predicts individual purchase values on its own.

# Transaction process (Buy) + Dropout Process (till you die)

# Data Preparation

import datetime as dt
import pandas as pd 
import matplotlib.pyplot as plt
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.plotting import plot_period_transactions

pd.set_option("display.max_columns", None)
pd.set_option("display.width",500)
pd.set_option("display.float_format", lambda x: "%.4f" % x)

from sklearn.preprocessing import MinMaxScaler

# Determines if a value is an outlier
# We don't delete, we replace it.
# You can adjust the percentile according to the data.
def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    # dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


df = pd.read_excel("online2.xlsx")
df = df.drop('Unnamed: 0', axis=1)
print(df.describe().T)
print(df.head())
print(df.isnull().sum())

# Data Preprocessing
df.dropna(inplace=True)
print(df.describe().T)
# When checking here, the value 75 should be 12, but 
# the max value is 80995. So we can understand there are outliers.
# We excluded return transactions
df = df[~df["Invoice"].str.contains("C", na=False)]
print(df.describe().T)

replace_with_thresholds(df, "Quantity")
replace_with_thresholds(df, "Price")
print(df.describe().T)

df["TotalPrice"] = df["Quantity"] * df["Price"]

today_date = dt.datetime(2011, 12, 11)

# Preparing the Lifetime data structure

# Recency = time since last purchase - first purchase (per user)
# T: The age of the customer (how much time has passed since the first purchase)
# Frequency: Frequency (total number of repeated purchases)
# Monetary: Average earning per purchase (not total earning)

cltv_df = df.groupby("Customer ID").agg({"InvoiceDate": [lambda date: (date.max() - date.min()).days,
                                                         lambda date: (today_date - date.min()).days],
                                         "Invoice": lambda num: num.nunique(),
                                         "TotalPrice": lambda TotalPrice: TotalPrice.sum()})

print(cltv_df.head())
cltv_df.columns = cltv_df.columns.droplevel(0)
cltv_df.columns = ["recency", "T", "frequency", "monetary"]
cltv_df["monetary"] = cltv_df["monetary"] / cltv_df["frequency"]
print(cltv_df.describe().T)
print("77777777777777777777777777777777")
cltv_df = cltv_df[(cltv_df["frequency"] > 1)]
# We need weekly data for BG/NBD, so

cltv_df["recency"] = cltv_df["recency"] / 7
cltv_df["T"] = cltv_df["T"] / 7

print(cltv_df.describe().T)

# Model Setup
# BG-NBD
# penalizer_coef = Penalizer coefficient
print("BG NBD MODELING")
bgf = BetaGeoFitter(penalizer_coef=0.001)

a = bgf.fit(cltv_df["frequency"],
            cltv_df["recency"],
            cltv_df["T"])
print(a)
# Who are the top 10 customers with the highest expected number of purchases in a week?
# The parameter "1" represents 1 week.
b = bgf.conditional_expected_number_of_purchases_up_to_time(1,
                                                            cltv_df["frequency"],
                                                            cltv_df["recency"],
                                                            cltv_df["T"]).sort_values(ascending=False).head(10)
print(b)
"""
# The same operation can be done using predict
bgf.predict(1,
            cltv_df["frequency"],
            cltv_df["recency"],
            cltv_df["T"]).sort_values(ascending=False).head(10)

"""
cltv_df["expected_purc_1_week"] = bgf.predict(1,
                                              cltv_df["frequency"],
                                              cltv_df["recency"],
                                              cltv_df["T"])

print("------------------------------------------------------------------------")
print(cltv_df)

# Monthly sales forecast
sales = bgf.predict(4,
                    cltv_df["frequency"],
                    cltv_df["recency"],
                    cltv_df["T"]).sum()

print(f"Monthly sales forecast: {sales} ")

# Accuracy of Forecasting Results

# plot_period_transactions(bgf)
# plt.show()


ggf = GammaGammaFitter(penalizer_coef=0.01)

canke = ggf.fit(cltv_df["frequency"], 
                cltv_df["monetary"])
"""
weekly_ggf = ggf.conditional_expected_average_profit(cltv_df["frequency"],
                                                    cltv_df["monetary"]).head(10)
"""

weekly_ggf = ggf.conditional_expected_average_profit(cltv_df["frequency"],
                                                    cltv_df["monetary"]).sort_values(ascending=False).head(10)

print(weekly_ggf)

cltv_df["expected_average_profit"] = ggf.conditional_expected_average_profit(cltv_df["frequency"],
                                                                             cltv_df["monetary"])

print("Let's take a look at the entire dataset")
print(cltv_df.sort_values("expected_average_profit", ascending=False).head())

# CLTV Calculation

cltv = ggf.customer_lifetime_value(bgf,
                                   cltv_df["frequency"],
                                   cltv_df["recency"],
                                   cltv_df["T"],
                                   cltv_df["monetary"],
                                   time=3, # 3 months
                                   freq="W", # Frequency of T (days, week, month?)
                                   discount_rate=0.01) # Discount rate if needed.

print(cltv.head())
cltv = cltv.reset_index() # Reset indexes to 1, 2, 3, ...
cltv_final = cltv_df.merge(cltv, on="Customer ID", how="left")
print("Final CLTV")
print(cltv_final.sort_values(by="clv", ascending=False).head(10))
# For regular customers, as the recency value increases, the probability of their purchases increases if you haven't lost the customer yet.
# The person on row 3 might be a potential new customer.
# The person on row 5 is an old customer, but the frequency is so high that their potential for making a purchase is also high.

# Segmenting Customers
print("Segmenting Process")
cltv_final["segment"] = pd.qcut(cltv_final["clv"], 4, labels=["D", "C", "B", "A"])
print(cltv_final.sort_values(by="clv", ascending=False).head())

print(cltv_final.groupby("segment").agg({
    "count", "mean", "sum"}))
