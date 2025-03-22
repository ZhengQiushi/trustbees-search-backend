import pandas as pd
import ast
from geopy.distance import geodesic
import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import *

# 定义给定的经纬度
zip_code = '07078'
my_lat, my_lon = get_lat_lon_from_zip(zip_code)
	
path = "/Users/lion/Project/trustbees-search-backend/"
# 读取 CSV 文件
df = pd.read_csv(path + "offering_dev.csv")

# 解析 mainOfferingAddress 列，提取 lat 和 lon
def parse_location(address):
    try:
        # 将字符串转换为字典
        address_dict = ast.literal_eval(address)
        location = address_dict.get("geo_info", {})
        return location.get("lat"), location.get("lon")
    except (ValueError, SyntaxError, AttributeError):
        return None, None

# 计算距离
def calculate_distance(row_lat, row_lon, my_lat, my_lon):
    if pd.notna(row_lat) and pd.notna(row_lon):
        return geodesic((row_lat, row_lon), (my_lat, my_lon)).miles
    return None

# 解析 lat 和 lon
df[["lat", "lon"]] = df["location"].apply(parse_location).apply(pd.Series)

# 计算距离
df["distance"] = df.apply(lambda row: calculate_distance(row["lat"], row["lon"], my_lat, my_lon), axis=1)

# 保存结果到新的 CSV 文件
df.to_csv(path + "filtered_web_content_with_distance.csv", index=False)

print("加工完成，结果已保存到 filtered_web_content_with_distance.csv")