from enum import StrEnum


class ActivityStatus(StrEnum):
    planned = "planned"
    completed = "completed"
    missed = "missed"
    modified = "modified"


class ActivitySource(StrEnum):
    strava = "strava"
    manual = "manual"
    ai_generated = "ai_generated"

    # Alias used in seed scripts
    STRAVA = "strava"
