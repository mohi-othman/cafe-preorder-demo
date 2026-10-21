"""Super Admin API: Cafés and Menu editing. Every route needs the admin role.

Prices come in as SAR text (`price_sar`, e.g. "18.50") and are stored as halalas (`price`); responses carry both.
Deleting is strict: a Category that still has Products, or a Product that is on an Order, answers 409
(mark the Product unavailable instead), so past Orders keep their lines.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import AfterValidator, BaseModel, BeforeValidator, StringConstraints
from sqlalchemy import func
from sqlmodel import Session, select

from app.auth import BARISTA, MAX_PASSWORD_BYTES, hash_password, require_admin
from app.db import get_session
from app.menu import CafeOut
from app.models import Cafe, Category, OrderLine, Product, User
from app.money import halalas_to_sar, sar_to_halalas

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


def _strip_or_none(v):
    return (v.strip() or None) if isinstance(v, str) else v


def _parse_sar(v):
    if not isinstance(v, str):  # numbers would bring float rounding with them
        raise ValueError('price_sar must be text, e.g. "18.50"')
    return sar_to_halalas(v)


def _fits_bcrypt(v: str) -> str:
    if len(v.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(f"password must be at most {MAX_PASSWORD_BYTES} bytes in UTF-8")
    return v


RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]
OptionalText = Annotated[str | None, BeforeValidator(_strip_or_none)]
Halalas = Annotated[int, BeforeValidator(_parse_sar)]  # from SAR text
# The Café's part of /c/<slug>: lowercase letters and digits, words joined by single hyphens.
Slug = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
MIN_PASSWORD_LENGTH = 8


class AdminCafeOut(BaseModel):
    id: int
    slug: str
    name_ar: str
    name_en: str


class CafeIn(BaseModel):
    name_ar: RequiredText
    name_en: Text = ""
    slug: Slug
    barista_username: RequiredText
    barista_password: Annotated[str, StringConstraints(min_length=MIN_PASSWORD_LENGTH), AfterValidator(_fits_bcrypt)]


class AdminCategoryOut(BaseModel):
    id: int
    name_ar: str
    name_en: str
    position: int


class AdminProductOut(BaseModel):
    id: int
    category_id: int
    name_ar: str
    name_en: str
    description_ar: str | None
    description_en: str | None
    price: int  # halalas
    price_sar: str  # "18.50"
    available: bool
    image_url: str | None
    position: int


class AdminMenuOut(BaseModel):
    cafe: CafeOut
    categories: list[AdminCategoryOut]
    products: list[AdminProductOut]  # all of them, unavailable ones too


# Patch models: fields left out are not changed. Non-optional types reject an explicit null.
class CategoryIn(BaseModel):
    name_ar: RequiredText
    name_en: Text = ""


class CategoryPatch(BaseModel):
    name_ar: RequiredText = ""
    name_en: Text = ""
    position: int = 0


class ProductIn(BaseModel):
    category_id: int
    name_ar: RequiredText
    name_en: Text = ""
    description_ar: OptionalText = None
    description_en: OptionalText = None
    price_sar: Halalas
    available: bool = True
    image_url: OptionalText = None


class ProductPatch(BaseModel):
    category_id: int = 0
    name_ar: RequiredText = ""
    name_en: Text = ""
    description_ar: OptionalText = None
    description_en: OptionalText = None
    price_sar: Halalas = 0
    available: bool = True
    image_url: OptionalText = None


def _cafe_or_404(session: Session, cafe_id: int) -> Cafe:
    cafe = session.get(Cafe, cafe_id)
    if cafe is None:
        raise HTTPException(status_code=404, detail="Café not found")
    return cafe


def _category_or_404(session: Session, cafe_id: int, category_id: int) -> Category:
    cat = session.get(Category, category_id)
    if cat is None or cat.cafe_id != cafe_id:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


def _product_or_404(session: Session, cafe_id: int, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if product is None or product.cafe_id != cafe_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _check_category(session: Session, cafe_id: int, category_id: int) -> None:
    cat = session.get(Category, category_id)
    if cat is None or cat.cafe_id != cafe_id:
        raise HTTPException(status_code=422, detail="Category does not belong to this Café")


def _next_position(session: Session, model, cafe_id: int) -> int:
    last = session.exec(select(func.max(model.position)).where(model.cafe_id == cafe_id)).one()
    return 0 if last is None else last + 1


def _product_out(p: Product) -> AdminProductOut:
    return AdminProductOut(**p.model_dump(), price_sar=halalas_to_sar(p.price))


def _commit_and_refresh(session: Session, row):
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get("/cafes", response_model=list[AdminCafeOut])
def list_cafes(session: Session = Depends(get_session)):
    return session.exec(select(Cafe).order_by(Cafe.id)).all()


@router.post("/cafes", status_code=201, response_model=AdminCafeOut)
def create_cafe(body: CafeIn, session: Session = Depends(get_session)):
    """A new Café with an empty Menu and its Barista login, in one transaction."""
    if session.exec(select(Cafe.id).where(Cafe.slug == body.slug)).first() is not None:
        raise HTTPException(status_code=409, detail="slug_taken")
    if session.exec(select(User.id).where(User.username == body.barista_username)).first() is not None:
        raise HTTPException(status_code=409, detail="username_taken")
    cafe =Cafe(slug=body.slug, name_ar=body.name_ar, name_en=body.name_en)
    session.add(cafe)
    session.flush()
    session.add(User(
        username=body.barista_username, password_hash=hash_password(body.barista_password),
        role=BARISTA, cafe_id=cafe.id,
    ))
    session.commit()
    session.refresh(cafe)
    return cafe


@router.get("/cafes/{cafe_id}/menu", response_model=AdminMenuOut)
def get_menu(cafe_id: int, session: Session = Depends(get_session)):
    cafe = _cafe_or_404(session, cafe_id)
    categories = session.exec(
        select(Category).where(Category.cafe_id == cafe_id).order_by(Category.position, Category.id)
    ).all()
    products = session.exec(
        select(Product).where(Product.cafe_id == cafe_id).order_by(Product.position, Product.id)
    ).all()
    return AdminMenuOut(
        cafe=CafeOut.model_validate(cafe, from_attributes=True),
        categories=[AdminCategoryOut.model_validate(c, from_attributes=True) for c in categories],
        products=[_product_out(p) for p in products],
    )


# ---------- Categories ----------

@router.post("/cafes/{cafe_id}/categories", status_code=201, response_model=AdminCategoryOut)
def create_category(cafe_id: int, body: CategoryIn, session: Session = Depends(get_session)):
    _cafe_or_404(session, cafe_id)
    position = _next_position(session, Category, cafe_id)
    return _commit_and_refresh(session, Category(cafe_id=cafe_id, position=position, **body.model_dump()))


@router.patch("/cafes/{cafe_id}/categories/{category_id}", response_model=AdminCategoryOut)
def update_category(cafe_id: int, category_id: int, body: CategoryPatch, session: Session = Depends(get_session)):
    cat = _category_or_404(session, cafe_id, category_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    return _commit_and_refresh(session, cat)


@router.delete("/cafes/{cafe_id}/categories/{category_id}", status_code=204)
def delete_category(cafe_id: int, category_id: int, session: Session = Depends(get_session)):
    cat = _category_or_404(session, cafe_id, category_id)
    if session.exec(select(Product.id).where(Product.category_id == cat.id)).first() is not None:
        raise HTTPException(status_code=409, detail="Category still has Products; move or delete them first")
    session.delete(cat)
    session.commit()
    return Response(status_code=204)


# ---------- Products ----------

@router.post("/cafes/{cafe_id}/products", status_code=201, response_model=AdminProductOut)
def create_product(cafe_id: int, body: ProductIn, session: Session = Depends(get_session)):
    _cafe_or_404(session, cafe_id)
    _check_category(session, cafe_id, body.category_id)
    fields = body.model_dump()
    fields["price"] = fields.pop("price_sar")
    product = Product(cafe_id=cafe_id, position=_next_position(session, Product, cafe_id), **fields)
    return _product_out(_commit_and_refresh(session, product))


@router.patch("/cafes/{cafe_id}/products/{product_id}", response_model=AdminProductOut)
def update_product(cafe_id: int, product_id: int, body: ProductPatch, session: Session = Depends(get_session)):
    product = _product_or_404(session, cafe_id, product_id)
    fields = body.model_dump(exclude_unset=True)
    if "category_id" in fields:
        _check_category(session, cafe_id, fields["category_id"])
    if "price_sar" in fields:
        fields["price"] = fields.pop("price_sar")
    for k, v in fields.items():
        setattr(product, k, v)
    return _product_out(_commit_and_refresh(session, product))


@router.delete("/cafes/{cafe_id}/products/{product_id}", status_code=204)
def delete_product(cafe_id: int, product_id: int, session: Session = Depends(get_session)):
    product = _product_or_404(session, cafe_id, product_id)
    if session.exec(select(OrderLine.id).where(OrderLine.product_id == product.id)).first() is not None:
        raise HTTPException(status_code=409, detail="Product is on past Orders; mark it unavailable instead")
    session.delete(product)
    session.commit()
    return Response(status_code=204)
