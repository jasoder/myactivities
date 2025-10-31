from typing import TypedDict, Literal
from datetime import datetime

class Gear(TypedDict, total=False):
    id: str
    name: str
    distance: float
    primary: bool

class IgnorePart(TypedDict, total=False):
    start_index: int
    end_index: int
    power: bool
    pace: bool
    hr: bool

class ZoneTime(TypedDict, total=False):
    id: str
    secs: int

class CustomZoneDetail(TypedDict, total=False):
    id: str
    start: float
    end: float
    start_value: float
    end_value: float
    secs: int

class CustomZone(TypedDict, total=False):
    code: str
    zones: list[CustomZoneDetail]

class AchievementPoint(TypedDict, total=False):
    start_index: int
    end_index: int
    secs: int
    value: int

class Achievement(TypedDict, total=False):
    id: str
    type: Literal["BEST_POWER", "FTP_UP", "LTHR_UP", "BEST_PACE"]
    message: str
    watts: int
    secs: int
    value: int
    distance: float
    pace: float
    point: AchievementPoint

class Hrr(TypedDict, total=False):
    start_index: int
    end_index: int
    start_time: int
    end_time: int
    start_bpm: int
    end_bpm: int
    average_watts: int
    hrr: int

class Attachment(TypedDict, total=False):
    id: str
    filename: str
    mimetype: str
    url: str

class IcuActivity(TypedDict, total=False):
    id: str
    start_date_local: str
    type: str
    icu_ignore_time: bool
    icu_pm_cp: int
    icu_pm_w_prime: int
    icu_pm_p_max: int
    icu_pm_ftp: int
    icu_pm_ftp_secs: int
    icu_pm_ftp_watts: int
    icu_ignore_power: bool
    icu_rolling_cp: float
    icu_rolling_w_prime: float
    icu_rolling_p_max: float
    icu_rolling_ftp: int
    icu_rolling_ftp_delta: int
    icu_training_load: int
    icu_atl: float
    icu_ctl: float
    ss_p_max: float
    ss_w_prime: float
    ss_cp: float
    paired_event_id: int
    icu_ftp: int
    icu_joules: int
    icu_recording_time: int
    elapsed_time: int
    icu_weighted_avg_watts: int
    carbs_used: int
    name: str
    description: str
    start_date: str
    distance: float
    icu_distance: float
    moving_time: int
    coasting_time: int
    total_elevation_gain: float
    total_elevation_loss: float
    timezone: str
    trainer: bool
    sub_type: Literal["NONE", "COMMUTE", "WARMUP", "COOLDOWN", "RACE"]
    commute: bool
    race: bool
    max_speed: float
    average_speed: float
    device_watts: bool
    has_heartrate: bool
    max_heartrate: int
    average_heartrate: int
    average_cadence: float
    calories: int
    average_temp: float
    min_temp: int
    max_temp: int
    avg_lr_balance: float
    gap: float
    gap_model: Literal["NONE", "STRAVA_RUN"]
    use_elevation_correction: bool
    gear: Gear
    perceived_exertion: int
    device_name: str
    power_meter: str
    power_meter_serial: str
    power_meter_battery: str
    crank_length: float
    external_id: str
    file_sport_index: int
    file_type: str
    icu_athlete_id: str
    created: datetime
    icu_sync_date: datetime
    analyzed: datetime
    icu_w_prime: int
    p_max: int
    threshold_pace: float
    icu_hr_zones: list[int]
    pace_zones: list[float]
    lthr: int
    icu_resting_hr: int
    icu_weight: float
    icu_power_zones: list[int]
    icu_sweet_spot_min: int
    icu_sweet_spot_max: int
    icu_power_spike_threshold: int
    trimp: float
    icu_warmup_time: int
    icu_cooldown_time: int
    icu_chat_id: int
    icu_ignore_hr: bool
    ignore_velocity: bool
    ignore_pace: bool
    ignore_parts: list[IgnorePart]
    icu_training_load_data: int
    interval_summary: list[str]
    skyline_chart_bytes: list[bytes]
    stream_types: list[str]
    has_weather: bool
    has_segments: bool
    power_field_names: list[str]
    power_field: str
    icu_zone_times: list[ZoneTime]
    icu_hr_zone_times: list[int]
    pace_zone_times: list[int]
    gap_zone_times: list[int]
    use_gap_zone_times: bool
    custom_zones: list[CustomZone]
    tiz_order: Literal[
        "POWER_HR_PACE", "POWER_PACE_HR", "HR_POWER_PACE", "HR_PACE_POWER",
        "PACE_POWER_HR", "PACE_HR_POWER"
    ]
    polarization_index: float
    icu_achievements: list[Achievement]
    icu_intervals_edited: bool
    lock_intervals: bool
    icu_lap_count: int
    icu_joules_above_ftp: int
    icu_max_wbal_depletion: int
    icu_hrr: Hrr
    icu_sync_error: str
    icu_color: str
    icu_power_hr_z2: float
    icu_power_hr_z2_mins: int
    icu_cadence_z2: int
    icu_rpe: int
    feel: int
    kg_lifted: float
    decoupling: float
    icu_median_time_delta: int
    p30s_exponent: float
    workout_shift_secs: int
    strava_id: str
    lengths: int
    pool_length: float
    compliance: float
    coach_tick: int
    source: Literal[
        "STRAVA", "UPLOAD", "MANUAL", "GARMIN_CONNECT", "OAUTH_CLIENT",
        "DROPBOX", "POLAR", "SUUNTO", "COROS", "WAHOO", "ZWIFT", "ZEPP", "CONCEPT2"
    ]
    oauth_client_id: int
    oauth_client_name: str
    average_altitude: float
    min_altitude: float
    max_altitude: float
    power_load: int
    hr_load: int
    pace_load: int
    hr_load_type: Literal["AVG_HR", "HR_ZONES", "HRSS"]
    pace_load_type: Literal["SWIM", "RUN"]
    tags: list[str]
    attachments: list[Attachment]
    recording_stops: list[int]
    average_weather_temp: float
    min_weather_temp: float
    max_weather_temp: float
    average_feels_like: float
    min_feels_like: float
    max_feels_like: float
    average_wind_speed: float
    average_wind_gust: float
    prevailing_wind_deg: int
    headwind_percent: float
    tailwind_percent: float
    average_clouds: int
    max_rain: float
    max_snow: float
    carbs_ingested: int
    route_id: int
    pace: float
    athlete_max_hr: int
    group: str
    icu_intensity: float
    icu_efficiency_factor: float
    icu_power_hr: float
    session_rpe: int
    average_stride: float
    icu_average_watts: int
    icu_variability_index: float
    strain_score: float
