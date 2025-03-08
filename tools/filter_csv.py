import pandas as pd
import ast
from geopy.distance import geodesic

# 定义给定的经纬度
my_lat = 40.6524315  # 示例：纽约市的纬度
my_lon = -74.1282894  # 示例：纽约市的经度

	
path = "/Users/lion/Project/trustbees-search-backend/tools/"
# 读取 CSV 文件
df = pd.read_csv(path + "studio_query_results.csv")

# 解析 mainOfferingAddress 列，提取 lat 和 lon
def parse_location(address):
    try:
        # 将字符串转换为字典
        address_dict = ast.literal_eval(address)
        location = address_dict.get("location", {})
        return location.get("lat"), location.get("lon")
    except (ValueError, SyntaxError, AttributeError):
        return None, None

# 计算距离
def calculate_distance(row_lat, row_lon, my_lat, my_lon):
    if pd.notna(row_lat) and pd.notna(row_lon):
        return geodesic((row_lat, row_lon), (my_lat, my_lon)).km
    return None

# 解析 lat 和 lon
df[["lat", "lon"]] = df["mainOfferingAddress"].apply(parse_location).apply(pd.Series)

# 计算距离
df["distance"] = df.apply(lambda row: calculate_distance(row["lat"], row["lon"], my_lat, my_lon), axis=1)

# 保存结果到新的 CSV 文件
df.to_csv(path + "filtered_web_content_with_distance.csv", index=False)

print("加工完成，结果已保存到 filtered_web_content_with_distance.csv")