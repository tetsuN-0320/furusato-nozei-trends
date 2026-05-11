import pandas as pd

df = pd.read_parquet('data/processed/products_raw.parquet')            
print(df.dtypes)                                                       
print()
print(df.head(3).to_string())                                          
print()                                                   
print('価格帯:')                                                       
print(df['item_price'].describe())
print()                                                                
print('キーワード別件数:')                                
print(df['search_keyword'].value_counts())     