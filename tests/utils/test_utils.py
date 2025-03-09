import unittest
import sys
import os
import time
import concurrent.futures
import numpy as np
import random

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.utils import transform_interests

# 单元测试类
class TestTransformInterests(unittest.TestCase):

    def test_normal_case(self):
        """测试正常情况"""
        input_interests = ["Sports: Esports, Basketball", "Arts: Drawing", "Study:"]
        expected_output = {
            "Sports": ["Esports", "Basketball"],
            "Arts": ["Drawing"],
            "Study": []
        }
        self.assertEqual(transform_interests(input_interests), expected_output)

    def test_empty_interests(self):
        """测试空列表"""
        input_interests = []
        expected_output = {}
        self.assertEqual(transform_interests(input_interests), expected_output)

    def test_no_colon(self):
        """测试没有冒号的情况"""
        input_interests = ["Sports", "Arts", "Study"]
        expected_output = {
            "Sports": [],
            "Arts": [],
            "Study": []
        }
        self.assertEqual(transform_interests(input_interests), expected_output)

    def test_empty_items(self):
        """测试空兴趣项的情况"""
        input_interests = ["Sports:", "Arts: Drawing", "Study:"]
        expected_output = {
            "Sports": [],
            "Arts": ["Drawing"],
            "Study": []
        }
        self.assertEqual(transform_interests(input_interests), expected_output)

    def test_multiple_commas(self):
        """测试多个逗号分隔的情况"""
        input_interests = ["Sports: Esports, Basketball, Soccer", "Arts: Drawing, Painting"]
        expected_output = {
            "Sports": ["Esports", "Basketball", "Soccer"],
            "Arts": ["Drawing", "Painting"]
        }
        self.assertEqual(transform_interests(input_interests), expected_output)

    def test_whitespace(self):
        """测试包含额外空格的情况"""
        input_interests = ["  Sports  :  Esports  ,  Basketball  ", "  Arts  :  Drawing  "]
        expected_output = {
            "Sports": ["Esports", "Basketball"],
            "Arts": ["Drawing"]
        }
        self.assertEqual(transform_interests(input_interests), expected_output)

    def test_mixed_format(self):
        """测试混合格式的情况"""
        input_interests = ["Sports: Esports, Basketball", "Arts", "Study:"]
        expected_output = {
            "Sports": ["Esports", "Basketball"],
            "Arts": [],
            "Study": []
        }
        self.assertEqual(transform_interests(input_interests), expected_output)

# 运行测试
if __name__ == '__main__':
    unittest.main()