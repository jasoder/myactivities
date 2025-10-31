from app.integrations.intervals_icu.client import IntervalsClient
from app.integrations.intervals_icu.mappers import map_intervals_activity_to_activity
from app.db.session import SessionLocal
from datetime import datetime

async def sync_intervals_all_activities(api_key: str, athlete_id: str):
    client = IntervalsClient(api_key)
    activities_df = await client.get_activities_csv(athlete_id)

    activities_df = SessionLocal()
    for _, IntervalsActivity in df.iterrows():
        activity = map_intervals_activity_to_activity(IntervalsActivity)
        db.add(activity)
    activities_df.commit()
    
async def sync_intervals_activities_from_date(api_key: str, athlete_id: str, from_date: datetime):
    client = IntervalsClient(api_key)
    df = await client.get_activities_from_date(athlete_id, from_date)

    db = SessionLocal()
    for _, row in df.iterrows():
        activity = map_intervals_activity_to_activity(row)
        db.add(activity)
    db.commit()
    
def save_icu_activity(session, raw: dict, athlete_id: int):
    icu_fields = {k: v for k, v in raw.items() if k.startswith("icu_")}
    activity_fields = {k: v for k, v in raw.items() if not k.startswith("icu_")}

    activity = IcuActivityModel(
        athlete_id=athlete_id,
        name=activity_fields["name"],
        type=activity_fields["type"],
        start_date_local=datetime.fromisoformat(activity_fields["start_date_local"]),
        elapsed_time=activity_fields["elapsed_time"],
        distance=activity_fields["distance"],
        average_speed=activity_fields["average_speed"],
        icu_data=IcuDataModel(data=icu_fields),
    )

    session.add(activity)
    session.commit()
