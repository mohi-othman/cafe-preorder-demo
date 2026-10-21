from sqlmodel import Field, SQLModel


class Cafe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name_ar: str
    name_en: str = ""


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    name_ar: str
    name_en: str = ""
    position: int = 0


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    name_ar: str
    name_en: str = ""
    description_ar: str | None = None
    description_en: str | None = None
    price: int  # halalas, VAT included
    available: bool = True
    image_url: str | None = None
    position: int = 0
