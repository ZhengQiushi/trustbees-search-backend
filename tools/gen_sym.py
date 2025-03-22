import time 
from google import genai

client = genai.Client(api_key="AIzaSyAcVqX_lu50ZR2gzDGo7hkXS6WxSc4yXdE")


# 从 activities.txt 文件中读取单词
with open("/Users/lion/Project/trustbees-search-backend/activities.txt", "r") as file:
    content = file.read().strip()  # 读取文件内容并去除首尾空白
    words = [word.strip() for word in content.split(",")]  # 按逗号分割并去除每个单词的空白

# 用于存储同义词的字典
synonyms_dict = {}

# 为每个单词生成同义词
for word in words:
    try:
        # 调用 Gemini 生成同义词
        time.sleep(2)
        query = f"Generate 3-5 synonyms for the word '{word}'. Return the synonyms as a comma-separated list. Pure text. withou any explanation"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=query,
        )

        # 提取生成的同义词
        synonyms = response.text.strip().split(", ")
        # 将单词和同义词存入字典
        synonyms_dict[word] = synonyms
        print(f"Generated synonyms for '{word}': {', '.join(synonyms)}")
    except Exception as e:
        print(f"Error generating synonyms for '{word}': {e}")

# 将结果写入 synonyms.txt 文件
with open("synonyms.txt", "w") as f:
    for word, synonyms in synonyms_dict.items():
        # 将单词和同义词组合成一行，用逗号分隔
        synonym_line = f"{word}, {', '.join(synonyms)}"
        f.write(synonym_line + "\n")

print("Synonyms have been written to synonyms.txt")