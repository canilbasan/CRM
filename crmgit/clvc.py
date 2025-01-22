# CUSTOMER LIFETIME VALUE CALCULATION

# 1. PREPARING THE DATA
# 2. AVERAGE ORDER VALUE (TOTAL_PRICE / TOTAL_TRANSACTION)
# 3. PURCHASE FREQUENCY (TOTAL_TRANSACTION / TOTAL_NUMBER_OF_CUSTOMERS)
# 4. REPEAT RATE & CHURN RATE (NUMBER OF CUSTOMERS WITH MULTIPLE PURCHASES / TOTAL CUSTOMERS)
# 5. PROFIT MARGIN (PROFIT_MARGIN = TOTAL_PRICE * 0.10)
# 6. CUSTOMER VALUE (CUSTOMER_VALUE = AVERAGE_ORDER_VALUE * PURCHASE_FREQUENCY)
# 7. CUSTOMER LIFETIME VALUE (CLTV = (CUSTOMER_VALUE / CHURN_RATE) * PROFIT_MARGIN)
# 8. CREATING SEGMENTS
# 9. FUNCTIONALIZATION

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: "%.5f" % x)

df_ = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2009-2010")
df = df_.copy()
print(df.head())

df = df[~df["Invoice"].str.contains("C", na=False)]
print(df.describe().T)
df.dropna(inplace=True)
df = df[(df["Quantity"] > 0)]
print(df.head())
print(df.describe().T)

# Calculating TotalPrice
df["TotalPrice"] = df["Quantity"] * df["Price"]
print(df.head())

# Calculating some metrics
# Total price and Total transaction are required

cltv_c = df.groupby("Customer ID").agg({
    "Invoice": lambda x: x.nunique(),
    "Quantity": lambda x: x.sum(),
    "TotalPrice": lambda x: x.sum()
})

print(cltv_c)

cltv_c.columns = ["total_transaction", "total_unit", "total_price"]
print(cltv_c)

# 2. AVERAGE ORDER VALUE (TOTAL_PRICE / TOTAL_TRANSACTION)
cltv_c["average_order_value"] = cltv_c["total_price"] / cltv_c["total_transaction"]

print(cltv_c)

# 3. PURCHASE FREQUENCY (TOTAL_TRANSACTION / TOTAL_NUMBER_OF_CUSTOMERS)
# The number of customers corresponds to the number of rows in the dataset
# because we only took unique values using nunique.

cltv_c["purchase_frequency"] = cltv_c["total_transaction"] / cltv_c.shape[0]

print(cltv_c)

# 4. REPEAT RATE & CHURN RATE (NUMBER OF CUSTOMERS WITH MULTIPLE PURCHASES / TOTAL CUSTOMERS)

# Repeat rate
repeat_rate = cltv_c[cltv_c["total_transaction"] > 1].shape[0] / cltv_c.shape[0]

# Churn rate
churn_rate = 1 - repeat_rate

print(churn_rate)

# 5. PROFIT MARGIN (PROFIT_MARGIN = TOTAL_PRICE * 0.10)
cltv_c["profit_margin"] = cltv_c["total_price"] * 0.10
print(cltv_c)

# 6. CUSTOMER VALUE (CUSTOMER_VALUE = AVERAGE_ORDER_VALUE * PURCHASE_FREQUENCY)

cltv_c["customer_value"] = cltv_c["average_order_value"] * cltv_c["purchase_frequency"]
print(cltv_c)

# 7. CUSTOMER LIFETIME VALUE (CLTV = (CUSTOMER_VALUE / CHURN_RATE) * PROFIT_MARGIN)
cltv_c["cltv"] = (cltv_c["customer_value"] / churn_rate) * cltv_c["profit_margin"]

print(cltv_c)
print("Sorted Version")

print(cltv_c.sort_values(by="cltv", ascending=False).head())
print(cltv_c.describe().T)

# 8. CREATING SEGMENTS

cltv_c["segment"] = pd.qcut(cltv_c["cltv"], 4, labels=["D", "C", "B", "A"])
print(cltv_c.head())

# Analyze the results
print(cltv_c.groupby("segment").agg(["count", "mean", "sum"]))

# Save the results to a CSV file
cltv_c.to_csv("cltv.csv")
