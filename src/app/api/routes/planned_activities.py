from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_planned_actities():
    return {"message": "List of Planned activities"}

@router.post("/")
async def create_planned_actity():
    return {"message": "Planned activity created"}

@router.delete("/")
async def delete_planned_actity():
    return {"message": "Planned activity deleted"}

@router.put("/")
async def update_planned_actity():
    return {"message": "Planned activity updated"}