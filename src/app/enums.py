from enum import StrEnum, Enum

class ActivityType(StrEnum):
    ride = "Ride"
    run = "Run"
    swim = "Swim"
    other = "Other"
    
class ActivityGoal(StrEnum):
    recovery = "Recovery"
    endurance = "Endurance"
    tempo = "Tempo"
    threshold = "Threshold"
    vo2max = "VO2 Max"
    intervals = "Intervals"
    long = "Long"

class ActivitySource(Enum):
    STRAVA = "strava"
    INTERVALS = "intervals"

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    debug = "DEBUG"