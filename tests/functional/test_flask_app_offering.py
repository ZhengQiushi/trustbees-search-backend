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

    # def test_get_query(self):
    #     # 测试 GetQuery 接口
    #     response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=5')

    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 15)

    # def test_get_query_conditions(self):
    #     # 测试 GetQuery 接口
    #     response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=5&isDetailSearch=true&campOptions=Indoor&campOptions=Outdoor')

    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 8)

    # def test_get_query_conditions_age(self):
    #     # 测试 GetQuery 接口
    #     response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=5&isDetailSearch=true&campOptions=Indoor&campOptions=Outdoor&age=3')

    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 6)


    # def test_get_query_conditions_age(self):
    #     # 测试 GetQuery 接口
    #     response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=1')

    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 4)


    # def test_get_query_conditions_camp_types(self):
    #     # 测试 GetQuery 接口
    #     response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=5000&isDetailSearch=true&campType=Sleepaway&campType=Full%20Day')

    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 15)

    # def test_get_query_conditions_camp_types(self):
    #     # 测试 GetQuery 接口
    #     response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=50000&isDetailSearch=true&campType=Sleepaway')

    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 3)

    def test_get_query_conditions_unique_provider_page(self):
        # 测试 GetQuery 接口
        response = self.app.get(f'/GetOfferingsTextQuery?search=Sports&zipCode=07083&radius=3')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)  # 假设返回的是一个列表
        self.assertEqual(len(data), 15)

    # def test_get_query_missing_parameter(self):
    #     # 测试缺少 query 参数的情况
    #     response = self.app.get('/GetOfferingsTextQuery')
    #     self.assertEqual(response.status_code, 400)
    #     data = response.get_json()
    #     self.assertIn("error", data)

    # def test_get_query_with_conditions(self):
    #     # 测试带条件的 GetQuery 接口
    #     conditions = '{"location": {"lat": 42.1073251, "lon": -72.5813903}, "distance": "10km"}'
    #     response = self.app.get(f'/GetOfferingsTextQuery?query=Fencing&conditions={conditions}')
    #     self.assertEqual(response.status_code, 200)
    #     data = response.get_json()
    #     self.assertIsInstance(data, list)  # 假设返回的是一个列表
    #     self.assertEqual(len(data), 4)  # 断言列表长度为 2


    # def test_get_query_invalid_conditions(self):
    #     # 测试无效的 conditions 参数
    #     conditions = 'invalid_json'
    #     response = self.app.get(f'/GetQuery?query=Studio&conditions={conditions}')
    #     self.assertEqual(response.status_code, 400)
    #     data = response.get_json()
    #     self.assertIn("error", data)

if __name__ == '__main__':
    unittest.main()