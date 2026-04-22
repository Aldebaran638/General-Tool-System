import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.models import Item, User

from . import repository
from .schemas import ItemCreate, ItemsPublic, ItemUpdate, Message


def read_items(
    session: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> ItemsPublic:
    owner_id = None if current_user.is_superuser else current_user.id
    count = repository.count_items(session, owner_id=owner_id)
    items = repository.list_items(
        session,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
    )
    return ItemsPublic(data=items, count=count)


def read_item(session: Session, *, current_user: User, item_id: uuid.UUID) -> Item:
    item = repository.get_item(session, item_id=item_id)
    return _require_item_access(item=item, current_user=current_user)


def create_item(session: Session, *, current_user: User, item_in: ItemCreate) -> Item:
    return repository.create_item(session, item_in=item_in, owner_id=current_user.id)


def update_item(
    session: Session,
    *,
    current_user: User,
    item_id: uuid.UUID,
    item_in: ItemUpdate,
) -> Item:
    item = repository.get_item(session, item_id=item_id)
    item = _require_item_access(item=item, current_user=current_user)
    return repository.update_item(session, item=item, item_in=item_in)


def delete_item(
    session: Session,
    *,
    current_user: User,
    item_id: uuid.UUID,
) -> Message:
    item = repository.get_item(session, item_id=item_id)
    item = _require_item_access(item=item, current_user=current_user)
    repository.delete_item(session, item=item)
    return Message(message="Item deleted successfully")


def _require_item_access(*, item: Item | None, current_user: User) -> Item:
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item