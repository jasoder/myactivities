from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_athlete():
    return {"message": "List of athletes"}

@router.post("/")
async def create_athlete():
    return {"message": "Athlete created"}

@router.put("/")
async def update_athlete():
    return {"message": "Athlete created"}

@router.delete("/")
async def delete_athlete():
    return {"message": "Athlete deleted"}