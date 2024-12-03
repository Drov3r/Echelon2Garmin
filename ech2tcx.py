
from datetime import datetime
import fit_tool
filename=""
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
    activityStats=[totalPower,maxCadence,avgCadence,avgPower,maxPower,avgResistance,maxResistance,maxSpeed,calories,startTime,endTime,distance]
    return activityStats
    #TotalPower         SUM of Watts?
    #MaximumCadence     Y
    #AverageCadence     Y
    #AverageWatts       Y
    #MaximumWatts       Y
    #AverageResistance  Y
    #MaximumResistance  Y
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
    tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)

    sec=tdelta.seconds
    return  sec


if __name__ == '__main__':
    activityStats=getActvityStats()
    f=open("export.tcx", "w")
    f.write("""<?xml version="1.0" encoding="utf-8"?>
                <TrainingCenterDatabase xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:activityExtensions="http://www.garmin.com/xmlschemas/ActivityExtension/v2" xmlns:trackPointExtensions="http://www.garmin.com/xmlschemas/TrackPointExtension/v2" xmlns:profileExtension="http://www.garmin.com/xmlschemas/ProfileExtension/v1" xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
                  <Activities>
                    <Activity Sport="Biking">
                      <Id>"""+getStartTime(activityStats[9])+"""</Id>
                      <Lap StartTime="""+'"'+getStartTime(activityStats[9])+'"'+""">
                        <TotalTimeSeconds>"""+str(getDurationSec(activityStats[9],activityStats[10]))+"""</TotalTimeSeconds>
                        <Intensity>Active</Intensity>
                        <Triggermethod>Manual</Triggermethod>
                        <DistanceMeters>"""+str(activityStats[11])+"""</DistanceMeters>
                        <MaximumSpeed>"""+str(activityStats[7])+"""</MaximumSpeed>
                        <Calories>"""+str(activityStats[8])+"""</Calories>
                        <AverageHeartRateBpm>
                          <Value>126</Value>
                        </AverageHeartRateBpm>
                        <MaximumHeartRateBpm>
                          <Value>143</Value>
                        </MaximumHeartRateBpm>
                        <activityExtensions:TPX>
                          <activityExtensions:TotalPower>"""+str(activityStats[0])+"""</activityExtensions:TotalPower>
                          <activityExtensions:MaximumCadence>"""+str(activityStats[1])+"""</activityExtensions:MaximumCadence>
                          <activityExtensions:AverageCadence>"""+str(activityStats[2])+"""</activityExtensions:AverageCadence>
                          <activityExtensions:AverageWatts>"""+str(activityStats[3])+"""</activityExtensions:AverageWatts>
                          <activityExtensions:MaximumWatts>"""+str(activityStats[4])+"""</activityExtensions:MaximumWatts>
                          <activityExtensions:AverageResistance>"""+str(activityStats[5])+"""</activityExtensions:AverageResistance>
                          <activityExtensions:MaximumResistance>"""+str(activityStats[6])+"""</activityExtensions:MaximumResistance>
                        </activityExtensions:TPX>
                        <Track>""")
    workout=open(filename,"r")

    for line in workout:
        split=line.split(",")
        f.write("""<TrackPoint>
            <HeartRateBpm>
              <Value>90</Value>
            </HeartRateBpm>
            <Cadence>"""+str(split[0])+"""</Cadence>
            <Extensions>
              <activityExtensions:TPX>
                <activityExtensions:Speed>"""+str(int(split[0])*0.38)+"""</activityExtensions:Speed>
                <activityExtensions:Watts>"""+str(split[1])+"""</activityExtensions:Watts>
                <activityExtensions:Resistance>"""+str(split[2])+"""</activityExtensions:Resistance>
              </activityExtensions:TPX>
            </Extensions>
            <Time>"""+str(getStartTime(split[3]))+"""</Time>
          </TrackPoint>
          """)
    f.write("""</Track>
      </Lap>
      <Creator xsi:type="Device_t">
        <Name>TacxTrainingAppWin</Name>
        <UnitId>1</UnitId>
        <ProductID>20533</ProductID>
        <Version>
          <VersionMajor>1</VersionMajor>
          <VersionMinor>30</VersionMinor>
          <BuildMajor>0</BuildMajor>
          <BuildMinor>0</BuildMinor>
        </Version>
      </Creator>
    </Activity>
  </Activities>
</TrainingCenterDatabase>""")