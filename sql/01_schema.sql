-- ---------------------------------------------------------------------------
-- B2C 商城 · 数据库建表脚本
-- 生成方式：python -m scripts.gen_schema_sql（由 ORM 模型反向生成，勿手工改动）
-- 目标库：MySQL 8.0 / InnoDB / utf8mb4
-- 执行：mysql -u root -p < sql/01_schema.sql
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `ebusiness_mall`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE `ebusiness_mall`;


CREATE TABLE categories (
	id INTEGER NOT NULL COMMENT '类别ID' AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL COMMENT '类别名称', 
	parent_id INTEGER COMMENT '父类别ID，顶级为空', 
	level SMALLINT NOT NULL COMMENT '层级：1=一级分类，2=二级分类', 
	icon VARCHAR(255) NOT NULL COMMENT '类别图标', 
	sort_order INTEGER NOT NULL COMMENT '同级排序，越小越靠前', 
	status SMALLINT NOT NULL COMMENT '状态：1=显示，0=隐藏', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME NOT NULL COMMENT '更新时间，由数据库自动维护' DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE CASCADE
)CHARSET=utf8mb4 COMMENT='商品类别表：支持一级/二级分类的自关联树';

CREATE INDEX idx_categories_parent ON categories (parent_id);

CREATE TABLE users (
	id INTEGER NOT NULL COMMENT '用户ID' AUTO_INCREMENT, 
	username VARCHAR(32) NOT NULL COMMENT '登录名，唯一', 
	password_hash VARCHAR(128) NOT NULL COMMENT 'bcrypt 密码散列，不保存明文', 
	nickname VARCHAR(32) NOT NULL COMMENT '昵称', 
	phone VARCHAR(20) COMMENT '手机号', 
	email VARCHAR(128) COMMENT '邮箱', 
	avatar VARCHAR(255) NOT NULL COMMENT '头像地址', 
	`role` VARCHAR(16) NOT NULL COMMENT '角色：user=普通用户，admin=管理员', 
	status SMALLINT NOT NULL COMMENT '状态：1=正常，0=禁用', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME NOT NULL COMMENT '更新时间，由数据库自动维护' DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (id)
)CHARSET=utf8mb4 COMMENT='用户表：账号、密码散列与基础资料';

CREATE INDEX idx_users_phone ON users (phone);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE orders (
	id INTEGER NOT NULL COMMENT '订单ID' AUTO_INCREMENT, 
	order_no VARCHAR(24) NOT NULL COMMENT '订单号，对外展示用', 
	user_id INTEGER NOT NULL COMMENT '下单用户ID', 
	total_amount NUMERIC(12, 2) NOT NULL COMMENT '商品总额（元）', 
	freight NUMERIC(10, 2) NOT NULL COMMENT '运费（元）', 
	pay_amount NUMERIC(12, 2) NOT NULL COMMENT '实付金额=商品总额+运费', 
	status SMALLINT NOT NULL COMMENT '状态：0待付款 1待发货 2待收货 3已完成 4已取消', 
	receiver_name VARCHAR(32) NOT NULL COMMENT '收货人', 
	receiver_phone VARCHAR(20) NOT NULL COMMENT '收货电话', 
	receiver_address VARCHAR(255) NOT NULL COMMENT '收货地址', 
	remark VARCHAR(255) NOT NULL COMMENT '买家备注', 
	paid_at DATETIME COMMENT '支付时间', 
	shipped_at DATETIME COMMENT '发货时间', 
	finished_at DATETIME COMMENT '完成时间', 
	cancelled_at DATETIME COMMENT '取消时间', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME NOT NULL COMMENT '更新时间，由数据库自动维护' DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (order_no), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 COMMENT='订单主表：收货信息、金额与状态';

CREATE INDEX idx_orders_user_status ON orders (user_id, status);

CREATE TABLE products (
	id INTEGER NOT NULL COMMENT '商品ID' AUTO_INCREMENT, 
	category_id INTEGER NOT NULL COMMENT '所属类别ID', 
	name VARCHAR(120) NOT NULL COMMENT '商品名称', 
	subtitle VARCHAR(200) NOT NULL COMMENT '副标题/卖点', 
	main_image VARCHAR(255) NOT NULL COMMENT '主图地址', 
	price NUMERIC(10, 2) NOT NULL COMMENT '售价（元）', 
	original_price NUMERIC(10, 2) NOT NULL COMMENT '划线价（元）', 
	stock INTEGER NOT NULL COMMENT '可售库存', 
	sales INTEGER NOT NULL COMMENT '累计销量', 
	unit VARCHAR(16) NOT NULL COMMENT '计量单位', 
	detail TEXT COMMENT '图文详情', 
	status SMALLINT NOT NULL COMMENT '状态：1=在售，0=下架', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME NOT NULL COMMENT '更新时间，由数据库自动维护' DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 COMMENT='商品表：价格、库存与上下架状态';

CREATE INDEX idx_products_category ON products (category_id);

CREATE INDEX idx_products_status ON products (status);

CREATE TABLE cart_items (
	id INTEGER NOT NULL COMMENT '购物车行ID' AUTO_INCREMENT, 
	user_id INTEGER NOT NULL COMMENT '用户ID', 
	product_id INTEGER NOT NULL COMMENT '商品ID', 
	quantity INTEGER NOT NULL COMMENT '数量', 
	checked SMALLINT NOT NULL COMMENT '是否勾选结算：1=勾选，0=未勾选', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME NOT NULL COMMENT '更新时间，由数据库自动维护' DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	CONSTRAINT uk_cart_user_product UNIQUE (user_id, product_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 COMMENT='购物车表：同一用户同一商品只保留一条，重复加购累加数量';

CREATE TABLE order_items (
	id INTEGER NOT NULL COMMENT '明细ID' AUTO_INCREMENT, 
	order_id INTEGER NOT NULL COMMENT '订单ID', 
	product_id INTEGER NOT NULL COMMENT '商品ID', 
	product_name VARCHAR(120) NOT NULL COMMENT '商品名称快照', 
	product_image VARCHAR(255) NOT NULL COMMENT '商品主图快照', 
	price NUMERIC(10, 2) NOT NULL COMMENT '成交单价快照', 
	quantity INTEGER NOT NULL COMMENT '购买数量', 
	subtotal NUMERIC(12, 2) NOT NULL COMMENT '小计金额', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME NOT NULL COMMENT '更新时间，由数据库自动维护' DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)CHARSET=utf8mb4 COMMENT='订单明细表：下单时快照商品名称与价格，不受后续改价影响';

CREATE INDEX idx_order_items_order ON order_items (order_id);

SET FOREIGN_KEY_CHECKS = 1;
