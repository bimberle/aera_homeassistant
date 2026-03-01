"""Constants for the Aera integration."""

DOMAIN = "aera"

# Session durations in minutes
SESSION_DURATION_2H = 120
SESSION_DURATION_4H = 240
SESSION_DURATION_8H = 480

SESSION_DURATIONS = {
    "2h": SESSION_DURATION_2H,
    "4h": SESSION_DURATION_4H,
    "8h": SESSION_DURATION_8H,
}

# Intensity range
INTENSITY_MIN = 1
INTENSITY_MAX = 10

# Update interval in seconds
UPDATE_INTERVAL = 30

# Schedule update interval in seconds (schedules change rarely)
SCHEDULE_UPDATE_INTERVAL = 300  # 5 minutes
