import math

def distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "K") -> float:
    if lat1 == lat2 and lon1 == lon2:
        return 0
    
    theta = lon1 - lon2
    dist = (math.sin(math.radians(lat1)) * math.sin(math.radians(lat2)) + 
           math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
           math.cos(math.radians(theta)))
    dist = math.acos(dist)
    dist = math.degrees(dist)
    miles = dist * 60 * 1.1515
    
    return miles * 1.609344 if unit == "K" else miles * 0.8684 if unit == "N" else miles