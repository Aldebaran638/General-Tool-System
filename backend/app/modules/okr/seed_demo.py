"""
OKR 演示数据种子脚本（幂等）

用法：
    docker compose exec backend python -m app.modules.okr.seed_demo

幂等策略：
    部门按 name 查、用户按 email 查、Objective 按 title 查、
    KR 按 (objective_id, title) 查；已存在则跳过，可重复执行。
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.db import engine
from app.models_core import UserCreate
from app.modules.okr import crud as okr_crud
from app.modules.okr.models import Department, KeyResult, Objective
from app.modules.okr.schemas import (
    DepartmentCreate,
    KeyResultCreate,
    ObjectiveCreate,
)

DEMO_PASSWORD = "demo12345"

# (name, description)
DEPARTMENTS: list[tuple[str, str]] = [
    ("研发部", "负责产品核心研发与技术架构"),
    ("产品部", "负责产品规划与用户体验"),
    ("市场部", "负责品牌推广与市场拓展"),
]

# (full_name, email, department_name)
MEMBERS: list[tuple[str, str, str]] = [
    ("张伟", "zhangwei@example.com", "研发部"),
    ("李娜", "lina@example.com", "研发部"),
    ("王强", "wangqiang@example.com", "产品部"),
    ("刘洋", "liuyang@example.com", "产品部"),
    ("陈静", "chenjing@example.com", "市场部"),
    ("赵磊", "zhaolei@example.com", "市场部"),
]

# (title, description)
OBJECTIVES: list[tuple[str, str]] = [
    ("提升产品核心体验", "聚焦性能、易用性与稳定性，打造极致产品体验"),
    ("扩大市场影响力", "通过内容、活动与社群，持续扩大品牌声量"),
]

# (objective_title, title, assignee_email, start_offset_days, deadline_offset_days, progress)
# offset 相对今天：负数表示过去，正数表示未来
KEY_RESULTS: list[tuple[str, str, str, int, int, int]] = [
    # ---- Objective 1: 提升产品核心体验 ----
    # 明天到期 + 进度<100 → 命中"即将到期"
    ("提升产品核心体验", "完成核心页面性能优化，首屏加载时间降至 1.5s 内",
     "zhangwei@example.com", -21, 1, 85),
    # 已过期但进度 100 → 不应算超期
    ("提升产品核心体验", "上线新手引导流程，新用户激活率提升至 60%",
     "lina@example.com", -28, -3, 100),
    ("提升产品核心体验", "重构搜索模块，搜索成功率提升至 95%",
     "wangqiang@example.com", -14, 28, 50),
    ("提升产品核心体验", "完成移动端适配，核心页面覆盖率 90%",
     "liuyang@example.com", -7, 42, 25),
    # ---- Objective 2: 扩大市场影响力 ----
    ("扩大市场影响力", "举办 3 场行业线上研讨会，累计触达 2000 人",
     "chenjing@example.com", -21, 14, 70),
    ("扩大市场影响力", "官网自然流量提升 40%",
     "zhaolei@example.com", -7, 56, 0),
    # 昨天已过期 + 进度<100 → 命中"已超期"
    ("扩大市场影响力", "输出 12 篇行业白皮书与深度文章",
     "zhangwei@example.com", -14, -1, 25),
    ("扩大市场影响力", "搭建私域社群，成员规模达 5000 人",
     "chenjing@example.com", -14, 35, 50),
]


def seed_departments(session: Session) -> dict[str, uuid.UUID]:
    """创建部门，返回 {name: id}。已存在则跳过。"""
    created, skipped = 0, 0
    ids: dict[str, uuid.UUID] = {}
    for name, description in DEPARTMENTS:
        existing = session.exec(
            select(Department).where(Department.name == name)
        ).first()
        if existing:
            print(f"  [跳过] 部门已存在: {name}")
            ids[name] = existing.id
            skipped += 1
            continue
        dept = okr_crud.create_department(
            session=session,
            department_in=DepartmentCreate(name=name, description=description),
        )
        print(f"  [创建] 部门: {name} (sort_order={dept.sort_order})")
        ids[name] = dept.id
        created += 1
    print(f"部门: 创建 {created}，跳过 {skipped}")
    return ids


def seed_members(
    session: Session, department_ids: dict[str, uuid.UUID]
) -> dict[str, uuid.UUID]:
    """创建普通成员，返回 {email: id}。已存在则跳过。"""
    created, skipped = 0, 0
    ids: dict[str, uuid.UUID] = {}
    for full_name, email, dept_name in MEMBERS:
        existing = crud.get_user_by_email(session=session, email=email)
        if existing:
            print(f"  [跳过] 用户已存在: {full_name} <{email}>")
            ids[email] = existing.id
            skipped += 1
            continue
        user = crud.create_user(
            session=session,
            user_create=UserCreate(
                email=email,
                password=DEMO_PASSWORD,
                is_active=True,
                is_superuser=False,
                full_name=full_name,
                department_id=department_ids[dept_name],
            ),
        )
        print(f"  [创建] 用户: {full_name} <{email}> → {dept_name}")
        ids[email] = user.id
        created += 1
    print(f"成员: 创建 {created}，跳过 {skipped}")
    return ids


def seed_objectives(
    session: Session, admin_id: uuid.UUID
) -> dict[str, uuid.UUID]:
    """创建 Objective，返回 {title: id}。已存在则跳过。"""
    created, skipped = 0, 0
    ids: dict[str, uuid.UUID] = {}
    for title, description in OBJECTIVES:
        existing = session.exec(
            select(Objective).where(Objective.title == title)
        ).first()
        if existing:
            print(f"  [跳过] Objective 已存在: {title}")
            ids[title] = existing.id
            skipped += 1
            continue
        obj = okr_crud.create_objective(
            session=session,
            objective_in=ObjectiveCreate(title=title, description=description),
            created_by_id=admin_id,
        )
        print(f"  [创建] Objective: {title}")
        ids[title] = obj.id
        created += 1
    print(f"Objective: 创建 {created}，跳过 {skipped}")
    return ids


def seed_key_results(
    session: Session,
    objective_ids: dict[str, uuid.UUID],
    member_ids: dict[str, uuid.UUID],
) -> None:
    """创建 KR，按 (objective_id, title) 幂等。已存在则跳过。"""
    created, skipped = 0, 0
    today = date.today()
    for obj_title, title, email, start_off, ddl_off, progress in KEY_RESULTS:
        objective_id = objective_ids[obj_title]
        existing = session.exec(
            select(KeyResult).where(
                KeyResult.objective_id == objective_id,
                KeyResult.title == title,
            )
        ).first()
        if existing:
            print(f"  [跳过] KR 已存在: {title}")
            skipped += 1
            continue
        start_date = today + timedelta(days=start_off)
        deadline = today + timedelta(days=ddl_off)
        okr_crud.create_key_result(
            session=session,
            kr_in=KeyResultCreate(
                objective_id=objective_id,
                assignee_id=member_ids[email],
                title=title,
                start_date=start_date,
                deadline=deadline,
                progress=progress,
            ),
        )
        print(
            f"  [创建] KR: {title} "
            f"(负责人={email}, 进度={progress}%, {start_date} ~ {deadline})"
        )
        created += 1
    print(f"KR: 创建 {created}，跳过 {skipped}")


def main() -> None:
    print("=" * 60)
    print("OKR 演示数据种子脚本")
    print("=" * 60)
    with Session(engine) as session:
        admin = crud.get_user_by_email(
            session=session, email=settings.FIRST_SUPERUSER
        )
        if admin is None:
            raise RuntimeError(
                f"找不到超管用户 {settings.FIRST_SUPERUSER}，"
                "请先运行初始化（app.initial_data）"
            )
        print(f"超管: {admin.email}\n")

        print("[1/4] 部门")
        department_ids = seed_departments(session)

        print("\n[2/4] 普通成员")
        member_ids = seed_members(session, department_ids)

        print("\n[3/4] Objective")
        objective_ids = seed_objectives(session, admin.id)

        print("\n[4/4] KeyResult")
        seed_key_results(session, objective_ids, member_ids)

    print("\n" + "=" * 60)
    print("完成。演示成员账号（密码统一为: " + DEMO_PASSWORD + "）:")
    for full_name, email, dept_name in MEMBERS:
        print(f"  {full_name:<4} {email:<24} ({dept_name})")
    print("=" * 60)


if __name__ == "__main__":
    main()
