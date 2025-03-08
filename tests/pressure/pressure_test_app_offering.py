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
    "Martial Arts", "Archery", "Fencing", "Karate", "Lacrosse", "Gymnastics", "Surfing", "Basketball", "Equestrian",
    "Physical Activities", "Hip Hop", "Cycling", "Softball", "Ice Skating", "Football", "Wrestling", "Cricket", "Tennis",
    "Rock Climbing", "Soccer", "Futsal", "Ninja", "Parkour", "Dance", "Boxing", "Camping", "Chess", "Skateboarding",
    "Hockey", "Judo", "Swimming", "Taekwondo", "Cheerleading", "Brazilian Jiu-Jitsu", "MMA", "Squash", "Water Polo",
    "Diving", "Badminton", "Paintball", "Bowling", "Kung Fu", "Wushu", "Lion Dance", "Cultural Activities"
]

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # 创建测试客户端
        self.app = app.test_client()
        self.app.testing = True


    def send_request(self, query, conditions):
        """发送请求并返回响应时间"""
        start_time = time.time()
        response = self.app.get(f'/GetOfferingsTextQuery?query={query}&conditions={conditions}')
        end_time = time.time()
        return end_time - start_time, response.status_code

    def test_pressure(self):
        """压力测试：多线程并发请求，持续 60 秒，每 5 秒打印吞吐量和百分位时延"""
        conditions = '{"page_len": 15}'
        duration = 60  # 测试总时长（秒）
        interval = 5   # 打印间隔（秒）
        num_threads = 10  # 并发线程数

        start_time = time.time()
        latency_list = []  # 记录所有请求的时延
        interval_latency = []  # 记录当前 interval 的时延
        interval_start_time = start_time  # 当前 interval 的开始时间

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            while time.time() - start_time < duration:
                # 如果进入新的 interval，打印统计量并重置
                if time.time() - interval_start_time >= interval:
                    # 计算当前 interval 的吞吐量和百分位时延
                    if interval_latency:
                        throughput = len(interval_latency) / interval
                        p50 = np.percentile(interval_latency, 50) * 1000
                        p90 = np.percentile(interval_latency, 90) * 1000
                        p99 = np.percentile(interval_latency, 99) * 1000
                        print(f"Throughput: {throughput:.2f} requests/s | Latency (ms): P50={p50:.2f}, P90={p90:.2f}, P99={p99:.2f}")

                    # 重置当前 interval 的统计量
                    interval_latency = []
                    interval_start_time = time.time()

                # 提交请求
                futures = [executor.submit(self.send_request, random.choice(ACTIVITIES), conditions) for _ in range(num_threads)]

                # 处理完成的请求
                for future in concurrent.futures.as_completed(futures):
                    latency, status_code = future.result()
                    if status_code == 200:
                        latency_list.append(latency)
                        interval_latency.append(latency)

                # 短暂休眠以避免过度占用 CPU
                time.sleep(0.1)

        # 打印总测试结果
        total_requests = len(latency_list)
        total_throughput = total_requests / duration
        avg_latency = np.mean(latency_list) * 1000
        p50 = np.percentile(latency_list, 50) * 1000
        p90 = np.percentile(latency_list, 90) * 1000
        p99 = np.percentile(latency_list, 99) * 1000

        print("\n=== Test Summary ===")
        print(f"Total Requests: {total_requests}")
        print(f"Average Throughput: {total_throughput:.2f} requests/s")
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"Latency (ms): P50={p50:.2f}, P90={p90:.2f}, P99={p99:.2f}")

if __name__ == '__main__':
    unittest.main()