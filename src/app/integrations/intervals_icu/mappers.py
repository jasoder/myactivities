from datetime import datetime
from typing import Any, Optional
from models.completed_activity import CompletedActivity, ActivitySource  

def map_icu_activity_to_completed(icu_data: dict[str, Any], athlete_id: str) -> CompletedActivity:
    """
    Convert an Intervals.icu API workout (IcuActivity) into a CompletedActivity ORM object.
    """

    def safe_get(key: str, default: Optional[Any] = None) -> Any:
        return icu_data.get(key, default)

    activity = CompletedActivity(
        # Identifiers
        source=ActivitySource.INTERVALS,
        external_id=str(safe_get("id")),
        intervals_id=str(safe_get("id")),
        athlete_id=athlete_id,

        # Metadata
        name=safe_get("name"),
        description=safe_get("description"),
        sport_type=safe_get("type"),
        sub_type=safe_get("sub_type"),
        start_date=parse_datetime(safe_get("start_date")),
        start_date_local=parse_datetime(safe_get("start_date_local")),
        timezone=safe_get("timezone"),
        trainer=safe_get("trainer"),
        commute=safe_get("commute"),
        race=safe_get("race"),

        # Summary metrics
        distance_m=safe_get("distance"),
        elapsed_time_s=safe_get("elapsed_time"),
        moving_time_s=safe_get("moving_time"),
        elevation_gain_m=safe_get("total_elevation_gain"),
        elevation_loss_m=safe_get("total_elevation_loss"),
        average_speed_mps=safe_get("average_speed"),
        max_speed_mps=safe_get("max_speed"),
        average_cadence=safe_get("average_cadence"),
        average_temp_c=safe_get("average_temp"),
        average_hr_bpm=safe_get("average_heartrate"),
        max_hr_bpm=safe_get("max_heartrate"),
        average_power_w=safe_get("icu_average_watts"),
        weighted_power_w=safe_get("icu_weighted_avg_watts"),
        max_power_w=safe_get("p_max"),
        calories_kcal=safe_get("calories"),
        carbs_used_g=safe_get("carbs_used"),

        # Intervals.icu metrics
        icu_training_load=safe_get("icu_training_load"),
        icu_trimp=safe_get("trimp"),
        icu_intensity=safe_get("icu_intensity"),
        icu_efficiency_factor=safe_get("icu_efficiency_factor"),
        icu_variability_index=safe_get("icu_variability_index"),
        icu_joules=safe_get("icu_joules"),
        icu_rpe=safe_get("icu_rpe"),
        icu_feel=safe_get("feel"),

        # Device & gear
        device_name=safe_get("device_name"),
        gear_id=safe_get("gear", {}).get("id") if safe_get("gear") else None,
        gear_name=safe_get("gear", {}).get("name") if safe_get("gear") else None,
        gear_distance_m=safe_get("gear", {}).get("distance") if safe_get("gear") else None,

        # Sync
        icu_sync_date=parse_datetime(safe_get("icu_sync_date")),
        analyzed=bool(safe_get("analyzed")),
        intervals_url=f"https://intervals.icu/activities/{safe_get('id')}",
    )

    return activity

def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safe datetime parser for ICU timestamps."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None