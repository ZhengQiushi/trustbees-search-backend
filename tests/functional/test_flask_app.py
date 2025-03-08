import unittest
from flask import Flask
import sys, os
import pandas as pd

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
                
from app import app  # 替换为你的 Flask 应用模块名

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # 创建测试客户端
        self.app = app.test_client()
        self.app.testing = True

    def test_get_business_full_name(self):
        # 测试 GetBusinessFullName 接口
        response = self.app.get('/GetBusinessFullName?businessFullName=Pioneer%20Academy')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # 假设返回的是一个列表
        self.assertEqual(len(data), 1)  # 断言列表长度为 1

        # 检查列表中的第一个元素是否包含预期的字段
        first_item = data[0]["_source"]
        self.assertIn("businessFullName", first_item)  # 断言包含 businessFullName 字段
        self.assertEqual(first_item["businessFullName"], "Pioneer Academy")  # 断言字段值正确
        
    def test_get_business_full_name_missing_parameter(self):
        # 测试缺少 businessFullName 参数的情况
        response = self.app.get('/GetBusinessFullName')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_get_query(self):
        # 测试 GetQuery 接口
        response = self.app.get('/GetQuery?query=Studio')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # 假设返回的是一个列表
        self.assertEqual(len(data), 49)  # 断言列表长度为 49

    def test_get_query_missing_parameter(self):
        # 测试缺少 query 参数的情况
        response = self.app.get('/GetQuery')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_get_query_with_conditions(self):
        # 测试带条件的 GetQuery 接口
        conditions = '{"min_rating": 4.9}'
        response = self.app.get(f'/GetQuery?query=Studio&conditions={conditions}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # 假设返回的是一个列表
        self.assertEqual(len(data), 31)  # 断言列表长度为 31

    def test_get_query_with_conditions(self):
        # 测试带条件的 GetQuery 接口
        conditions = '{"location": {"lat": 40.6524315, "lon": -74.1282894}, "distance": "10km", "min_rating": 4.9}'
        response = self.app.get(f'/GetQuery?query=Studio&conditions={conditions}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # 假设返回的是一个列表
        self.assertEqual(len(data), 2)  # 断言列表长度为 2


    def test_get_query_invalid_conditions(self):
        # 测试无效的 conditions 参数
        conditions = 'invalid_json'
        response = self.app.get(f'/GetQuery?query=Studio&conditions={conditions}')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

if __name__ == '__main__':
    unittest.main()