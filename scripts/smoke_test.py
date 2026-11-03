"""端到端冒烟测试：按真实用户顺序把核心链路走一遍。

前置：先启动服务 `uvicorn backend.app.main:app --port 8000`，并完成建库播种。

用法（在项目根目录）：
    python -m scripts.smoke_test                       # 默认打本地 8000
    python -m scripts.smoke_test --base http://IP:PORT
"""

import argparse
import json
import random
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal

# Windows 控制台默认 GBK，中文用例名会直接抛 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ADMIN_USER = "admin"
ADMIN_PASS = "Admin@123456"

_results: list[tuple[str, bool, str]] = []


class ApiError(Exception):
    def __init__(self, status: int, body: dict) -> None:
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def call(base: str, method: str, path: str, *, token: str | None = None, payload: dict | None = None):
    url = base.rstrip("/") + path
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw) if raw else {}


def step(name: str, fn):
    try:
        value = fn()
        _results.append((name, True, str(value)[:110]))
        return value
    except AssertionError as exc:
        _results.append((name, False, f"断言失败：{exc}"))
        return None
    except Exception as exc:
        _results.append((name, False, f"{type(exc).__name__}: {exc}"))
        return None


def expect_ok(base, method, path, **kw):
    status, body = call(base, method, path, **kw)
    assert status == 200 or status == 201, f"{method} {path} -> HTTP {status} {body}"
    assert body.get("code") == 0, f"{method} {path} -> 业务码 {body.get('code')} {body.get('message')}"
    return body["data"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base

    print(f"目标服务：{base}\n")

    expect_ok(base, "GET", "/health")
    _results.append(("健康检查 /health", True, "服务与数据库均在线"))

    username = "buyer" + "".join(random.choices(string.ascii_lowercase + string.digits, k=7))
    password = "Test@123456"

    expect_ok(base, "POST", "/api/v1/auth/register", payload={
        "username": username, "password": password, "nickname": "冒烟买家", "phone": "13900000000"
    })
    token_data = expect_ok(base, "POST", "/api/v1/auth/login", payload={
        "username": username, "password": password
    })
    token = token_data["access_token"]
    _results.append(("注册 + 登录取令牌", True, f"用户 {username}，令牌有效期 {token_data['expires_in']} 秒"))

    me = expect_ok(base, "GET", "/api/v1/auth/me", token=token)
    assert me["username"] == username and me["role"] == "user"
    _results.append(("读取当前用户 /auth/me", True, f"{me['nickname']}（{me['role']}）"))

    bad = call(base, "POST", "/api/v1/auth/login", payload={"username": username, "password": "wrong-pass"})
    assert bad[0] == 401 and bad[1]["code"] == 40100
    _results.append(("错误密码被拒绝", True, f"HTTP {bad[0]} {bad[1]['message']}"))

    anon = call(base, "GET", "/api/v1/cart")
    assert anon[0] == 401
    _results.append(("未登录访问购物车被拒绝", True, f"HTTP {anon[0]} {anon[1]['message']}"))

    tree = expect_ok(base, "GET", "/api/v1/categories/tree")
    assert tree and tree[0]["children"], "分类树为空，请先执行 python -m scripts.init_db"
    _results.append(("分类树", True, f"{len(tree)} 个一级分类，首个为 {tree[0]['name']}"))

    page = expect_ok(base, "GET", "/api/v1/products?page=1&page_size=5")
    assert page["total"] > 0
    _results.append(("商品分页", True, f"共 {page['total']} 条 / {page['pages']} 页，本页 {len(page['items'])} 条"))

    cheap = expect_ok(base, "GET", "/api/v1/products?sort=price_asc&page_size=3")
    prices = [Decimal(str(i["price"])) for i in cheap["items"]]
    assert prices == sorted(prices)
    _results.append(("按价格升序", True, " -> ".join(str(p) for p in prices)))

    hit = expect_ok(base, "GET", "/api/v1/products?keyword=" + urllib.parse.quote("手机"))
    assert all("手机" in i["name"] or "手机" in i.get("subtitle", "") for i in hit["items"])
    _results.append(("关键词搜索", True, f"命中 {hit['total']} 条"))

    first = page["items"][0]
    detail = expect_ok(base, "GET", f"/api/v1/products/{first['id']}")
    _results.append(("商品详情", True, f"{detail['name']} 库存 {detail['stock']} {detail['unit']}"))

    stock_before = detail["stock"]
    expect_ok(base, "POST", "/api/v1/cart", token=token, payload={"product_id": first["id"], "quantity": 2})
    cart = expect_ok(base, "POST", "/api/v1/cart", token=token, payload={"product_id": first["id"], "quantity": 1})
    assert cart["items"][0]["quantity"] == 3, "重复加购应累加为 3"
    _results.append((
        "加购并累加数量", True,
        f"{cart['items'][0]['product_name']} × {cart['total_quantity']}，合计 {cart['total_amount']} 元",
    ))

    item_id = cart["items"][0]["id"]
    cart = expect_ok(base, "PUT", f"/api/v1/cart/{item_id}", token=token, payload={"quantity": 2})
    _results.append(("修改购物车数量", True, f"数量改为 2，合计 {cart['total_amount']} 元"))

    order = expect_ok(base, "POST", "/api/v1/orders", token=token, payload={
        "receiver_name": "冒烟收件人",
        "receiver_phone": "13900000000",
        "receiver_address": "北京市海淀区中关村大街 1 号",
        "remark": "冒烟测试订单",
    })
    _results.append((
        "购物车结算下单", True,
        f"订单号 {order['order_no']}，实付 {order['pay_amount']} 元（运费 {order['freight']}）",
    ))

    after = expect_ok(base, "GET", f"/api/v1/products/{first['id']}")
    assert after["stock"] == stock_before - 2, f"库存应减 2：{stock_before} -> {after['stock']}"
    _results.append(("下单后库存已扣减", True, f"{stock_before} -> {after['stock']}"))

    empty_cart = expect_ok(base, "GET", "/api/v1/cart", token=token)
    assert empty_cart["items"] == []
    _results.append(("下单后购物车已清空", True, "购物车为空"))

    paid = expect_ok(base, "PUT", f"/api/v1/orders/{order['id']}/payment", token=token)
    assert paid["status_label"] == "待发货"
    _results.append(("支付订单", True, f"状态 {paid['status']}（{paid['status_label']}）"))

    admin_token = expect_ok(base, "POST", "/api/v1/auth/login", payload={
        "username": ADMIN_USER, "password": ADMIN_PASS
    })["access_token"]
    shipped = expect_ok(base, "PUT", f"/api/v1/orders/{order['id']}/shipment", token=admin_token)
    assert shipped["status_label"] == "待收货", f"发货后应为待收货，实际 {shipped['status_label']}"
    received = expect_ok(base, "PUT", f"/api/v1/orders/{order['id']}/receipt", token=token)
    assert received["status_label"] == "已完成"
    _results.append(("管理员发货 -> 买家收货", True, f"最终状态 {received['status_label']}"))

    my_orders = expect_ok(base, "GET", "/api/v1/orders?page=1&page_size=10", token=token)
    assert my_orders["total"] >= 1
    _results.append(("我的订单列表", True, f"共 {my_orders['total']} 单"))

    # 再下一单用于验证取消回滚
    expect_ok(base, "POST", "/api/v1/cart", token=token, payload={"product_id": first["id"], "quantity": 3})
    order2 = expect_ok(base, "POST", "/api/v1/orders", token=token, payload={
        "receiver_name": "冒烟收件人",
        "receiver_phone": "13900000000",
        "receiver_address": "北京市海淀区中关村大街 1 号",
    })
    stock_mid = expect_ok(base, "GET", f"/api/v1/products/{first['id']}")["stock"]
    cancelled = expect_ok(base, "PUT", f"/api/v1/orders/{order2['id']}/cancellation", token=token)
    stock_after_cancel = expect_ok(base, "GET", f"/api/v1/products/{first['id']}")["stock"]
    assert stock_after_cancel == stock_mid + 3, "取消订单应回滚 3 件库存"
    _results.append((
        "取消订单回滚库存", True,
        f"{stock_mid} -> {stock_after_cancel}，状态 {cancelled['status_label']}",
    ))

    neg_status, neg_body = call(base, "PUT", f"/api/v1/orders/{order['id']}/cancellation", token=token)
    assert neg_status == 400 and "不能执行该操作" in neg_body["message"]
    _results.append(("已完成订单取消被拒绝", True, f"HTTP {neg_status} {neg_body['message']}"))

    neg_status, neg_body = call(base, "POST", "/api/v1/categories", token=token, payload={"name": "越权分类"})
    assert neg_status == 403 and neg_body["code"] == 40300
    _results.append(("普通用户建分类被拒绝", True, f"HTTP {neg_status} {neg_body['message']}"))

    new_cat = expect_ok(base, "POST", "/api/v1/categories", token=admin_token, payload={
        "name": "冒烟测试分类-" + "".join(random.choices(string.ascii_lowercase, k=6)), "sort_order": 99
    })
    new_prod = expect_ok(base, "POST", "/api/v1/products", token=admin_token, payload={
        "category_id": new_cat["id"],
        "name": "冒烟测试商品-" + "".join(random.choices(string.ascii_lowercase, k=6)),
        "price": "19.90",
        "stock": 7,
        "unit": "件",
    })
    _results.append(("管理员建分类 + 上架商品", True, f"分类 {new_cat['id']} / 商品 {new_prod['id']}"))

    expect_ok(base, "PUT", f"/api/v1/products/{new_prod['id']}", token=admin_token, payload={"status": 0})
    hidden = expect_ok(base, "GET", "/api/v1/products?keyword=" + urllib.parse.quote(new_prod["name"]))
    assert hidden["total"] == 0, "下架商品不应出现在公开列表"
    _results.append(("下架后公开列表查不到", True, f"{new_prod['name']} 已隐藏"))

    # 商品只能下架不能硬删，所以挂着商品的分类必须删不掉
    neg_status, neg_body = call(base, "DELETE", f"/api/v1/categories/{new_cat['id']}", token=admin_token)
    assert neg_status == 409 and "无法删除" in neg_body["message"]
    _results.append(("删除有商品的分类被拒绝", True, f"HTTP {neg_status} {neg_body['message']}"))

    empty_cat = expect_ok(base, "POST", "/api/v1/categories", token=admin_token, payload={
        "name": "冒烟空分类-" + "".join(random.choices(string.ascii_lowercase, k=6))
    })
    expect_ok(base, "DELETE", f"/api/v1/categories/{empty_cat['id']}", token=admin_token)
    gone = call(base, "GET", f"/api/v1/categories/{empty_cat['id']}")
    assert gone[0] == 404
    _results.append(("删除空分类并确认已不存在", True, f"分类 {empty_cat['id']} 已删除"))

    expect_ok(base, "DELETE", "/api/v1/cart", token=token)
    _results.append(("清空购物车", True, "OK"))

    width = max(len(name) for name, _, _ in _results)
    passed = 0
    for name, ok_, note in _results:
        flag = "PASS" if ok_ else "FAIL"
        passed += bool(ok_)
        print(f"[{flag}] {name.ljust(width)}  {note}")
    print(f"\n合计 {passed}/{len(_results)} 项通过")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
