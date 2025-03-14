import unittest
from flask import Flask
import sys
import os
import time
import concurrent.futures
import numpy as np
import random

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app  # 替换为你的 Flask 应用模块名

# 活动列表
ACTIVITIES = [
    "Sports", "Arts", "General", "Academic", "Life Skills", "Social"
]

SPORTS = [
    "Martial Arts",
    "Basketball",
    "Fencing",
    "Wrestling",
    "Soccer",
    "Gymnastics",
    "Lacrosse",
    "Swimming",
    "Equestrian Sports",
    "Brazilian Jiu-Jitsu"
]

ACADEMIC = [
    "PreSchool",
    "Test Preparation",
    "Math",
    "STEM",
    "Coding",
    "Science",
    "Chess",
    "Reading",
    "Writing",
    "Special Needs Support"
]

ARTS = [
    "Music",
    "Painting",
    "Drawing",
    "Dance",
    "Theater",
    "Handcrafts",
    "Sculpture",
    "Musical",
    "Performing",
    "Ballet"
]


OTHERS = [
    "STEM", 
    "learning", 
    "program", 
    "children", 
    "education", 
    "skills", 
    "reading", 
    "writing", 
    "math", 
    "thinking"
]

# 纽约的邮编列表
ZIP_CODES = [
    "07072", "07646", "07083", "07039", "07506", "07004", "07076", "08202", "07024", 
    "07002", "08844", "07304", "07031", "07452", "07663", "07621", "07109", "08558", 
    "07901", "07002", "07751", "07001", "07928", "07470", "07039", "07310", "07930", 
    "07512", "07039", "07470", "07874", "07828", "08840", "07928", "07008", "07430", 
    "07008", "07430", "07940", "07008", "08820", "07112", "07712", "07932", "07012", 
    "07853", "07306", "11217", "07030", "07930", "07628", "07652", "07501", "10027", 
    "07105", "07981", "07104", "07083", "07747", "07105", "07452", "07601", "07435", 
    "07727", "07463", "07004", "07083", "07039", "08558", "07111", "07004", "07747", 
    "08872", "07036", "08872", "07039", "07304", "08822", "07470", "08822", "07508", 
    "07423", "18455", "18045", "08550", "07103", "07860", "08520", "07601", "08520", 
    "07058", "07058", "07042", "07083", "08520", "07080", "07058", "07040", "08520", 
    "07017", "07079", "10019", "08822", "07901", "07040", "07090", "07640", "10019", 
    "10016", "07090", "07040", "96816", "07940", "07028", "96816", "07940", "07424", 
    "07940", "96816", "07940", "07869", "96816", "07069", "96816", "08036", "08840", 
    "07307", "96816", "96816", "96816", "07760", "07740", "07076", "08088", "08831", 
    "07662", "07083", "07027", "07029", "08822", "08742", "07081", "34431", "07666", 
    "07932", "19380", "08734", "08822", "07853", "34431", "34431", "07624", "10128", 
    "07033", "08822", "07481", "07652", "07006", "10128", "07050", "07006", "07079", 
    "07481", "07006", "10128", "07050", "07013", "07050", "07731", "10128", "07650", 
    "07083", "07650", "07304", "07083", "07928", "07675", "08088", "07405", "07801", 
    "05471", "07801", "07044", "07005", "07005", "07650", "07650", "07650", "07605", 
    "07801", "07090", "33881", "07090", "08550", "07076", "07060", "08840", "07076", 
    "07107", "07039", "07076", "08840", "08820", "07090", "07090", "07001", "07076", 
    "07650", "08840", "07076", "07644", "07601", "07042", "07043", "07522", "07076", 
    "07601", "07059", "07059", "07059", "07675", "07003", "07932", "07059", "07003", 
    "77006", "07043", "07083", "07083", "07043", "07083", "07043", "07083", "07043", 
    "07083", "07043", "07083"
]

# 营地类型
CAMP_TYPES = ["AnyType", "FullDayCamp", "HalfDayCamp", "SleepawayCamp"]

# 营地选项
CAMP_OPTIONS = ["Indoor", "Outdoor", "Lunch", "EarlyDropoff", "Transportation", "LatePickup"]

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # 创建测试客户端
        self.app = app.test_client()
        self.app.testing = True

    def send_request(self, query, zip_code, radius, is_detail_search, age, camp_types, camp_options):
        """发送请求并返回响应时间和状态码"""
        start_time = time.time()
        final_query = query
        if query == "Sports":
            final_query += " " + random.choice(SPORTS)
        if query == "Academic":
            final_query += " " + random.choice(ACADEMIC)
        if query == "Arts":
            final_query += " " + random.choice(ARTS)
        
        for i in range(0, random.randint(1, 3)):
            final_query += " " + random.choice(OTHERS)

        url = f'/GetOfferingsTextQuery?search={query}&zipCode={zip_code}&radius={radius}&isDetailSearch={is_detail_search}'
        if is_detail_search.lower() == "true":
            
            url += f'&age={age}'
            for i, t in enumerate(camp_types):
                url += f'&campType={t}'
            for i, o in enumerate(camp_options):
                url += f'&campOptions={o}'

        response = self.app.get(url)
        end_time = time.time()
        is_empty = 0
        if response.status_code != 200:
            print(f"Error: {response.status_code} {url}")
        if response.status_code == 200 and len(response.get_json()) == 0:
            print(f"Warning: Empty response {url}")
            is_empty = 1
        return end_time - start_time, response.status_code, is_empty

    def test_pressure(self):
        """压力测试：多线程并发请求，持续 60 秒，每 5 秒打印吞吐量、百分位时延和成功率"""
        duration = 60  # 测试总时长（秒）
        interval = 5   # 打印间隔（秒）
        num_threads = 20  # 并发线程数

        start_time = time.time()
        latency_list = []  # 记录所有请求的时延
        interval_latency = []  # 记录当前 interval 的时延
        interval_start_time = start_time  # 当前 interval 的开始时间
        success_count = 0  # 记录成功的请求数
        interval_success_count = 0  # 记录当前 interval 的成功请求数
        is_empty_count = 0  # 记录空响应的请求数
        interval_is_empty_count = 0  # 记录当前 interval 的空响应的请求数

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            while time.time() - start_time < duration:
                # 如果进入新的 interval，打印统计量并重置
                if time.time() - interval_start_time >= interval:
                    # 计算当前 interval 的吞吐量、百分位时延和成功率
                    if interval_latency:
                        throughput = len(interval_latency) / interval
                        p50 = np.percentile(interval_latency, 50) * 1000
                        p90 = np.percentile(interval_latency, 90) * 1000
                        p99 = np.percentile(interval_latency, 99) * 1000
                        success_rate = (interval_success_count / len(interval_latency)) * 100
                        empty_rate = (interval_is_empty_count / len(interval_latency)) * 100
                        print(f"Throughput: {throughput:.2f} requests/s | Latency (ms): P50={p50:.2f}, P90={p90:.2f}, P99={p99:.2f} | Success Rate: {success_rate:.2f}% | Empty Rate: {empty_rate:.2f}%")

                    # 重置当前 interval 的统计量
                    interval_latency = []
                    interval_success_count = 0
                    interval_is_empty_count = 0
                    interval_start_time = time.time()

                # 提交请求
                futures = [executor.submit(self.send_request, 
                                           random.choice(ACTIVITIES), 
                                           random.choice(ZIP_CODES), 
                                           random.randint(5000, 10000), 
                                           random.choice(["true", "false"]), 
                                           random.randint(0, 20), 
                                           random.sample(CAMP_TYPES, random.randint(0, 1)), 
                                           random.sample(CAMP_OPTIONS, random.randint(0, 1))) 
                           for _ in range(num_threads)]

                # 处理完成的请求
                for future in concurrent.futures.as_completed(futures):
                    latency, status_code, is_empty = future.result()
                    latency_list.append(latency)
                    interval_latency.append(latency)
                    if status_code == 200:
                        success_count += 1
                        interval_success_count += 1
                    if is_empty == 1:
                        is_empty_count += 1
                        interval_is_empty_count += 1

                # 短暂休眠以避免过度占用 CPU
                time.sleep(0.1)

        # 打印总测试结果
        total_requests = len(latency_list)
        total_throughput = total_requests / duration
        avg_latency = np.mean(latency_list) * 1000
        p50 = np.percentile(latency_list, 50) * 1000
        p90 = np.percentile(latency_list, 90) * 1000
        p99 = np.percentile(latency_list, 99) * 1000
        total_success_rate = (success_count / total_requests) * 100
        total_empty_rate = (is_empty_count / total_requests) * 100

        print("\n=== Test Summary ===")
        print(f"Total Requests: {total_requests}")
        print(f"Average Throughput: {total_throughput:.2f} requests/s")
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"Latency (ms): P50={p50:.2f}, P90={p90:.2f}, P99={p99:.2f}")
        print(f"Success Rate: {total_success_rate:.2f}%")
        print(f"Empty Rate: {total_empty_rate:.2f}%")

if __name__ == '__main__':
    unittest.main()