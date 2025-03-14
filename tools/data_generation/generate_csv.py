import csv
import concurrent.futures
import pandas as pd
from ast import literal_eval
import sys
import os
import google.generativeai as genai
from datetime import datetime  # 导入 datetime 模块

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


import os

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['all_proxy'] = 'socks5://127.0.0.1:7890'


import config

# 设置 Google API 密钥
# genai.configure(api_key=config.GEMINI_KEY)

import google.generativeai as genai

genai.configure(
    api_key=config.GOOGLE_API_KEY,
    transport="rest",  # 使用 REST 而不是 gRPC
)

# 定义生成测试数据的函数
def generate_test_data(thread_id, num_records):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_data_thread_{thread_id}_{timestamp}.csv"  # 在文件名中添加时间戳
    
    fieldnames = [
        "RSVP", "RSVPDeadline", "activity", "activityCategory", "ageGroup",
        "businessFullName", "campAmenities", "campSessionOptions", "facility",
        "hyperlink", "location", "locationDisplayName", "locationType",
        "lunchIncluded", "name", "offeringInsightSummary", "offeringName",
        "offeringType", "pricing", "schedule", "skillLevel", "sourceLink",
        "transportation"
    ]

    # 打开 CSV 文件并写入表头
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        file.flush()

        remaining_records = num_records
        while remaining_records > 0:
            # 使用 Gemini API 生成数据
            prompt = """
            ---
            Role Description:
            You are a data generator assistant. Your task is to generate synthetic test data for a summer camp registration system. The data should be realistic, diverse, and follow the provided CSV format strictly.
            ---

            CSV Format Description:
            The CSV has 27 fields. Each field is described below:
            1. RSVP: String, e.g., ''
            2. RSVPDeadline: Date, e.g., '2023-07-17'
            3. activity: String, e.g., 'Martial Arts'
            4. activityCategory: String, e.g., 'Sports'
            5. ageGroup: JSON, e.g., '{"gte": 0, "lte": 100}'
            6. businessFullName: String, e.g., 'AllStar Martial Arts'
            7. campAmenities: String, e.g., ''
            8. campSessionOptions: String, e.g., 'AnyType', 'HalfDayCamp', 'SleepawayCamp', 'FullDay Camp'
            9. facility: String, e.g., 'indoor' / 'outdoor' / 'both'
            10. hyperlink: List, e.g., ['Sign up today: https://example.com']
            11. location: JSON, e.g., '{"name": "1166 West Chestnut St, Union, NJ, 07083, USA", "geo_info": {"lon": -74.2862706, "lat": 40.6924411}}'
            12. locationDisplayName: String, e.g., 'Union, NJ'
            13. locationType: String, e.g., 'in_person', 'online'
            14. lunchIncluded: String, e.g., 'no' / 'yes'
            15. name: String, e.g., 'Summer Camp'
            16. offeringInsightSummary: String, e.g., 'Includes martial arts workouts\\nFeatures relay races and obstacle courses\\nOffers early bird special pricing'
            17. offeringName: String, e.g., ''
            18. offeringType: String, e.g., 'Summer Camp'
            19. pricing: List, e.g., ['$249 first child', '$25 off additional child', 'Earlybird Before $199']
            20. schedule: JSON, e.g., '[{"classDay": "Monday, Tuesday, Wednesday, Thursday, Friday", "endDate": "2023-07-21", "durationSeason": null, "time": "09:00-14:00", "startDate": "2023-07-17", "frequency": null, "blackoutDate": null}]'
            21. skillLevel: String, e.g., ''
            22. sourceLink: String, e.g., 'https://example.com/summer-camp/'
            23. transportation: String, e.g., 'no' / 'yes'
            24. offeringID: String, 10-character unique ID
            25. businessID: String, 10-character ID (some courses may share the same businessID)
            26. earlyDropOff: String, e.g., 'no' / 'yes'
            27. latePickup: String, e.g., 'no' / 'yes'

            Output Requirements:
            - Generate a list of 10 records.
            - Each record should be a dictionary with the 27 fields described above.
            - Return only the list of dictionaries as a valid Python list. Do not include any explanations or additional text.

            Few-shot Examples:
            Here are 2 example records:

            [
                {
                    "RSVP": "",
                    "RSVPDeadline": "2023-07-17",
                    "activity": "Martial Arts",
                    "activityCategory": "Sports",
                    "ageGroup": '{"gte": 6, "lte": 12}',
                    "businessFullName": "AllStar Martial Arts",
                    "campAmenities": "",
                    "campSessionOptions": "Full day camp",
                    "facility": "indoor",
                    "hyperlink": ["Sign up today: https://example.com"],
                    "location": '{"name": "1166 West Chestnut St, Union, NJ, 07083, USA", "geo_info": {"lon": -74.2862706, "lat": 40.6924411}}',
                    "locationDisplayName": "Union, NJ",
                    "locationType": "in_person",
                    "lunchIncluded": "no",
                    "name": "Summer Camp",
                    "offeringInsightSummary": "Includes martial arts workouts\\nFeatures relay races and obstacle courses\\nOffers early bird special pricing",
                    "offeringName": "",
                    "offeringType": "Summer Camp",
                    "pricing": ["$249 first child", "$25 off additional child", "Earlybird Before $199"],
                    "schedule": '[{"classDay": "Monday, Tuesday, Wednesday, Thursday, Friday", "endDate": "2023-07-21", "durationSeason": null, "time": "09:00-14:00", "startDate": "2023-07-17", "frequency": null, "blackoutDate": null}]',
                    "skillLevel": "",
                    "sourceLink": "https://example.com/summer-camp/",
                    "transportation": "no",
                    "offeringID": "CAMP001234",
                    "businessID": "BUSI001234",
                    "earlyDropOff": "yes",
                    "latePickup": "no"
                },
                {
                    "RSVP": "",
                    "RSVPDeadline": "2023-08-01",
                    "activity": "Coding Camp",
                    "activityCategory": "STEM",
                    "ageGroup": '{"gte": 8, "lte": 14}',
                    "businessFullName": "Code Ninjas",
                    "campAmenities": "Computers, Snacks",
                    "campSessionOptions": "HalfDayCamp",
                    "facility": "indoor",
                    "hyperlink": ["Sign up today: https://codeninjas.com/summer-camp"],
                    "location": '{"name": "123 Main St, Springfield, IL, 62701, USA", "geo_info": {"lon": -89.650148, "lat": 39.781721}}',
                    "locationDisplayName": "Springfield, IL",
                    "locationType": "in_person",
                    "lunchIncluded": "yes",
                    "name": "Summer Coding Camp",
                    "offeringInsightSummary": "Learn Python and Scratch\\nBuild fun projects\\nEarly bird discounts available",
                    "offeringName": "",
                    "offeringType": "Summer Camp",
                    "pricing": ["$299 first child", "$50 off additional child", "Earlybird Before $249"],
                    "schedule": '[{"classDay": "Monday, Wednesday, Friday", "endDate": "2023-08-15", "durationSeason": null, "time": "10:00-15:00", "startDate": "2023-08-01", "frequency": null, "blackoutDate": null}]',
                    "skillLevel": "Beginner",
                    "sourceLink": "https://codeninjas.com/summer-camp",
                    "transportation": "no",
                    "offeringID": "CAMP002345",
                    "businessID": "BUSI002345",
                    "earlyDropOff": "no",
                    "latePickup": "yes"
                }
            ]

            Task:
            Generate a list of 10 records following the format above. Return only the list of dictionaries as a valid Python list. Do not include any explanations or additional text.

            Note!!!
            Don't return ```python``` and ```json```.
            Just return a pure text that literal_eval can parse!
            !!!
            """
            response = None
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')  # 使用 Gemini 1.5 Flash 模型
                response = model.generate_content(prompt)
            except Exception as e:
                print(f"Thread {thread_id}: Stop Unexpectedly...")
                print(e)
                return filename
            # 获取生成的文本
            generated_text = response.text.strip()
            generated_text = generated_text.replace("```json", "")
            generated_text = generated_text.replace("```", "")
            generated_text = generated_text.replace("```python", "")
            generated_text = generated_text.replace("```", "")

            try:
                # 尝试将生成的文本解析为Python List
                records = literal_eval(generated_text)
                if not isinstance(records, list) or len(records) == 0:
                    raise ValueError("Generated data is not a valid list.")

                # 检查每条记录的格式
                for record in records:
                    if isinstance(record, dict) and len(record) == 23:  # 确保每条记录是字典且有23个字段
                        # 写入 CSV 文件
                        writer.writerow(record)
                        file.flush()
                        remaining_records -= 1
                
                print(f"Thread {thread_id}: Generated {num_records - remaining_records}/{num_records} records.")

            except (ValueError, SyntaxError) as e:
                print(f"Thread {thread_id}: Invalid format in generated data. Retrying...")
                print(e)
                print(generated_text)
                continue

    return filename

# 定义合并 CSV 文件的函数
def merge_csv_files(filenames, output_filename):
    dfs = []
    for filename in filenames:
        df = pd.read_csv(filename)
        dfs.append(df)

    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df.to_csv(output_filename, index=False)

# 主函数
def main():
    num_threads = 10  # 线程数
    num_records_per_thread = 100  # 每个线程生成的记录数
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 获取当前时间戳
    output_filename = f"merged_test_data_{timestamp}.csv"  # 在合并后的文件名中添加时间戳


    # 使用线程池生成数据
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(generate_test_data, i, num_records_per_thread) for i in range(num_threads)]
        filenames = [future.result() for future in concurrent.futures.as_completed(futures)]

    # 合并生成的 CSV 文件
    merge_csv_files(filenames, output_filename)
    print(f"All data has been generated and merged into {output_filename}")

if __name__ == "__main__":
    main()