from datetime import datetime
from typing import Any, Optional
from app.models.completed_activity import CompletedActivity, ActivitySource

def map_strava_activity_to_completed(strava_data: dict[str, Any], athlete_id: str) -> CompletedActivity:
    """
    Convert a Strava API activity into a CompletedActivity ORM object.
    """

    def safe_get(key: str, default: Optional[Any] = None) -> Any:
        return strava_data.get(key, default)

    # Map Strava activity type to our sport_type
    sport_type_mapping = {
        "Ride": "Ride",
        "Run": "Run",
        "Swim": "Swim",
        "Hike": "Hike",
        "Walk": "Walk",
        "AlpineSki": "Alpine Ski",
        "BackcountrySki": "Backcountry Ski",
        "Canoe": "Canoe",
        "Crossfit": "Crossfit",
        "EBikeRide": "E-bike Ride",
        "Elliptical": "Elliptical",
        "Golf": "Golf",
        "Handcycle": "Handcycle",
        "IceSkate": "Ice Skate",
        "InlineSkate": "Inline Skate",
        "Kayak": "Kayak",
        "Kitesurf": "Kitesurf",
        "NordicSki": "Nordic Ski",
        "RockClimbing": "Rock Climbing",
        "RollerSki": "Roller Ski",
        "Rowing": "Rowing",
        "Snowboard": "Snowboard",
        "Snowshoe": "Snowshoe",
        "Soccer": "Soccer",
        "StairStepper": "Stair Stepper",
        "StandUpPaddling": "Stand Up Paddling",
        "Surfing": "Surfing",
        "Velomobile": "Velomobile",
        "VirtualRide": "Virtual Ride",
        "VirtualRun": "Virtual Run",
        "WeightTraining": "Weight Training",
        "Wheelchair": "Wheelchair",
        "Windsurf": "Windsurf",
        "Workout": "Workout",
        "Yoga": "Yoga"
    }

    sport_type = sport_type_mapping.get(safe_get("type", "Workout"), safe_get("type"))

    activity = CompletedActivity(
        # Identifiers
        source=ActivitySource.STRAVA,
        external_id=str(safe_get("id")),
        strava_id=str(safe_get("id")),
        athlete_id=athlete_id,

        # Metadata
        name=safe_get("name"),
        description=safe_get("description"),
        sport_type=sport_type,
        start_date=parse_datetime(safe_get("start_date")),
        start_date_local=parse_datetime(safe_get("start_date_local")),
        timezone=safe_get("timezone"),

        # Summary metrics
        distance_m=safe_get("distance"),
        moving_time_s=safe_get("moving_time"),
        elapsed_time_s=safe_get("elapsed_time"),
        elevation_gain_m=safe_get("total_elevation_gain"),
        average_speed_mps=safe_get("average_speed"),
        max_speed_mps=safe_get("max_speed"),
        average_cadence=safe_get("average_cadence"),
        average_temp_c=safe_get("average_temp"),
        average_hr_bpm=safe_get("average_heartrate"),
        max_hr_bpm=safe_get("max_heartrate"),
        average_power_w=safe_get("average_watts"),
        max_power_w=safe_get("max_watts"),
        calories_kcal=safe_get("calories"),

        # Device & gear
        device_name=safe_get("device_name"),
        gear_id=safe_get("gear_id"),

        # Sync
        strava_sync_date=datetime.now(),
        analyzed=bool(safe_get("has_heartrate") or safe_get("has_power_meter")),
        strava_url=f"https://www.strava.com/activities/{safe_get('id')}",

        # Trainer/commute flags
        trainer=safe_get("trainer"),
        commute=safe_get("commute"),
    )

    return activity

def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safe datetime parser for Strava timestamps."""
    if not dt_str:
        return None
    try:
        # Strava returns ISO format like "2018-02-16T14:52:54Z"
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None