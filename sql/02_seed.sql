-- ---------------------------------------------------------------------------
-- B2C 商城 · 演示数据脚本（可重复执行，已存在的行自动跳过）
-- 执行：mysql -u root -p < sql/02_seed.sql
-- 等价做法：python -m scripts.init_db（由后端代码幂等播种）
--
-- 账号说明（密码均为 bcrypt 散列，明文只写在这里供演示登录）：
--   管理员  admin      / Admin@123456
--   普通用户 student01 / Student@123
-- ---------------------------------------------------------------------------

USE `ebusiness_mall`;

SET NAMES utf8mb4;

-- 用户表 --------------------------------------------------------------
INSERT IGNORE INTO `users`
    (`id`, `username`, `password_hash`, `nickname`, `phone`, `email`, `avatar`, `role`, `status`)
VALUES
    (1, 'admin', '$2b$10$udltE22GvzOQw7rIEs.9Futc1gB3FhhDMHuEapfXbww8ILH9UW./u',
     '平台管理员', '13800000000', 'admin@example.com', '', 'admin', 1),
    (2, 'student01', '$2b$10$9ZPrqaj6BhVF./pcYXnnROaU5HMP44msUoxYMCwadBINtnnUnR3Ju',
     '演示买家', '13800001111', 'student01@example.com', '', 'user', 1);

-- 商品类别表（一级 1-3，二级 11-32） ----------------------------------
INSERT IGNORE INTO `categories`
    (`id`, `name`, `parent_id`, `level`, `icon`, `sort_order`, `status`)
VALUES
    (1,  '手机数码', NULL, 1, '/static/cat/digital.png', 1, 1),
    (2,  '家用电器', NULL, 1, '/static/cat/appliance.png', 2, 1),
    (3,  '服饰鞋包', NULL, 1, '/static/cat/clothing.png', 3, 1),
    (11, '智能手机', 1, 2, '', 1, 1),
    (12, '笔记本电脑', 1, 2, '', 2, 1),
    (13, '智能穿戴', 1, 2, '', 3, 1),
    (21, '厨房电器', 2, 2, '', 1, 1),
    (22, '生活电器', 2, 2, '', 2, 1),
    (31, '男装', 3, 2, '', 1, 1),
    (32, '女鞋', 3, 2, '', 2, 1);

-- 商品表 --------------------------------------------------------------
-- 5 号商品库存为 0，用于演示「库存不足」分支
INSERT IGNORE INTO `products`
    (`id`, `category_id`, `name`, `subtitle`, `main_image`, `price`, `original_price`,
     `stock`, `sales`, `unit`, `detail`, `status`)
VALUES
    (101, 11, '星海 12 Pro 5G 手机', '智能手机·热销款', '/static/goods/0001.jpg',
     3999.00, 4199.00, 120, 36, '台', '<p>6.7 英寸直屏，5000mAh 电池。</p>', 1),
    (102, 11, '轻氧 Air 折叠屏手机', '智能手机·热销款', '/static/goods/0002.jpg',
     6899.00, 7099.00, 30, 12, '台', '<p>折叠形态，2 英寸外屏。</p>', 1),
    (103, 12, '木鱼 Book 14 轻薄本', '笔记本电脑·热销款', '/static/goods/0003.jpg',
     5299.00, 5499.00, 45, 20, '台', '<p>1.2kg 机身，14 小时续航。</p>', 1),
    (104, 13, '潮汐 Watch 运动手表', '智能穿戴·热销款', '/static/goods/0004.jpg',
     899.00, 1099.00, 200, 40, '只', '<p>双频 GPS，14 天续航。</p>', 1),
    (105, 13, '云感 降噪耳机', '智能穿戴·热销款', '/static/goods/0005.jpg',
     499.00, 599.00, 0, 8, '副', '<p>主动降噪，单次 8 小时。</p>', 1),
    (106, 21, '山泉 破壁料理机', '厨房电器·热销款', '/static/goods/0006.jpg',
     1299.00, 1499.00, 60, 15, '台', '<p>38000 转/分钟破壁。</p>', 1),
    (107, 22, '暖阳 变频空调', '生活电器·热销款', '/static/goods/0007.jpg',
     2799.00, 2999.00, 18, 6, '台', '<p>新一级能效，1.5 匹。</p>', 1),
    (108, 31, '简白 纯棉短袖 T 恤', '男装·热销款', '/static/goods/0008.jpg',
     89.00, 129.00, 500, 48, '件', '<p>220g 重磅纯棉。</p>', 1),
    (109, 32, '踏云 轻便跑步鞋', '女鞋·热销款', '/static/goods/0009.jpg',
     329.00, 399.00, 150, 22, '双', '<p>回弹中底，单只 210g。</p>', 1);

-- 校验：三张表各自的行数
SELECT '用户' AS 表, COUNT(*) AS 行数 FROM `users`
UNION ALL SELECT '分类', COUNT(*) FROM `categories`
UNION ALL SELECT '商品', COUNT(*) FROM `products`;
