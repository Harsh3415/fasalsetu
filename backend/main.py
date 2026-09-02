from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI(title="FasalSetu API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "FasalSetu API is running"
    }


@app.post("/assess")
async def assess_claim(
    crop: str = Form(...),
    damage_type: str = Form(...),
    area: float = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...)
):

    # Demo AI assessment
    damage_percentage = random.randint(45, 85)
    confidence = random.randint(80, 96)
    consistency = random.randint(75, 95)

    if consistency >= 90:
        priority = "LOW"
        recommendation = "Routine processing"
    elif consistency >= 75:
        priority = "MEDIUM"
        recommendation = "Human verification required"
    else:
        priority = "HIGH"
        recommendation = "Priority investigation"

    return {
        "field_id": "FSL-1024",
        "crop": crop,
        "damage_type": damage_type,
        "area_hectares": area,
        "damage_percentage": damage_percentage,
        "confidence": confidence,
        "consistency_score": consistency,
        "priority": priority,
        "recommendation": recommendation,
        "location": {
            "latitude": latitude,
            "longitude": longitude
        }
    }