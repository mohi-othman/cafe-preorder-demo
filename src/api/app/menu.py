from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Cafe, Category, Product

router = APIRouter(prefix="/api")


class CafeOut(BaseModel):
    slug: str
    name_ar: str
    name_en: str


class ProductOut(BaseModel):
    id: int
    name_ar: str
    name_en: str
    description_ar: str | None
    description_en: str | None
    price: int
    image_url: str | None


class CategoryOut(BaseModel):
    id: int
    name_ar: str
    name_en: str
    products: list[ProductOut]


class MenuOut(BaseModel):
    cafe: CafeOut
    categories: list[CategoryOut]


@router.get("/cafes/{slug}/menu", response_model=MenuOut)
def get_menu(slug: str, session: Session = Depends(get_session)):
    cafe = session.exec(select(Cafe).where(Cafe.slug == slug)).first()
    if cafe is None:
        raise HTTPException(status_code=404, detail="Café not found")
    categories = session.exec(
        select(Category).where(Category.cafe_id == cafe.id).order_by(Category.position, Category.id)
    ).all()
    products = session.exec(
        select(Product)
        .where(Product.cafe_id == cafe.id, Product.available)
        .order_by(Product.position, Product.id)
    ).all()
    return MenuOut(
        cafe=CafeOut.model_validate(cafe, from_attributes=True),
        categories=[
            CategoryOut(
                id=c.id,
                name_ar=c.name_ar,
                name_en=c.name_en,
                products=[
                    ProductOut.model_validate(p, from_attributes=True)
                    for p in products
                    if p.category_id == c.id
                ],
            )
            for c in categories
        ],
    )
