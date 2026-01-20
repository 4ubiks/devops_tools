# A script to generate a 'Weekly' template file to track my work hours. 
# Template: 

# # X/XX/XXXX - X/XX/XXXX
# Crewed hours:
# - `X.0` - event X/XX
#
# Total: `X.0`
#
# Required Office Hours: `38.0 - Total`
# Monday X/XX:

# Tuesday X/XX:

# Wednesday X/XX:

# Thursday X/XX:

# Friday X/XX:

from datetime import date, timedelta

startDateFmt = date.today()
weekdateInt = startDateFmt.weekday()
monthDate = startDateFmt.month

weekdayNumbers = [0, 1, 2, 3, 4, 5, 6]
weekdayDates = ["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]

def startDate(weekday, weekdateInt, todayDate, dater):
    delta_days = weekday - weekdateInt
    startDate = todayDate + timedelta(days=delta_days)
    dater = str(monthDate) + "/" + str(startDate.day) 
    return dater

match weekdateInt:
    case 0:
        startDateFmt = startDate(weekdayNumbers[0], weekdateInt, startDateFmt)
    case 1:
        weekdayNumbers = [-1, 0, 1, 2, 3, 4, 5]
        counter = 0;
        for weekday in weekdayNumbers:
            weekdayDates[counter] = startDate(weekday, weekdateInt, startDateFmt, weekdayDates[counter])
            counter+=1
        startDateFmt = startDateFmt + timedelta(days=(0-weekdateInt))
        endDateFmt = startDateFmt + timedelta(days=(5-weekdateInt))
            
    case 2:
        weekdayNumbers = [-1, 0, 1, 2, 3, 4, 5]
        counter = 0;
        for weekday in weekdayNumbers:
            weekdayDates[counter] = startDate(weekday, weekdateInt, startDateFmt, weekdayDates[counter])
            counter+=1
        startDateFmt = startDateFmt + timedelta(days=(1-weekdateInt))
        endDateFmt = startDateFmt + timedelta(days=(4-weekdateInt))
    case 3:
        weekdayNumbers = [-1, 0, 1, 2, 3, 4, 5]
        counter = 0;
        for weekday in weekdayNumbers:
            weekdayDates[counter] = startDate(weekday, weekdateInt, startDateFmt, weekdayDates[counter])
            counter+=1
        startDateFmt = startDateFmt + timedelta(days=(2-weekdateInt))
        endDateFmt = startDateFmt + timedelta(days=(3-weekdateInt))
    case 4:
        weekdayNumbers = [-1, 0, 1, 2, 3, 4, 5]
        counter = 0;
        for weekday in weekdayNumbers:
            weekdayDates[counter] = startDate(weekday, weekdateInt, startDateFmt, weekdayDates[counter])
            counter+=1
        startDateFmt = startDateFmt + timedelta(days=(3-weekdateInt))
        endDateFmt = startDateFmt + timedelta(days=(2-weekdateInt))
        
    case 5:
        weekdayNumbers = [-1, 0, 1, 2, 3, 4, 5]
        counter = 0;
        for weekday in weekdayNumbers:
            weekdayDates[counter] = startDate(weekday, weekdateInt, startDateFmt, weekdayDates[counter])
            counter+=1
        startDateFmt = startDateFmt + timedelta(days=(4-weekdateInt))
        endDateFmt = startDateFmt + timedelta(days=(1-weekdateInt))
    case 6:
        weekdayNumbers = [-1, 0, 1, 2, 3, 4, 5]
        counter = 0;
        for weekday in weekdayNumbers:
            weekdayDates[counter] = startDate(weekday, weekdateInt, startDateFmt, weekdayDates[counter])
            counter+=1
        startDateFmt = startDateFmt + timedelta(days=(5-weekdateInt))
        endDateFmt = startDateFmt + timedelta(days=(0-weekdateInt))


with open("weekly.md", "w") as file:
    pass

with open("weekly.md", "w") as weeklyFile:
    weeklyFile.write(f"# {startDateFmt} - {endDateFmt}\n\n")
    weeklyFile.write("Crewed hours:\n\n")
    weeklyFile.write("Total: \n\n")

    weeklyFile.write("Required Office Hours: \n\n")
    weeklyFile.write(f"- [ ] Monday {weekdayDates[1]}:\n")
    weeklyFile.write(f"- [ ] Tuesday {weekdayDates[2]}:\n")
    weeklyFile.write(f"- [ ] Wednesday {weekdayDates[3]}:\n")
    weeklyFile.write(f"- [ ] Thursday {weekdayDates[4]}:\n")
    weeklyFile.write(f"- [ ] Friday {weekdayDates[5]}:\n")
    

