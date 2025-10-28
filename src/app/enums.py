from enum import StrEnum

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