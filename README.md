# E-Business Platform · B2C 商城

**后端** FastAPI + SQLAlchemy 2.0 + MySQL 8.0，**前端** Vue 3 + Vite + Element Plus，
覆盖用户、商品分类、商品、购物车、订单五条核心业务链路。前端把 17 个接口全部做成了可点
的页面（买家端 7 页 + 管理后台 3 页）。

- 仓库地址：<https://github.com/6jbw6/E-Business-Platform>
- 功能设计文档（需求分析 / 功能图 / ER 图 / 接口设计）：[docs/功能设计文档.md](docs/功能设计文档.md)
- 接口文档（逐接口请求响应示例）：[docs/接口文档.md](docs/接口文档.md)
- 机器可读规范：[docs/openapi.json](docs/openapi.json)

## 特性

- **统一响应体**：`{"code": 0, "message": "success", "data": ...}`，前端只需判一个字段
- **JWT 鉴权 + 角色控制**：普通用户只能操作自己的购物车与订单；商品/分类写接口仅管理员可用
- **下单不超卖**：`SELECT ... FOR UPDATE` 按商品主键升序加行锁，扣库存与写订单同事务提交
- **订单价格快照**：明细表存下单瞬间的商品名与单价，事后改价不影响历史订单
- **状态机校验**：订单只能沿「待付款 → 待发货 → 待收货 → 已完成」流转，非法流转返回 400
- **端到端冒烟脚本**：一条命令跑完 32 项正向与负向用例，逐项打印 PASS/FAIL
- **Vue 3 前端**：买家端与管理员后台两套布局，路由守卫按角色分流，金额按字符串展示不做浮点运算

## 技术栈

| 组件 | 选型 | 用途 |
| --- | --- | --- |
| Web 框架 | FastAPI 0.115 | 路由、校验、OpenAPI 文档 |
| ASGI 服务器 | uvicorn 0.32 | 本地与公网部署 |
| ORM | SQLAlchemy 2.0 | 模型、事务、行锁 |
| 数据库驱动 | PyMySQL | MySQL 连接 |
| 数据校验 | Pydantic v2 | 请求/响应模型 |
| 配置 | pydantic-settings | `.env` 加载 |
| 鉴权 | PyJWT + bcrypt | 令牌签发与密码散列 |
| 前端框架 | Vue 3 + Vite 6 | 页面与构建 |
| 前端路由/状态 | vue-router 4 + Pinia 2 | 页面跳转与登录态、购物车 |
| UI 组件 | Element Plus 2.9 | 表格、表单、分页、消息提示 |
| HTTP 客户端 | axios | 统一注入令牌、拆响应信封 |

## 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py            # 应用入口，CORS、异常处理、/health
│   │   ├── api/
│   │   │   ├── router.py      # v1 路由汇总
│   │   │   └── v1/            # auth / categories / products / cart / orders
│   │   ├── core/              # config、security(JWT+bcrypt)、deps、exceptions
│   │   ├── crud/              # 各业务的数据访问与事务逻辑
│   │   ├── db/                # Base、engine/session、init_db 建库播种
│   │   ├── models/            # 6 张表的 ORM 模型
│   │   └── schemas/           # Pydantic 请求/响应模型
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── api/               # axios 实例与各业务请求封装
│   │   ├── stores/            # Pinia：登录态与购物车
│   │   ├── router/            # 路由表与 requiresAuth / requiresAdmin 守卫
│   │   ├── layouts/           # 买家端顶栏布局、管理后台侧栏布局
│   │   ├── views/             # 买家端 7 页 + admin/ 3 页
│   │   ├── components/        # ProductCard 等
│   │   └── utils/             # 金额与时间展示、富文本降级
│   ├── vite.config.js         # /api 与 /health 代理到 127.0.0.1:8000
│   └── package.json
├── docs/
│   ├── 功能设计文档.md         # 需求分析、功能图、ER 图、接口设计
│   ├── 接口文档.md             # 逐接口示例
│   └── openapi.json           # 由 scripts/export_openapi.py 生成
├── sql/
│   ├── 01_schema.sql          # 建库建表（由 ORM 反向生成）
│   └── 02_seed.sql            # 演示数据
├── scripts/
│   ├── init_db.py             # 建库 + 建表 + 播种
│   ├── smoke_test.py          # 端到端冒烟测试
│   ├── export_openapi.py      # 导出 OpenAPI 规范
│   ├── gen_schema_sql.py      # 重新生成 01_schema.sql
│   └── deploy_ubuntu.sh       # 公网服务器 uvicorn 部署
├── .env.example
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 准备环境

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

需要本机或远程有一个可用的 MySQL 8.0 实例。

### 2. 配置

```bash
cp .env.example .env      # Windows 用 copy .env.example .env
```

至少改这三项：`MYSQL_USER`、`MYSQL_PASSWORD`、`JWT_SECRET`（公网部署务必换成随机长串）。

### 3. 建库与演示数据

```bash
python -m scripts.init_db          # 建库 + 建表 + 播种，可重复执行
# 或走纯 SQL：
# mysql -u root -p < sql/01_schema.sql
# mysql -u root -p < sql/02_seed.sql
```

### 4. 启动

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

| 地址 | 说明 |
| --- | --- |
| <http://127.0.0.1:8000/docs> | Swagger UI，可在线调试 |
| <http://127.0.0.1:8000/health> | 健康检查（含数据库连通性） |

### 5. 验证

```bash
python -m scripts.smoke_test --base http://127.0.0.1:8000
```

### 6. 启动前端

后端跑起来后，另开一个终端：

```bash
cd frontend
npm install            # 国内可加 --registry=https://registry.npmmirror.com
npm run dev            # http://127.0.0.1:5173
```

`vite.config.js` 已把 `/api` 与 `/health` 代理到 `127.0.0.1:8000`，所以前端不用配跨域，
改后端端口时同步改 `VITE_PROXY_TARGET` 即可。生产构建 `npm run build` 产物在 `frontend/dist`。

> 提示：后端用 `--reload` 调试时请加 `--reload-dir backend`，否则 `npm install`、
> `npm run build` 改动 `frontend/` 里的文件会让后端反复重启，页面会短暂显示"后端未连接"。

### 前端页面清单

| 页面 | 路径 | 对应接口 |
| --- | --- | --- |
| 登录 / 注册 | `/login` | `POST /auth/login`、`POST /auth/register` |
| 商品首页 | `/` | `GET /categories/tree`、`GET /products` |
| 商品详情 | `/products/:id` | `GET /products/{id}` |
| 购物车 | `/cart` | `GET/POST/PUT/DELETE /cart` |
| 确认订单 | `/checkout` | `POST /orders`（结算勾选或直接购买） |
| 我的订单 | `/orders` | `GET /orders` |
| 订单详情 | `/orders/:id` | `GET /orders/{id}`、支付/收货/取消 |
| 个人资料 | `/profile` | `GET/PUT /auth/me` |
| 分类管理 | `/admin/categories` | 分类增删改（管理员） |
| 商品管理 | `/admin/products` | 商品发布/改价/上下架（管理员） |
| 订单发货 | `/admin/orders` | `GET /orders?all=true`、`PUT /orders/{id}/shipment` |

未登录访问购物车/订单会跳登录页并记住来源，登录后自动回跳；非管理员访问 `/admin/**`
会被送回首页。

### 演示账号

| 角色 | 登录名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `Admin@123456` |
| 普通用户 | `student01` | `Student@123` |

仅用于本地演示，公网部署前请删除或改密。

## 最小调用示例

```bash
# 登录拿令牌
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student01","password":"Student@123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")

# 加购 -> 下单
curl -s -X POST http://127.0.0.1:8000/api/v1/cart \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_id":101,"quantity":1}'

curl -s -X POST http://127.0.0.1:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"receiver_name":"张三","receiver_phone":"13900000001","receiver_address":"北京市海淀区中关村大街1号"}'
```

## 公网部署（uvicorn，不使用 docker 与 nginx）

```bash
# 服务器上，项目放在 /opt/ebusiness
cd /opt/ebusiness
cp .env.example .env && vi .env
bash scripts/deploy_ubuntu.sh 8000
```

脚本会装依赖、建库播种、后台拉起 uvicorn 并自检 `/health`。
云安全组需放行入方向 TCP `8000`；完成后访问 `http://<公网IP>:8000/docs`。

## 数据库表

| 表 | 中文名 | 说明 |
| --- | --- | --- |
| `users` | 用户表 | 账号、bcrypt 密码散列、角色与状态 |
| `categories` | 商品类别表 | 自关联两级分类 |
| `products` | 商品表 | 价格、库存、销量、上下架 |
| `cart_items` | 购物车表 | `(user_id, product_id)` 唯一 |
| `orders` | 订单主表 | 金额、收货信息、状态机 |
| `order_items` | 订单明细表 | 商品名称与价格快照 |

ER 图与字段说明见 [功能设计文档 · 第三章](docs/功能设计文档.md#三数据库设计与-er-图)。

## 已裁剪的功能

收货地址簿、真实支付对接、优惠券/满减/积分、售后退款与物流、商品评价、统计报表、
秒杀削峰、商品主图上传（商品图仍存 URL，只有用户头像做真实上传）。取舍理由逐条写在
[功能设计文档 · 需求池表格](docs/功能设计文档.md#12-需求池与取舍)。

## 许可

仅用于课程演示与学习交流。
