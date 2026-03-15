"""Product API - CRUD operations and file import."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional

from models.database import get_db, Product, ActivityLog
from models.schemas import ProductCreate, ProductResponse
from utils.file_parser import parse_file

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all products with optional filters."""
    query = select(Product).order_by(Product.created_at.desc())
    if status:
        query = query.where(Product.status == status)
    if category:
        query = query.where(Product.category == category)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def product_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Product.id)))
    active = await db.execute(
        select(func.count(Product.id)).where(Product.status == "active")
    )
    categories = await db.execute(
        select(Product.category, func.count(Product.id)).group_by(Product.category)
    )
    return {
        "total": total.scalar() or 0,
        "active": active.scalar() or 0,
        "categories": {row[0] or "Chưa phân loại": row[1] for row in categories.all()}
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return product


@router.post("/", response_model=ProductResponse)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    db.add(ActivityLog(
        action="product_created", entity_type="product",
        entity_id=product.id, details={"name": product.name}
    ))
    await db.commit()
    return product


@router.post("/import")
async def import_products(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Import products from Excel/CSV file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có file")
    allowed_ext = (".xlsx", ".xls", ".csv", ".tsv")
    if not file.filename.lower().endswith(allowed_ext):
        raise HTTPException(status_code=400, detail=f"Chỉ chấp nhận: {', '.join(allowed_ext)}")

    content = await file.read()
    try:
        products_data = parse_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    created = []
    for item in products_data:
        product = Product(
            name=item["name"], price=item.get("price"),
            original_price=item.get("original_price"),
            category=item.get("category"), description=item.get("description"),
            images=item.get("images", []), source="import"
        )
        db.add(product)
        created.append(item["name"])

    await db.commit()
    db.add(ActivityLog(
        action="products_imported", entity_type="product",
        details={"file": file.filename, "count": len(created)}
    ))
    await db.commit()
    return {"success": True, "imported": len(created), "products": created[:20]}


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, data: ProductCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    await db.execute(delete(Product).where(Product.id == product_id))
    await db.commit()
    return {"success": True, "message": f"Đã xóa: {product.name}"}
