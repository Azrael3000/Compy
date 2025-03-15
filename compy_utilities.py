def convDay(day):
    try:
        day = int(day)
        year = day//10000
        month = (day-year*10000)//100
        day = day%100
        return str(year).zfill(4) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2)
    except ValueError:
        if '-' in day:
            day = day.split('-')
            if len(day) == 3:
                return int(day[0])*10000 + int(day[1])*100 + int(day[2])
    return None

def convTime(time):
    try:
        time = int(time)
        hour = time//100
        time = time%100
        return str(hour).zfill(2) + ":" + str(time).zfill(2)
    except ValueError:
        if ':' in time:
            time = time.split(':')
            if len(time) == 2:
                return int(time[0])*100 + int(time[1])
    return None
