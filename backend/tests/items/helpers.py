"""
backend/tests/items/helpers.py
items 测试辅助函数
"""

from sqlmodel import Session

from app import crud
from app.models import Item, ItemCreate
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_item(db: Session) -> Item:
    """创建一个随机 item，自动生成 owner"""
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None
    title = random_lower_string()
    description = random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    return crud.create_item(session=db, item_in=item_in, owner_id=owner_id)


def create_item_for_user(db: Session, owner_id, title: str | None = None, description: str | None = None) -> Item:
    """为指定 owner 创建一个 item"""
    title = title or random_lower_string()
    description = description or random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    return crud.create_item(session=db, item_in=item_in, owner_id=owner_id)
