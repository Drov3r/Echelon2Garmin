from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.profile_type import FileType, Manufacturer, Event, EventType
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.messages.activity_message import ActivityMessage
import datetime

filename=""
path="/var/www/html/"
filename=path+filename
def getActvityStats():
    cadence=[]
    resistance=[]
    power=[]
    speed=[]
    time=[]
    first=True
    startTime=""
    endTime=""

    f = open(filename, "r")

    for x in f:
        if x!="\n":
            y=x.split(",")
            cadence.append(int(y[0]))
            power.append(int(y[1]))
            resistance.append(int(y[2]))
            speed.append(int(y[0])*.38)
            time.append(y[3])
            endTime = y[3]
            if first:
                    first=False
                    startTime=y[3]

    totalPower=sum(power)
    maxCadence=max(cadence)
    avgCadence=sum(cadence)/len(cadence)
    avgPower=sum(power)/len(power)
    maxPower=max(power)
    avgResistance=sum(resistance)/len(resistance)
    maxResistance=max(resistance)
    avgSpeed=sum(speed)/len(speed)
    maxSpeed=max(speed)
    calories=totalPower*0.0013
    distance = getDistance(speed,time)
    duration=getDurationSec(startTime,endTime)
    activityStats=[totalPower,maxCadence,avgCadence,avgPower,maxPower,avgResistance,maxResistance,maxSpeed,calories,startTime,endTime,distance,avgSpeed,duration]
    return activityStats

def getDistance(speed,time):
    count=0
    previousTime=time[0]
    speedInASec=[]
    distanceInMeters=0
    for t in time:
        if (t==previousTime):
            speedInASec.append(speed[count])
        if (t!=previousTime):
            avgSpeedPerSec=sum(speedInASec)/len(speedInASec)
            distanceInMeters=distanceInMeters+(avgSpeedPerSec/3600)*1000
        previousTime=t
        count=count+1
    return distanceInMeters


def monthToNum(shortMonth):
    return {
            'January': 1,
            'Febuary': 2,
            'March': 3,
            'April': 4,
            'May': 5,
            'June': 6,
            'July': 7,
            'August': 8,
            'September': 9,
            'October': 10,
            'November': 11,
            'December': 12
    }[shortMonth]
def getStartTime(time):
    #output 2024-11-25T15:15:21Z
    #input November 26 2024 23:15:24
    splittime=time.split(" ")
    return str(splittime[2])+"-"+str(monthToNum(splittime[0]))+"-"+str(splittime[1])+"T"+str(splittime[3].replace("\n",""))


def getDurationSec(t1, t2):
    time1=t1.split(" ")[3].replace('\n',"")
    time2=t2.split(" ")[3].replace('\n',"")


    s1 = time1
    s2 = time2  # for example
    FMT = '%H:%M:%S'

    tdelta = datetime.datetime.strptime(s2, FMT) - datetime.datetime.strptime(s1, FMT)

    sec=tdelta.seconds
    return  sec





if __name__ == '__main__':



    # Set auto_define to true, so that the builder creates the required Definition Messages for us.
    builder = FitFileBuilder(auto_define=True, min_string_size=50)
    workout = open(filename, "r")
    f=workout.readline()
    date=f.split(",")[3].split(" ")
    now_timestamp_millis = round(datetime.datetime(int(date[2]), int(monthToNum(date[0])), int(date[1]), int(date[3].split(":")[0]), int(date[3].split(":")[1]), int(date[3].split(":")[2])).timestamp()) * 1000
    message = FileIdMessage()
    message.type = FileType.ACTIVITY
    message.manufacturer = Manufacturer.STAGES_CYCLING.value
    message.product = 0

    message.time_created = now_timestamp_millis
    message.serial_number = 0x12345678
    builder.add(message)

    # It is a best practice to include timer start and stop events in all Activity files. A timer start event
    # should occur before the first Record message in the file, and a timer stop event should occur after the
    # last Record message in the file when the activity recording is complete. Timer stop and start events
    # should be used anytime the activity recording has been paused and resumed. Record messages should not be
    # encoded to the file when the timer is paused.
    start_timestamp = now_timestamp_millis
    message = EventMessage()
    message.event = Event.TIMER
    message.event_type = EventType.START
    message.timestamp = start_timestamp
    builder.add(message)


    distance = 0.0
    timestamp = start_timestamp

    records = []

    prev_coordinate = None

    activityStats=getActvityStats()

    workout=open(filename,"r")
    workout_name="workout4"

    previousTime=""
    first=True
    linePerSec=[]
    for line in workout:
        split = line.split(",")
        if first:
            first=False
            previousTime=split[3]


        if (previousTime==split[3]):
            linePerSec.append(split)
            previousTime=split[3]
        if (previousTime!=split[3]):
            previousTime=split[3]
            count=0
            sumCad=0
            sumPow=0
            sumRes=0
            for l in linePerSec:
                sumCad+=int(l[0])
                sumPow+=int(l[1])
                sumRes+=int(l[2])
                count+=1

            message = RecordMessage()

            message.timestamp = timestamp
            avgCad=sumCad/count
            message.cadence=avgCad
            avgSpd=(avgCad*.38)/10
            message.speed=avgSpd
            message.power = sumPow/count
            message.resistance=sumRes/count
            distance+=(avgSpd*10000)/3600
            message.distance = distance
            records.append(message)
            linePerSec=[]

            timestamp += 1000



    builder.add_all(records)



    message = EventMessage()
    message.event = Event.TIMER
    message.event_type = EventType.STOP
    message.timestamp = timestamp
    builder.add(message)
    builder.add(message)


    message = LapMessage()
    message.event = Event.LAP
    message.timestamp=timestamp
    message.event_type=EventType.STOP
    message.start_time = start_timestamp
    message.total_elapsed_time=activityStats[13]
    message.total_timer_time=activityStats[13]
    message.total_distance=distance
    message.avg_power = activityStats[3]
    message.max_power = activityStats[4]
    message.lap_trigger=0
    builder.add(message)

    message=SessionMessage()
    message.timestamp=timestamp
    message.event= Event.LAP
    message.event=EventType.STOP
    message.start_time=start_timestamp
    message.total_elapsed_time=activityStats[13]
    message.total_timer_time=activityStats[13]
    message.total_distance=distance
    message.avg_power=activityStats[3]
    message.max_power=activityStats[4]
    builder.add(message)

    message=ActivityMessage()
    message.timestamp=timestamp
    message.total_timer_time=activityStats[13]
    message.event=Event.LAP
    message.event_type=EventType.STOP
    builder.add(message)
    #[totalPower, maxCadence, avgCadence, avgPower, maxPower, avgResistance, maxResistance, maxSpeed, calories,startTime, endTime, distance, avgSpeed, duration]

    # Finally build the FIT file object and write it to a file
    fit_file = builder.build()

    out_path = filename+'.fit'
    fit_file.to_file(out_path)
    csv_path = filename+'.csv'
    fit_file.to_csv(csv_path)
