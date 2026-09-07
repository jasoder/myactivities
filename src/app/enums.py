from enum import StrEnum, Enum

class ActivityType(StrEnum):
    ride = "Ride"
    run = "Run"
    swim = "Swim"
    other = "Other"
    
class ActivityStatus(StrEnum):
    planned = "planned"
    completed = "completed"
    missed = "missed"
    modified = "modified"


class ActivityGoal(StrEnum):
    recovery = "Recovery"
    endurance = "Endurance"
    tempo = "Tempo"
    threshold = "Threshold"
    vo2max = "VO2 Max"
    intervals = "Intervals"
    long = "Long"

class ActivitySource(StrEnum):
    strava = "strava"
    intervals = "intervals"
    manual = "manual"
    ai_generated = "ai_generated"

    # Uppercase aliases for compatibility
    STRAVA = "strava"
    INTERVALS = "intervals"
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    debug = "DEBUG"