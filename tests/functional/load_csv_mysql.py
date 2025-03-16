import pandas as pd
from sqlalchemy import create_engine

# CSV 文件路径
csv_file = '/Users/lion/Project/trustbees-search-backend/tests/functional/test_distance_filter_test.csv'

# 读取 CSV 文件
df = pd.read_csv(csv_file)

# 连接到 MySQL
engine = create_engine('mysql+pymysql://root:19990916@localhost/offering')

# 将数据导入 MySQL，自动创建表
df.to_sql('filtered_web_content_test', con=engine, if_exists='replace', index=False)

print("CSV 文件已成功导入 MySQL！")