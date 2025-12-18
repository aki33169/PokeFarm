import pymysql

# ==================================================
# 数据库连接配置
# ==================================================
DB_ROOT = {
    "host": "127.0.0.1",
    "port": 4000,        # TiDB / (兼容MySQL)
    "user": "root",
    "password": "",
    "charset": "utf8mb4"
}

DB_NAME = "pokefarm"


def exec_sql(cursor, sql: str):
    """
    执行多条 SQL（按 ; 分割）
    """
    for stmt in sql.split(";"):
        if stmt.strip():
            cursor.execute(stmt)


def main():
    conn = pymysql.connect(**DB_ROOT, autocommit=True)
    cursor = conn.cursor()

    # ==================================================
    # 1. 创建数据库
    # ==================================================
    cursor.execute(f"""
    CREATE DATABASE IF NOT EXISTS {DB_NAME}
    DEFAULT CHARSET utf8mb4;
    """)
    cursor.execute(f"USE {DB_NAME}")

    # ==================================================
    # 2. 玩家相关表
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS player (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '玩家ID',
        username VARCHAR(32) UNIQUE NOT NULL COMMENT '用户名',
        password_hash VARCHAR(128) NOT NULL COMMENT '密码哈希',
        password_salt VARCHAR(64) NOT NULL COMMENT '密码盐',
        nickname VARCHAR(32) COMMENT '昵称',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        last_login_at DATETIME COMMENT '最后登录时间'
    );

    CREATE TABLE IF NOT EXISTS player_resource (
        player_id BIGINT PRIMARY KEY COMMENT '玩家ID',
        wood INT DEFAULT 0 COMMENT '木材',
        ore INT DEFAULT 0 COMMENT '矿石',
        herb INT DEFAULT 0 COMMENT '草药',
        berry INT DEFAULT 0 COMMENT '树果',
        gold INT DEFAULT 0 COMMENT '金币',
        food INT DEFAULT 0 COMMENT '食物',
        capacity_resource INT DEFAULT 1000 COMMENT '资源容量',
        capacity_pokemon INT DEFAULT 6 COMMENT '宝可梦容量',
        pokeball_normal INT DEFAULT 0 COMMENT '普通球',
        pokeball_super INT DEFAULT 0 COMMENT '超级球',
        pokeball_ultra INT DEFAULT 0 COMMENT '高级球',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
    );
    """)

    # ==================================================
    # 3. 宝可梦
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS pokemon_species (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '图鉴ID',
        name_cn VARCHAR(32) NOT NULL COMMENT '中文名',
        type1 VARCHAR(16) NOT NULL COMMENT '主属性',
        type2 VARCHAR(16) COMMENT '副属性',
        base_hp INT NOT NULL COMMENT '基础HP',
        base_atk INT NOT NULL COMMENT '基础攻击',
        base_def INT NOT NULL COMMENT '基础防御',
        base_sp_atk INT NOT NULL COMMENT '基础特攻',
        base_sp_def INT NOT NULL COMMENT '基础特防',
        base_speed INT NOT NULL COMMENT '基础速度',
        gender_rate TINYINT NOT NULL COMMENT '性别比',
        rarity TINYINT NOT NULL COMMENT '稀有度',
        sprite_url VARCHAR(255) COMMENT '精灵图片'
    );

    CREATE TABLE IF NOT EXISTS pokemon_instance (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '实例ID',
        player_id BIGINT NOT NULL COMMENT '玩家ID',
        species_id INT NOT NULL COMMENT '图鉴ID',
        nickname VARCHAR(32) COMMENT '昵称',
        level INT DEFAULT 1 COMMENT '等级',
        exp INT DEFAULT 0 COMMENT '经验',
        gender ENUM('M','F','N') NOT NULL COMMENT '性别',
        cur_hp INT DEFAULT 1 COMMENT '当前HP',
        fatigue INT DEFAULT 0 COMMENT '疲劳',
        rarity TINYINT NOT NULL COMMENT '稀有度',
        status ENUM('idle','working','resting') DEFAULT 'idle' COMMENT '状态',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '获得时间'
    );

    CREATE TABLE IF NOT EXISTS pokemon_level_exp (
        level INT PRIMARY KEY COMMENT '等级',
        exp_required INT NOT NULL COMMENT '升级所需经验'
    );
    """)

    # ==================================================
    # 4. 职业
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS job (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '职业ID',
        name VARCHAR(32) NOT NULL COMMENT '名称',
        code VARCHAR(32) UNIQUE NOT NULL COMMENT '代码',
        description VARCHAR(255) COMMENT '描述',
        base_efficiency FLOAT DEFAULT 1 COMMENT '基础效率',
        weight_hp FLOAT DEFAULT 0 COMMENT 'HP权重',
        weight_atk FLOAT DEFAULT 0 COMMENT '攻击权重',
        weight_def FLOAT DEFAULT 0 COMMENT '防御权重',
        weight_sp_atk FLOAT DEFAULT 0 COMMENT '特攻权重',
        weight_sp_def FLOAT DEFAULT 0 COMMENT '特防权重',
        weight_speed FLOAT DEFAULT 0 COMMENT '速度权重'
    );
    """)

    # ==================================================
    # 5. 建筑
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS building (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '建筑ID',
        name VARCHAR(32) NOT NULL COMMENT '名称',
        code VARCHAR(32) UNIQUE NOT NULL COMMENT '代码',
        description VARCHAR(255) COMMENT '描述',
        sprite_url VARCHAR(255) COMMENT '图片',
        building_type ENUM(
            'production','recovery','capacity','functional','decoration'
        ) NOT NULL COMMENT '类型',
        output_resource VARCHAR(32) COMMENT '产出资源',
        output_base INT DEFAULT 0 COMMENT '基础产出',
        base_slots INT DEFAULT 0 COMMENT '基础槽位',
        max_level INT DEFAULT 10 COMMENT '最大等级',
        unlock_level INT DEFAULT 1 COMMENT '解锁等级',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        job_id INT COMMENT '关联职业'
    );

    CREATE TABLE IF NOT EXISTS building_upgrade_cost (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
        building_code VARCHAR(32) NOT NULL COMMENT '建筑代码',
        level INT NOT NULL COMMENT '等级',
        cost_wood INT DEFAULT 0 COMMENT '木材',
        cost_ore INT DEFAULT 0 COMMENT '矿石',
        cost_herb INT DEFAULT 0 COMMENT '草药',
        cost_berry INT DEFAULT 0 COMMENT '树果',
        cost_gold INT DEFAULT 0 COMMENT '金币'
    );

    CREATE TABLE IF NOT EXISTS player_building (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '实例ID',
        player_id BIGINT NOT NULL COMMENT '玩家ID',
        building_id INT NOT NULL COMMENT '建筑ID',
        level INT DEFAULT 1 COMMENT '等级',
        pos_x INT DEFAULT 0 COMMENT 'X坐标',
        pos_y INT DEFAULT 0 COMMENT 'Y坐标',
        efficiency_bonus INT DEFAULT 0 COMMENT '效率加成',
        slot_bonus INT DEFAULT 0 COMMENT '槽位加成',
        storage_bonus INT DEFAULT 0 COMMENT '仓库加成',
        home_capacity_bonus INT DEFAULT 0 COMMENT '宿舍加成',
        upgraded_at DATETIME COMMENT '升级时间',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建造时间'
    );
    """)

    # ==================================================
    # 6. 派遣与产出
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS job_assignment (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '派遣ID',
        player_id BIGINT NOT NULL COMMENT '玩家ID',
        pokemon_id BIGINT NOT NULL COMMENT '宝可梦ID',
        building_id BIGINT NOT NULL COMMENT '建筑实例ID',
        job_id INT NOT NULL COMMENT '职业ID',
        start_time DATETIME NOT NULL COMMENT '开始时间',
        last_calc_time DATETIME NOT NULL COMMENT '上次结算',
        status ENUM('working','removed') DEFAULT 'working' COMMENT '状态',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
    );

    CREATE TABLE IF NOT EXISTS produce_log (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
        player_id BIGINT NOT NULL COMMENT '玩家ID',
        pokemon_id BIGINT NOT NULL COMMENT '宝可梦ID',
        building_id BIGINT NOT NULL COMMENT '建筑ID',
        job_id INT NOT NULL COMMENT '职业ID',
        resource_type VARCHAR(32) NOT NULL COMMENT '资源类型',
        amount INT NOT NULL COMMENT '数量',
        start_time DATETIME NOT NULL COMMENT '开始时间',
        end_time DATETIME NOT NULL COMMENT '结束时间',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间'
    );

    CREATE TABLE IF NOT EXISTS encounter_log (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '遭遇ID',
        player_id BIGINT NOT NULL COMMENT '玩家ID',
        species_id INT NOT NULL COMMENT '图鉴ID',
        pokemon_instance_id BIGINT COMMENT '捕获实例ID',
        encounter_time DATETIME NOT NULL COMMENT '遭遇时间',
        success TINYINT(1) NOT NULL COMMENT '是否成功',
        base_rate FLOAT NOT NULL COMMENT '基础概率',
        rarity_factor FLOAT NOT NULL COMMENT '稀有度修正',
        final_rate FLOAT NOT NULL COMMENT '最终概率',
        ball_type ENUM('normal','super','ultra') NOT NULL COMMENT '球类型'
    );
    """)

    # 初始化 job 数据
    cursor.execute("SELECT COUNT(*) FROM job")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO job
        (id,name,code,description,base_efficiency,
         weight_hp,weight_atk,weight_def,
         weight_sp_atk,weight_sp_def,weight_speed)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, [
            (1, "伐木", "lumber", "适合力量型宝可梦的伐木工作", 1,   1, 2, 2, 0.5, 0.5, 1),
            (30001, "采矿", "mining", "挖掘矿石的重体力劳动", 0.8, 2.2,1.8,1,1.4,0.6,1),
            (30002, "种植", "berry_farm", "照料树果作物", 0.6, 0.8,1.2,2,1.2,1.6,1),
            (30003, "采集", "herb_garden", "采集稀有草药", 0.6, 1,1,1.8,1.4,2.2,1),
            (30004, "经营", "shop", "管理商店赚取金币", 0.8, 0.8,2,0.8,2,0.8,1),
            (30005, "护理", "pokecenter", "恢复宝可梦体力", 2, 0.6,1.4,1.6,1.6,0.8,1),
        ])

    # ==================================================
    # 5. 建筑表
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS building (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '建筑ID',
        name VARCHAR(32) NOT NULL COMMENT '建筑名称',
        code VARCHAR(32) UNIQUE NOT NULL COMMENT '建筑代码',
        description VARCHAR(255) COMMENT '建筑描述',
        sprite_url VARCHAR(255) COMMENT '建筑图片',
        building_type ENUM(
            'production','recovery','capacity','functional','decoration'
        ) NOT NULL COMMENT '建筑类型',
        output_resource VARCHAR(32) COMMENT '产出资源类型',
        output_base INT DEFAULT 0 COMMENT '基础产出',
        base_slots INT DEFAULT 0 COMMENT '基础派遣槽位',
        max_level INT DEFAULT 10 COMMENT '最大等级',
        unlock_level INT DEFAULT 1 COMMENT '解锁等级',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        job_id INT COMMENT '对应职业ID'
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM building")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO building
        (id,name,code,description,sprite_url,building_type,
         output_resource,output_base,base_slots,max_level,unlock_level,job_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,10,1,%s)
        """, [
            (1,"伐木场","lumber_mill","能够产出木材的基础生产建筑。","lumber_mill.png","production","wood",5,1,1),
            (60001,"宿舍","home","增加可容纳宝可梦数量","home.png","capacity",None,0,0,None),
            (60002,"仓库","warehouse","增加资源储存上限","warehouse.png","capacity",None,0,0,None),
            (60003,"宝可梦中心","pokecenter","派遣宝可梦恢复HP","pokecenter.png","recovery",None,0,2,30005),
            (60004,"商店","shop","派遣宝可梦赚取金币","shop.png","production","gold",1,2,30004),
            (60005,"矿洞","mine","派遣宝可梦挖掘矿石","mine.png","production","ore",1,2,30001),
            (60006,"树果农场","berry_farm","种植并收获树果","berry_farm.png","production","berry",1,2,30002),
            (60007,"草药园","herb_garden","采集草药资源","herb_garden.png","production","herb",1,2,30003),
        ])

    # ==================================================
    # 6. 建筑升级消耗表（完整）
    # ==================================================
    exec_sql(cursor, """
    CREATE TABLE IF NOT EXISTS building_upgrade_cost (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
        building_code VARCHAR(32) NOT NULL COMMENT '建筑代码',
        level INT NOT NULL COMMENT '当前等级',
        cost_wood INT DEFAULT 0 COMMENT '木材消耗',
        cost_ore INT DEFAULT 0 COMMENT '矿石消耗',
        cost_herb INT DEFAULT 0 COMMENT '草药消耗',
        cost_berry INT DEFAULT 0 COMMENT '树果消耗',
        cost_gold INT DEFAULT 0 COMMENT '金币消耗'
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM building_upgrade_cost")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO building_upgrade_cost
        (building_code,level,cost_wood,cost_ore,cost_herb,cost_berry,cost_gold)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, [
            # lumber_mill
            ("lumber_mill",0,30,0,0,0,20),
            ("lumber_mill",1,60,0,0,0,40),
            ("lumber_mill",2,120,0,0,0,80),
            ("lumber_mill",3,220,0,0,0,150),

            # mine
            ("mine",0,10,30,0,0,60),
            ("mine",1,15,50,0,0,100),
            ("mine",2,20,80,0,0,160),
            ("mine",3,30,120,0,0,240),
            ("mine",4,40,180,0,0,360),

            # berry_farm
            ("berry_farm",0,15,0,0,20,40),
            ("berry_farm",1,25,0,0,35,70),
            ("berry_farm",2,40,0,0,60,120),
            ("berry_farm",3,60,0,0,90,180),
            ("berry_farm",4,90,0,0,140,260),

            # herb_garden
            ("herb_garden",0,10,0,15,0,40),
            ("herb_garden",1,18,0,30,0,70),
            ("herb_garden",2,30,0,50,0,120),
            ("herb_garden",3,45,0,80,0,180),
            ("herb_garden",4,70,0,120,0,260),

            # shop
            ("shop",0,30,10,0,0,120),
            ("shop",1,50,15,0,0,200),
            ("shop",2,80,25,0,0,350),
            ("shop",3,120,40,0,0,550),
            ("shop",4,180,60,0,0,800),

            # pokecenter
            ("pokecenter",0,40,10,20,0,150),
            ("pokecenter",1,60,15,30,0,250),
            ("pokecenter",2,90,25,45,0,400),
            ("pokecenter",3,140,40,70,0,650),
            ("pokecenter",4,200,60,100,0,1000),

            # home
            ("home",0,50,20,0,0,200),
            ("home",1,80,30,0,0,350),
            ("home",2,120,45,0,0,600),
            ("home",3,180,70,0,0,1000),
            ("home",4,260,100,0,0,1600),

            # warehouse
            ("warehouse",0,40,30,0,0,180),
            ("warehouse",1,70,50,0,0,300),
            ("warehouse",2,110,80,0,0,520),
            ("warehouse",3,160,120,0,0,850),
            ("warehouse",4,240,180,0,0,1400),
        ])

    cursor.close()
    conn.close()
    print("pokefarm 数据库初始化完成")


if __name__ == "__main__":
    main()
