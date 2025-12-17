import requests
from bs4 import BeautifulSoup
import json
import pymysql
import os

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 4000,
    "user": "root",
    "password": "",
    "database": "pokefarm",
    "charset": "utf8mb4"
}

# 本地保存图片的真实路径（给爬虫用）
SPRITE_SAVE_DIR = r"D:\\code\\Games\\Pokefarm\\frontend\\pokefarm_front\\src\\assets\\pokemons"
NAME_JSON_PATH = r"d:\\code\\Games\\Pokefarm\\scripts\\pokedex_national_simple.json"

os.makedirs(SPRITE_SAVE_DIR, exist_ok=True)

# -------------------------
# 加载英文名 -> 中文名映射
# -------------------------
def load_name_mapping():
    with open(NAME_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {entry["name_en"]: entry["name"] for entry in data}

# -------------------------
# 稀有度计算（250 起步，50 递进，最高 10）
# -------------------------
def calc_rarity(total):
    if total < 250:
        return 1
    r = 1 + (total - 250) // 50
    return min(r, 10)

name_map = load_name_mapping()

url = "https://pokemondb.net/pokedex/all"
soup = BeautifulSoup(requests.get(url).text, 'html.parser')
rows = soup.select("table#pokedex tr")

# -------------------------
# 收集每个全国编号的所有形态
# -------------------------
all_forms = {}

for row in rows[1:]:
    cols = row.find_all("td")
    if not cols:
        continue

    dex_num = cols[0].text.strip().lstrip('#').zfill(4)

    name_tag = cols[1].find("a", class_="ent-name")
    is_primary = name_tag is not None

    all_forms.setdefault(dex_num, [])
    all_forms[dex_num].append((is_primary, cols))

# -------------------------
# 选择形态规则
# -------------------------
def pick_form(forms):
    for is_primary, cols in forms:
        if is_primary:
            return cols
    return forms[0][1]

# -------------------------
# 写入数据库
# -------------------------
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

sql = """
INSERT INTO pokemon_species (
    id, name_cn, type1, type2,
    base_hp, base_atk, base_def,
    base_sp_atk, base_sp_def, base_speed,
    gender_rate, rarity, sprite_url
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for dex_num, forms in all_forms.items():
    cols = pick_form(forms)

    img_tag = cols[0].find("img")
    sprite_url = img_tag["src"] if img_tag else ""

    # 清理 img，防止影响编号解析
    for img in cols[0].find_all("img"):
        img.decompose()

    name_en = cols[1].find("a", class_="ent-name").text.strip()
    name_cn = name_map.get(name_en, "")

    type_tags = cols[2].find_all("a")
    type1 = type_tags[0].text.strip()
    type2 = type_tags[1].text.strip() if len(type_tags) > 1 else None

    base_hp = int(cols[4].text.strip())
    base_atk = int(cols[5].text.strip())
    base_def = int(cols[6].text.strip())
    base_sp_atk = int(cols[7].text.strip())
    base_sp_def = int(cols[8].text.strip())
    base_speed = int(cols[9].text.strip())
    total = base_hp + base_atk + base_def + base_sp_atk + base_sp_def + base_speed

    rarity = calc_rarity(total)
    gender_rate = -1

    # -------------------------
    # 文件名 & 路径
    # -------------------------
    filename = f"{dex_num}.png"
    save_path = os.path.join(SPRITE_SAVE_DIR, filename)

    # 下载图片（磁盘用绝对路径）
    try:
        r = requests.get(sprite_url)
        if r.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(r.content)
    except Exception as e:
        print("[IMG ERROR]", dex_num, e)

    # ⚠️ 数据库里只存文件名！
    record = (
        dex_num, name_cn, type1, type2,
        base_hp, base_atk, base_def,
        base_sp_atk, base_sp_def, base_speed,
        gender_rate, rarity, filename
    )

    try:
        cursor.execute(sql, record)
        conn.commit()
        print("Inserted:", dex_num, name_en)
    except Exception as e:
        print("[DB ERROR]", dex_num, name_en, e)

cursor.close()
conn.close()

print("全部完成！")
