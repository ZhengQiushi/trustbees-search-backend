import unittest, re, ast
import requests, json
import pandas as pd
from geopy.distance import geodesic
import os, sys
# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app  # 替换为你的 Flask 应用模块名
import global_vars
from utils.utils import * 
from itertools import combinations

# 营地类型和选项
CAMP_TYPES = ["AnyType", "FullDayCamp", "HalfDayCamp", "SleepawayCamp"]
CAMP_OPTIONS = ["Indoor", "Outdoor", "Lunch", "EarlyDropoff", "Transportation", "LatePickup"]

class TestGetOfferingsTextQuery(unittest.TestCase):
    # 计算 CSV 中符合条件的记录数
    def is_within_radius(self, row, radius, lat, lon):
        try:
            # 获取地理位置信息
            row_lat = row.get("location").get("geo_info", {}).get("lat")
            row_lon = row.get("location").get("geo_info", {}).get("lon")
            end_date = row.get("schedule", {}).get("endDate")
            # 过滤条件：geo_info 必须完整，endDate 不能为 None
            if end_date is None or end_date == "":
                return False  
            
            is_online = row.get("locationType") == "online"
            if is_online:
                return True
            if row_lat is None or row_lon is None:
                return False
            # 计算距离
            distance = geodesic((lat, lon), (row_lat, row_lon)).miles
            return distance <= radius
        except Exception:
            return False  # 避免异常导致计算终止
    def setUp(self):
        self.zip_code = "07072"

        # 创建测试客户端
        self.app = app.test_client()
        self.app.testing = True
        # 初始化全局变量
        global_vars.init_globals("/Users/lion/Project/trustbees-search-backend/config.env")
        # 加载数据集
        self.df = pd.read_csv("/Users/lion/Project/trustbees-search-backend/offering_dev.csv")

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
        self.df[["lat", "lon"]] = self.df["location"].apply(parse_location).apply(pd.Series)

        my_lat, my_lon = get_lat_lon_from_zip(self.zip_code)

        # 计算距离
        self.df["distance"] = self.df.apply(lambda row: calculate_distance(row["lat"], row["lon"], my_lat, my_lon), axis=1)

        # 解析 df["location"] 中的字符串
        def parse_location_string(location_str):
            # 替换 None 为 null
            location_str = location_str.replace("None", "\"\"")
            return ast.literal_eval(location_str)
        
        self.df["location"] = self.df["location"].apply(parse_location_string)
        self.df["schedule"] = self.df["schedule"].apply(parse_location_string)
        self.df["ageGroup"] = self.df["ageGroup"].apply(parse_location_string)

        # 解析 mainOfferingAddress 列，提取 lat 和 lon
        self.test_lat, self.test_lon = get_lat_lon_from_zip(self.zip_code)


    # def test_invalid_parameters1(self):
    #     # 测试非法传参
    #     # 1. zipCode 不是五位数字
    #     response = self.app.get(f"/GetOfferingsTextQuery?zipCode=1234&radius=10")
    #     self.assertEqual(response.status_code, 400)

    #     # 2. radius 不是数字
    #     response = self.app.get(f"/GetOfferingsTextQuery?zipCode=07072&radius=abc")
    #     self.assertEqual(response.status_code, 400)

    #     # 3. age 不是数字
    #     response = self.app.get(f"/GetOfferingsTextQuery?zipCode=07072&radius=10&age=abc")
    #     self.assertEqual(response.status_code, 400)

    #     # 4. campType 不是指定字符串
    #     response = self.app.get(f"/GetOfferingsTextQuery?zipCode=07072&radius=10&campType=InvalidType")
    #     self.assertEqual(response.status_code, 400)

    #     # 5. campOptions 不是指定字符串
    #     response = self.app.get(f"/GetOfferingsTextQuery?zipCode=07072&radius=10&campOptions=InvalidOption")
    #     self.assertEqual(response.status_code, 400)

    def test_distance_filter(self):
        # 测试距离筛选正确性
        # 1. 必须schedule的enddate>今天
        # 2. locationType=online不测距离

        radius = 10  # 10 miles
        response = self.app.get(f"/GetOfferingsTextQuery?pageLen=5000&zipCode={self.zip_code}&radius={radius}")
        self.assertEqual(response.status_code, 200)
        # 将 response.text 转换为 JSON 对象
        results = json.loads(response.text)['data']

        # 过滤符合条件的记录
        filtered_df = self.df[self.df.apply(lambda row: self.is_within_radius(row, radius=radius, lat=self.test_lat, lon=self.test_lon), axis=1)]

        # 计算符合条件的 businessID 的唯一个数
        unique_business_count = filtered_df["businessID"].nunique()

        # 断言检查
        self.assertEqual(len(results), unique_business_count)
            

#     def test_keyword_filter(self):
#         # 测试关键词筛选正确性
#         # 符合条件的数据条数：
#         radius = 10
#         search = "Basketball"
#         response = self.app.get(f"/GetOfferingsTextQuery?zipCode={self.zip_code}&radius={radius}&search={search}")
#         self.assertEqual(response.status_code, 200)
#         # 
#         results = json.loads(response.text)['data']

#         # 过滤符合条件的记录
#         filtered_df = self.df[self.df.apply(lambda row: self.is_within_radius(row, radius=radius, lat=self.test_lat, lon=self.test_lon), axis=1)]

#         # 计算 CSV 中符合条件的记录数
#         def contains_keyword(row):
#             return (
#                 search.lower() in row["activity"].lower() or
#                 search.lower() in row["activityCategory"].lower() or
#                 search.lower() in row["offeringName"].lower() or
#                 search.lower() in row["businessFullName"].lower() or
#                 search.lower() in row["offeringInsightSummary"].lower()
#             )


#         filtered_df = filtered_df[filtered_df.apply(contains_keyword, axis=1)]
#         # 计算符合条件的 businessID 的唯一个数
#         unique_business_count = filtered_df["businessID"].nunique()
        

#         self.assertEqual(len(results), unique_business_count)

#     def test_age_filter(self):
#         # 测试年龄筛选正确性
#         # 符合条件的数据条数：
#         #  1. 如果是null 默认 [0, 100]
#         zip_code = "07072"
#         radius = 10
#         age = 10
#         response = self.app.get(f"/GetOfferingsTextQuery?zipCode={zip_code}&radius={radius}&age={age}&pageLen=5000")
#         self.assertEqual(response.status_code, 200)
#         results = json.loads(response.text)['data']

#         # 计算 CSV 中符合条件的记录数
#         def is_within_age(row):
#             age_group = row["ageGroup"]
#             if age_group["gte"] != "" and int(age_group["gte"]) > age:
#                 return False
            
#             if age_group["lte"] != "" and int(age_group["lte"]) < age:
#                 return False
            
#             return True

#         results = json.loads(response.text)['data']
#         # 过滤符合条件的记录        
#         filtered_df = self.df[self.df.apply(lambda row: self.is_within_radius(row, radius=radius, lat=self.test_lat, lon=self.test_lon), axis=1)]

#         filtered_df = filtered_df[filtered_df.apply(lambda row: is_within_age(row), axis=1)]

#         unique_business_count = filtered_df["businessID"].nunique()


#         # 将 JSON 数据转换为 DataFrame
#         df = pd.DataFrame(results)
#         # 将 DataFrame 保存为 CSV 文件
#         df.to_csv("/Users/lion/Project/trustbees-search-backend/tests/functional/test_distance_filter_request.csv", index=False)
    
#         filtered_df.to_csv("/Users/lion/Project/trustbees-search-backend/tests/functional/test_distance_filter_test.csv", index=False)

#         self.assertEqual(len(results), unique_business_count)

#     def test_camp_type_filter(self):
#         # 测试营地类型筛选正确性
#         # 符合条件的数据条数：3 条，businessID: [9, 13, 105]
#         zip_code = "07072"
#         radius = 10

#         filtered_df = self.df[self.df.apply(lambda row: self.is_within_radius(row, radius=radius, lat=self.test_lat, lon=self.test_lon), axis=1)]

#         # 5.1 测试单项
#         for camp_option in CAMP_OPTIONS:
#             response = self.app.get(f"/GetOfferingsTextQuery?zipCode={zip_code}&radius={radius}&campOptions={camp_option}&pageLen=5000")
#             self.assertEqual(response.status_code, 200)
#             results = json.loads(response.text)['data']

#             # 计算 CSV 中符合条件的记录数
#             def contains_camp_type(row):
#                 row = row.fillna("")

#                 facility = row["facility"]
#                 lunchIncluded = row['lunchIncluded']
#                 latePickup = row['latePickup']
#                 lunchIncluded = row['lunchIncluded']
#                 transportation = row['transportation']
#                 earlyDropOff = row['earlyDropOff']
#                 try:
#                     if camp_option == "Indoor":
#                         return "indoor" in facility or "both" in facility
#                     elif camp_option == "Outdoor":
#                         return "outdoor" in facility or "both" in facility
#                     elif camp_option == "Lunch":
#                         return "yes" in lunchIncluded
#                     elif camp_option == "EarlyDropoff":
#                         return "yes" in earlyDropOff
#                     elif camp_option == "Transportation":
#                         return "yes" in transportation
#                     elif camp_option == "LatePickup":
#                         return "yes" in latePickup
#                 except Exception as e:
#                     print(str(e))

#             cur_filtered_df = filtered_df[filtered_df.apply(contains_camp_type, axis=1)]
#             unique_business_count = cur_filtered_df["businessID"].nunique()

#             self.assertEqual(len(results), unique_business_count)

#         # 计算 CSV 中符合条件的记录数
#         def more_contains_camp_type(row, camp_options):
#             row = row.fillna("")
            
#             facility = row["facility"]
#             lunchIncluded = row['lunchIncluded']
#             latePickup = row['latePickup']
#             lunchIncluded = row['lunchIncluded']
#             transportation = row['transportation']
#             earlyDropOff = row['earlyDropOff']
            
#             if "Indoor" in camp_options and "Outdoor" in camp_options:
#                 if "both" not in facility:
#                     return False
                
#             for option in camp_options:
#                 if option == "Indoor":
#                     if "indoor" not in facility and "both" not in facility:
#                         return False
#                 elif option == "Outdoor":
#                     if "outdoor" not in facility and "both" not in facility:
#                         return False
#                 elif option == "Lunch":
#                     if "yes" not in lunchIncluded:
#                         return False
#                 elif option == "EarlyDropoff":
#                     if "yes" not in earlyDropOff:
#                         return False
#                 elif option == "Transportation":
#                     if "yes" not in transportation:
#                         return False
#                 elif option == "LatePickup":
#                     if "yes" not in latePickup:
#                         return False
#             return True
        
#         for i in range(3, 7):
#             # 多项组合
#             print(i)
#             for camp_options in combinations(CAMP_OPTIONS, i):
#                 query_str = f"/GetOfferingsTextQuery?zipCode={zip_code}&radius={radius}&pageLen=5000"
#                 for i in camp_options:
#                     query_str += f"&campOptions=" + i

#                 response = self.app.get(query_str)
#                 self.assertEqual(response.status_code, 200)
#                 results = json.loads(response.text)['data']

#                 cur_filtered_df = filtered_df[filtered_df.apply(lambda row : more_contains_camp_type(row, camp_options=camp_options), axis=1)]
#                 unique_business_count = cur_filtered_df["businessID"].nunique()
#                 self.assertEqual(len(results), unique_business_count)
#                 print(unique_business_count, query_str)

#     def test_camp_options_filter(self):
#         # 测试营地选项筛选正确性
#         # 符合条件的数据条数：
#         zip_code = "07072"
#         radius = 10
        
#         filtered_df = self.df[self.df.apply(lambda row: self.is_within_radius(row, radius=radius, lat=self.test_lat, lon=self.test_lon), axis=1)]

#         # 计算 CSV 中符合条件的记录数
#         def more_contains_camp_options(row, camp_options):
#             row = row.fillna("")
#             optionstr = row["campSessionOptions"]
#             if "AnyType" in camp_options:
#                 return True
            
#             for option in camp_options:
#                 if option == "AnyType":
#                     continue

#                 if option == "FullDayCamp": 
#                     if option not in optionstr:
#                         return False
                        
#                 if option == "HalfDayCamp": 
#                     if option not in optionstr:
#                         return False
                    
#                 if option == "SleepawayCamp":
#                     if option not in optionstr:
#                         return False
#             return True
        
#         for i in range(1,5):
#             # 多项组合
#             for camp_options in combinations(CAMP_TYPES, i):
#                 query_str = f"/GetOfferingsTextQuery?zipCode={zip_code}&radius={radius}&pageLen=5000"
#                 for i in camp_options:
#                     query_str += f"&campType=" + i

#                 response = self.app.get(query_str)
#                 self.assertEqual(response.status_code, 200)
#                 results = json.loads(response.text)['data']

#                 cur_filtered_df = filtered_df[filtered_df.apply(lambda row: more_contains_camp_options(row, camp_options=camp_options), axis=1)]
#                 unique_business_count = cur_filtered_df["businessID"].nunique()
#                 self.assertEqual(len(results), unique_business_count)
#                 print(unique_business_count, query_str)


if __name__ == "__main__":
    unittest.main()