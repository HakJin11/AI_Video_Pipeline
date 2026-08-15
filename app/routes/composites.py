from fastapi import APIRouter, HTTPException, Query

from app import db

router = APIRouter(prefix="/api/composites", tags=["composites"])


@router.get("")
def list_composites():
    return db.list_composites()


@router.get("/find")
def find_composite(
    character1_id: int = Query(...),
    character2_id: int = Query(...),
    background_id: int = Query(...),
):
    composite = db.find_composite(character1_id, character2_id, background_id)
    if not composite:
        raise HTTPException(404, "no composite registered for this combination")
    return composite
