import pandas as pd

# 读取两张表
table2 = pd.read_csv('/Users/lion/Project/trustbees-search-backend/merged_table.csv')
table1 = pd.read_csv('/Users/lion/Project/trustbees-search-backend/offering_dev.csv')

# 通过 businessFullName 列进行 join 操作，并将表1的 id 拼接到表2上
merged_table = pd.merge(table1, table2[['Name', 'Rating', 'Rating Count']], left_on='businessFullName', right_on='Name', how='left')

# 生成新的表并保存为 CSV 文件
merged_table.to_csv('merged_table_offering.csv', index=False)

print("合并后的表已保存为 'merged_table_offering.csv'")