import datetime

def get_mensa_status(datetime: datetime) -> int:
    if datetime.weekday() in [5, 6]:
        # Weekend
        return -1
    
    if datetime.hour >= 11 and datetime.minute >= 30:
        # Mensa is open
        return 1
    
    if 8 <= datetime.hour < 15:
        # Café71 is open
        return 0
    
    # Café71 and Mensa71 are closed
    return -1