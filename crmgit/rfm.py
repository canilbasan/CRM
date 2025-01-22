# BUSINESS PROBLEM
# DATA UNDERSTANDING
# DATA PREPARATION
# CALCULATION OF RFM METRICS
# CALCULATION OF RFM SCORES
# CREATION AND ANALYSIS OF RFM SEGMENTS
# FUNCTIONALIZING THE ENTIRE PROCESS


# BUSINESS PROBLEM

# An e-commerce company wants to segment its customers and determine marketing strategies based on these segments.


# DATA UNDERSTANDING

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: "%.3f" % x)

df_ = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2009-2010")
df = df_.copy()

# Uncomment the following lines to print the data exploration outputs
# print(df.head())
# print(df.shape)
# print("777777777777777777777777")
# print(df.isnull().sum())
# print("777777777777777777777777")
# print(df["Description"].nunique())
# print("777777777777777777777777")
# print(df["Description"].value_counts().head())
# print("777777777777777777777777")
# print(df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head())

df["TotalPrice"] = df["Quantity"] * df["Price"]
print(df["TotalPrice"])
print("Total price")
print(df.groupby("Invoice").agg({"TotalPrice": "sum"}).head())

# DATA PREPARATION

print(df.shape)
print(df.isnull().sum())
df.dropna(inplace=True)
print(df.shape)

# Since price can't be negative, we need to remove returns from the data.
# Return transactions corrupt the data.
print(df.describe().T)

print("Removing returns")
df = df[~df["Invoice"].str.contains("C", na=False)]


# CALCULATION OF RFM METRICS

# Recency, Frequency, Monetary

import datetime as dt
print(df["InvoiceDate"].max())

today_date = dt.datetime(2010, 12, 11)
print(type(today_date))

rfm = df.groupby("Customer ID").agg({"InvoiceDate": lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
                                     "Invoice": lambda Invoice: Invoice.nunique(),
                                     "TotalPrice": lambda TotalPrice: TotalPrice.sum()})

print("Outputs")
print(rfm.head())
rfm.columns = ["recency", "frequency", "monetary"]
print("Let's check the descriptive statistics.")

print(rfm.describe().T)

rfm = rfm[rfm["monetary"] > 0]
print(rfm.head())
print(rfm.shape)

# CALCULATION OF RFM SCORES

rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1])
# Splits into 5 parts (0-100, 0-20, 20-40, 40-60, 60-80, 80-100) and assigns labels accordingly.

rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5])
print(rfm.head())

rfm["RFM_SCORE"] = (rfm["recency_score"].astype(str) +
                   rfm["frequency_score"].astype(str))
print(rfm["RFM_SCORE"])

print("Let's check the descriptive statistics")
print(rfm.describe().T)

print("Who are the champions?")
"""
print(rfm["RFM_SCORE"] == "55")
"""

# CREATION AND ANALYSIS OF RFM SEGMENTS

# Using Regex

seg_map = {
    r'[1-2][1-2]': "hibernating",
    r'[1-2][3-4]': "at_Risk",
    r'[1-2]5': "cant_loose",
    r'3[1-2]': "about_to_sleep",
    r'33': "need_attention",
    r'[3-4][4-5]': "loyal_customers",
    r'41': "promising",
    r'51': "new_customers",
    r'[4-5][2-3]': "potential_loyalists",
    r'5[4-5]': "champions"
}

rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)
print(rfm)
print("AVERAGES")
print(rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"]))
print("Let's look at some special customers, for example ")

new_df = pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index
new_df["new_customer_id"] = new_df["new_customer_id"].astype(int)
print(new_df)
new_df.to_csv("new_customers.csv")
