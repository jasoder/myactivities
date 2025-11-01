from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_completed_actities():
    return {"message": "List of activities"}

@router.post("/")
async def create_completed_actity():
    return {"message": "Activity created"}

@router.delete("/")
async def delete_completed_actity():
    return {"message": "Activity deleted"}

@router.put("/")
async def update_completed_actity():
    return {"message": "Activity updated"}