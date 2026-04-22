import uuid

from sqlmodel import Session, func, select

from app.models import Item

from .schemas import ItemCreate, ItemUpdate


def count_items(session: Session, *, owner_id: uuid.UUID | None = None) -> int:
    statement = select(func.count()).select_from(Item)
    if owner_id is not None:
        statement = statement.where(Item.owner_id == owner_id)
    return session.exec(statement).one()


def list_items(
    session: Session,
    *,
    skip: int,
    limit: int,
    owner_id: uuid.UUID | None = None,
) -> list[Item]:
    statement = select(Item)
    if owner_id is not None:
        statement = statement.where(Item.owner_id == owner_id)
    statement = statement.order_by(Item.created_at.desc()).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_item(session: Session, *, item_id: uuid.UUID) -> Item | None:
    return session.get(Item, item_id)


def create_item(session: Session, *, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_item(session: Session, *, item: Item, item_in: ItemUpdate) -> Item:
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, *, item: Item) -> None:
    session.delete(item)
    session.commit()