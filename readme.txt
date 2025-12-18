---

POKEFARM —— 宝可梦农场模拟系统

==================================================
组员
张子繁 2023141490178
罗云腾 2024141480038
==================================================

1. 项目简介

PokeFarm 是一个基于 Web 的宝可梦主题模拟经营系统。
玩家可以在系统中完成宝可梦捕捉、农场建设、宝可梦派遣以及资源生产等操作，体验一个持续运行、状态可积累的农场世界。

本项目以数据库系统设计与前后端分离架构实践为主要目标，重点关注以下内容：

1. 关系型数据库的合理建模
2. 模板表与实例表的区分设计
3. 多实体协作下的数据一致性
4. 定时任务驱动的生产系统
5. 实际可运行的完整 Web 项目

---

2. 项目整体结构说明

项目整体采用前后端分离架构，目录结构如下：

POKEFARM
├─ backend/                后端（FastAPI）
│  ├─ routers/             功能模块路由
│  ├─ utils/               工具函数
│  ├─ db.py                数据库连接封装
│  ├─ main.py              后端入口
│  ├─ scheduler.py         定时产出调度器
│  └─ .env                 数据库配置
│
├─ frontend/
│  └─ pokefarm_front/      前端（Vue3 + Vite）
│     ├─ src/
│     │  ├─ api/           API 请求封装
│     │  ├─ assets/        宝可梦精灵与素材（1025 只）
│     │  ├─ components/    组件
│     │  ├─ router/        路由配置
│     │  └─ views/         页面视图
│     ├─ App.vue
│     ├─ main.js
│     ├─ vite.config.js
│     └─ index.html
│
├─ scripts/                数据初始化与爬虫脚本
│  ├─ init_database.py     数据库建库建表脚本
│  ├─ PokemonDataGet.py    宝可梦图鉴数据爬虫
│  └─ pokedex_national_simple.json
│
└─ README.txt

---

3. 技术栈说明

3.1 前端部分

1. 框架：Vue 3
2. 构建工具：Vite
3. 技术特点：

   1. 单页面应用（SPA）
   2. 组件化 UI 设计
   3. 基于 REST API 与后端通信

3.2 后端部分

1. 框架：FastAPI
2. 数据库：TiDB (兼容MySQL协议)
3. 定时调度：APScheduler
4. 技术特点：

   1. 路由模块化拆分
   2. 明确区分业务逻辑与数据访问
   3. 定时任务驱动核心业务逻辑

---

4. 数据库设计说明

4.1 数据库初始化脚本

数据库的建库与建表操作统一放在 scripts/init_database.py 中。
该脚本主要完成以下工作：

1. 创建数据库 pokefarm
2. 创建项目所需的全部数据表
3. 建立必要的主键与外键关系

执行方式如下：

cd scripts
python init_database.py

---

4.2 宝可梦图鉴数据规模说明

本项目的宝可梦图鉴数据覆盖 **当前全国图鉴全部 1025 只宝可梦**，
不包含抽样、不做简化，也未使用虚拟数据。

具体说明如下：

1. 覆盖全国编号 0001 – 1025 的全部宝可梦
2. 每只宝可梦均包含：

   1. 全国编号
   2. 中文名称
   3. 属性信息
   4. 基础种族值
   5. 稀有度参数
   6. 精灵图片资源
3. 图鉴数据以 pokemon_species 表的形式完整存储

---

4.3 核心数据表设计

4.3.1 玩家相关表

1. player：玩家账号信息
2. player_resource：玩家资源、容量与道具信息

4.3.2 宝可梦系统

1. pokemon_species：宝可梦图鉴表（1025 只完整数据）
2. pokemon_instance：玩家持有的宝可梦实例

该设计将宝可梦的基础图鉴数据与玩家实例数据分离，
避免数据冗余，并支持多个玩家同时持有同一宝可梦种类。

4.3.3 建筑与派遣系统

1. building：建筑模板表
2. player_building：玩家建筑实例
3. job：岗位定义表
4. job_assignment：宝可梦派遣关系表

4.3.4 产出系统

1. produce_log：资源产出日志表

---

5. 核心功能机制说明

5.1 宝可梦捕捉系统

后端随机生成遭遇宝可梦，候选宝可梦来源于完整的 1025 只全国图鉴。
每只宝可梦均具有稀有度参数，捕捉成功率由以下因素共同决定：

1. 宝可梦稀有度
2. 精灵球类型
3. 基础概率公式

捕捉成功后，在 pokemon_instance 表中生成对应记录。

---

5.2 建筑与派遣系统

1. 建筑决定可派遣的岗位类型与产出资源
2. 宝可梦派遣后进入 working 状态
3. 实际产出效率由以下因素综合计算：

   1. 宝可梦等级
   2. 宝可梦基础种族值
   3. 岗位权重参数
   4. 建筑效率加成

---

5.3 自动产出与定时任务

1. 系统使用 APScheduler 实现定时产出结算
2. 调度器每 5 秒执行一次产出计算
3. 通过 last_calc_time 精确计算时间差
4. 支持碎片化产出累计，避免精度损失

---

6. 爬虫脚本说明（数据来源）

6.1 爬虫脚本位置

爬虫与数据初始化脚本统一放在 scripts 目录下：

1. PokemonDataGet.py
2. pokedex_national_simple.json

---

6.2 爬虫功能说明

PokemonDataGet.py 用于从公开宝可梦数据库网站抓取以下信息：

1. 全国编号
2. 宝可梦中文名称
3. 属性信息
4. 基础种族值
5. 精灵图片资源

脚本在抓取完成后：

1. 自动计算宝可梦稀有度
2. 将 1025 只宝可梦数据写入 pokemon_species 表
3. 下载对应精灵图片至前端资源目录

---

6.3 项目提交说明

1. 本项目提交时，图片资源库中已包含完整的 1025 只宝可梦图鉴数据
2. 项目运行与评测过程中需要再次执行爬虫脚本和init_database.py填充数据库
3. 爬虫脚本仅用于说明数据来源与数据初始化过程
4：重要！！！！必须执行Pokemondataget.py后数据库内才会包含宝可梦数据！！！！

---

7. 项目部署与运行说明

7.1 环境要求

1. Python 3.9 及以上
2. Node.js 16 及以上
3. TiDB 数据库 （兼容MySQL）

---

7.2 后端依赖库安装说明

后端依赖的 Python 库主要包括 Web 框架、数据库驱动、调度器以及爬虫相关库。

建议在 backend 目录下使用虚拟环境安装依赖。

1. 创建并激活虚拟环境（可选）

Windows：
python -m venv venv
venv\Scripts\activate

Linux / macOS：
python3 -m venv venv
source venv/bin/activate

---

2. 安装后端依赖库

进入 backend 目录后，执行以下命令：

pip install fastapi
pip install uvicorn
pip install pymysql
pip install python-dotenv
pip install apscheduler

---

3. 爬虫脚本相关依赖

爬虫脚本位于 scripts 目录，其运行依赖以下库：

pip install requests
pip install beautifulsoup4

说明如下：

1. requests：用于发送 HTTP 请求
2. beautifulsoup4：用于解析网页结构
3. pymysql：用于将爬取的数据写入数据库

课程项目提交与运行过程中不需要再次执行爬虫脚本，
此处仅用于说明项目数据的获取方式与技术实现。

---

7.3 后端启动步骤

1. 进入 backend 目录
2. 配置 .env 文件

DB_HOST=127.0.0.1
DB_PORT=4000
DB_USER=root
DB_PASSWORD=
DB_NAME=pokefarm

3. 启动后端服务

uvicorn main:app --reload

---

7.4 前端依赖库安装说明

前端依赖统一由 npm 管理，已在 package.json 中定义。

进入前端目录：

cd frontend/pokefarm_front

安装依赖：

npm install

该命令将自动安装以下核心依赖（包括但不限于）：

1. vue
2. vue-router
3. axios
4. vite

---

7.5 前端启动步骤

启动前端开发服务器：

npm run dev

浏览器访问地址：

[http://localhost:5173]

---

8. 项目总结

PokeFarm 项目完整实现了一个基于宝可梦的农场模拟经营系统。

项目在以下方面具有较强实践价值：

1. 完整的关系型数据库建模
2. 前后端分离架构的工程实现
3. 定时任务驱动的持续生产机制
4. 实际可运行、可扩展的系统设计

==================================================

