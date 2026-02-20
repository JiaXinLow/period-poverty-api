from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas import BasketItemCreate, BasketItemUpdate, BasketItemRead

router = APIRouter(prefix="/v1/basket-items", tags=["Basket Items"])

# Get DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CREATE (POST)
@router.post("/", response_model=BasketItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: BasketItemCreate, db: Session = Depends(get_db)):
    # Optional: enforce unique name
    existing = db.query(models.BasketItem).filter(models.BasketItem.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Item name already exists.")

    item = models.BasketItem(**payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# READ ALL (GET)
@router.get("/", response_model=list[BasketItemRead])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.BasketItem).all()

# READ ONE (GET)
@router.get("/{item_id}", response_model=BasketItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# UPDATE (PUT)
@router.put("/{item_id}", response_model=BasketItemRead)
def update_item(item_id: int, payload: BasketItemUpdate, db: Session = Depends(get_db)):
    item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item

# DELETE
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return None