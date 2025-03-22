import csv

# 读取CSV文件
input_file = '/Users/lion/Project/trustbees-search-backend/offering_dev.csv'  # 替换为你的CSV文件路径
output_file = '/Users/lion/Project/trustbees-search-backend/activities.txt'  # 输出的TXT文件路径

# 创建一个集合来存储所有唯一的activity
activities_set = set()

# 打开CSV文件并读取内容
with open(input_file, mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)  # 使用DictReader读取CSV
    for row in reader:
        # 获取activity列的内容，并按逗号分割
        activities = row['activity'].split(', ')
        # 将分割后的内容添加到集合中
        activities_set.update(activities)

# 将集合中的内容导出到TXT文件
with open(output_file, mode='w', encoding='utf-8') as txtfile:
    # 将集合转换为逗号分隔的字符串
    activities_str = ', '.join(sorted(activities_set))  # 排序后导出
    txtfile.write(activities_str)

print(f"处理完成！结果已导出到 {output_file}")