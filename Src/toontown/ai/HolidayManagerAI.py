from toontown.toonbase import ToontownGlobals
from toontown.effects.DistributedFireworkShowAI import DistributedFireworkShowAI
from toontown.effects import FireworkShows

class HolidayManagerAI:

    def __init__(self, air):
        self.air = air
        self.currentHolidays = []
        self.xpMultiplier = 1
        self.setup()
        self.fireworkTasks= []

    def setup(self):
        holidays = config.GetString('active-holidays','')
        if holidays != '':
            for holiday in holidays.split(","):
                holiday = int(holiday)
                self.currentHolidays.append(holiday)
            simbase.air.newsManager.setHolidayIdList([self.currentHolidays])

    def isHolidayRunning(self, holidayId):
        if holidayId in self.currentHolidays:
            return True
            
    def areHolidaysRunning(self, holidayIds):
        for holidayId in holidayIds:
            if holidayId in self.currentHolidays:
                return True

        return False

    def isMoreXpHolidayRunning(self):
        if ToontownGlobals.MORE_XP_HOLIDAY in self.currentHolidays:
            self.xpMultiplier = 2
            return True
        return False

    def getXpMultiplier(self):
        return self.xpMultiplier

    def startFireworkTask(self, id, task=None):
        self.startFireworks(id)
        self.fireworkTasks.append(taskMgr.doMethodLater(1, self.startFireworks, 'fireworkTask-%s' % id, extraArgs=[id]))

    def startFireworks(self, type, task=None):
        maxShow = len(FireworkShows.shows.get(type, [])) - 1

        for hood in self.air.hoods:
            if hood.zoneId == ToontownGlobals.GolfZone:
                continue

            fireworkShow = DistributedFireworkShowAI(self.air)
            fireworkShow.generateWithRequired(hood.zoneId)
            fireworkShow.b_startShow(type, random.randint(0, maxShow), globalClockDelta.getRealNetworkTime())

        return Task.again

    def appendHoliday(self, holidayId):
        if holidayId not in self.currentHolidays:
            self.currentHolidays.append(holidayId)
            self.air.newsManager.setHolidayIdList([self.currentHolidays])
            return True

    def removeHoliday(self, holidayId):
        if holidayId in self.currentHolidays:
            self. currentHolidays.remove(holidayId)
            self.air.newsManager.setHolidayIdList([self.currentHolidays])
            return True

from otp.ai.MagicWordGlobal import *

@magicWord(category=CATEGORY_PROGRAMMER, types=[int])
def startHoliday(holidayId):
    if simbase.air.holidayManager.appendHoliday(holidayId) == True:
        return 'Started Holiday %s' % holidayId
    return 'Holiday %s is already running' % holidayId

@magicWord(category=CATEGORY_PROGRAMMER, types=[int])
def endHoliday(holidayId):
    if simbase.air.holidayManager.removeHoliday(holidayId) == True:
        return 'Ended Holiday %s' % holidayId
    return 'Holiday %s already ended' % holidayId
