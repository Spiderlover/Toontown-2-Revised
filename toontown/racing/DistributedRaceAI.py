from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.fsm.FSM import FSM
from direct.task import Task
import random

from toontown.racing import RaceGlobals
from toontown.racing.DistributedGagAI import DistributedGagAI
from toontown.racing.DistributedVehicleAI import DistributedVehicleAI
from toontown.toonbase import TTLocalizer, ToontownGlobals


class DistributedRaceAI(DistributedObjectAI, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedRaceAI")

    def __init__(self, air, circuitPoints=[], circuitWinnings=[]):
        DistributedObjectAI.__init__(self, air)
        FSM.__init__(self, 'DistributedRaceAI')
        self.air = air
        self.zoneId = 0
        self.trackId = 0
        self.raceType = 0
        self.circuitLoop = []
        self.avatars = []
        self.finishedAvatars = []
        self.startingPlaces = []
        self.avatarKarts = []
        self.lapCount = 1
        self.gags = {}
        self.avatarGags = {}
        self.livingGags = []
        self.currentlyAffectedByAnvil = {}
        self.avatarProgress = {}
        self.circuitPoints = circuitPoints
        self.circuitWinnings = circuitWinnings
        self.quitAvatars = []
        self.startTime = globalClockDelta.networkToLocalTime(globalClockDelta.getRealNetworkTime()) + 3

    def generate(self):
        for avatar in self.avatars:
            self.acceptOnce(self.air.getAvatarExitEvent(avatar), self.playerLeave, [avatar])
        self.demand('Join')

    def delete(self):
        for aK in self.avatarKarts:
            kart = self.air.doId2do[aK[1]]
            kart.requestDelete()
        for gag in self.livingGags:
            gag.requestDelete()
        if not self.circuitLoop:
            self.air.deallocateZone(self.zoneId)
        for i in xrange(len(self.gags)):
            taskMgr.remove('regenGag%i-%i' % (i, self.doId))
        taskMgr.remove(self.uniqueName('next-race'))
        DistributedObjectAI.delete(self)

    def enterJoin(self):
        self.beginBarrier('waitingForJoin', self.avatars, 60, self.joinBarrierCallback)
        self.d_waitingForJoin()

    def exitJoin(self):
        pass

    def enterPrep(self):
        self.beginBarrier('waitingForReady', self.avatars, 60, self.readyBarrierCallback)
        self.gagPoints = RaceGlobals.TrackDict[self.trackId][4]
        if self.raceType != RaceGlobals.Practice:
            for i in xrange(len(self.gagPoints)):
                gagId = random.randint(0, 5)
                self.b_genGag(i, 1, gagId)
        self.d_prepForRace()

    def exitPrep(self):
        pass

    def enterTutorial(self):
        self.beginBarrier('readRules', self.avatars, 30, self.readRulesCallback)
        self.d_startTutorial()

    def exitTutorial(self):
        pass

    def enterStart(self):
        self.startTime = globalClockDelta.networkToLocalTime(globalClockDelta.getRealNetworkTime()) + 3
        self.b_startRace(3)

    def exitStart(self):
        pass

    def readyBarrierCallback(self, avatars):
        self.demand('Tutorial')

    def readRulesCallback(self, avatars):
        self.demand('Start')

    def joinBarrierCallback(self, avatars):
        for av in self.avatars:
            if not av in avatars:
                self.playerLeave(av)
        for av in avatars:
            kart = DistributedVehicleAI(self.air, av)
            kart.generateWithRequired(self.zoneId)
            self.avatarKarts.append([av, kart.getDoId()])
        self.beginBarrier('waitingForPrep', self.avatars, 60, self.prepBarrierCallback)
        self.sendUpdate('setEnteredRacers', [self.avatarKarts])

    def prepBarrierCallback(self, avatars):
        self.demand('Prep')

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def d_setZoneId(self, zoneId):
        self.sendUpdate('setZoneId', [zoneId])

    def b_setZoneId(self, zoneId):
        self.setZoneId(zoneId)
        self.d_setZoneId(zoneId)

    def getZoneId(self):
        return self.zoneId

    def setTrackId(self, trackId):
        self.trackId = trackId

    def getTrackId(self):
        return self.trackId

    def setRaceType(self, raceType):
        self.raceType = raceType

    def getRaceType(self):
        return self.raceType

    def setCircuitLoop(self, circuitLoop):
        self.circuitLoop = circuitLoop
        if self.circuitLoop and not self.circuitPoints:
            self.circuitPoints = [[0, 0]] * len(self.avatars)
            self.circuitWinnings = [0] * len(self.avatars)

    def getCircuitLoop(self):
        return self.circuitLoop

    def setAvatars(self, avatarList):
        self.avatars = avatarList

    def getAvatars(self):
        return self.avatars

    def setStartingPlaces(self, startingPlaces):
        self.startingPlaces = startingPlaces

    def getStartingPlaces(self):
        return self.startingPlaces

    def setLapCount(self, lapCount):
        self.lapCount = lapCount

    def getLapCount(self):
        return self.lapCount

    def waitingForJoin(self):
        self.beginBarrier('waitingForJoin', self.avatars, 60, self.b_prepForRace)

    def d_waitingForJoin(self):
        self.sendUpdate('waitingForJoin', [])

    def b_waitingForJoin(self):
        self.waitingForJoin()
        self.d_waitingForJoin()

    def setEnteredRacers(self, todo0):
        pass

    def d_prepForRace(self):
        self.sendUpdate('prepForRace', [])

    def b_prepForRace(self, avatars):
        self.prepForRace()
        self.d_prepForRace()

    def startTutorial(self):
        self.beginBarrier('readRules', self.avatars, 60, self.raceStart)

    def d_startTutorial(self):
        self.sendUpdate('startTutorial', [])

    def b_startTutorial(self, avatars):
        self.startTutorial()
        self.d_startTutorial()

    def startRace(self, timeUntilStart):
        taskMgr.doMethodLater(timeUntilStart, self.startKarts, 'startKarts%i' % self.doId, [])

    def startKarts(self):
        for avatarKart in self.avatarKarts:
            if avatarKart[1] in self.air.doId2do:
                kart = self.air.doId2do[avatarKart[1]]
                kart.sendUpdate('setInput', [1])
                self.avatarProgress[avatarKart[0]] = 0
                self.avatarGags[avatarKart[0]] = 0
                self.currentlyAffectedByAnvil[avatarKart[0]]  = False

    def b_startRace(self, timeUntilStart):
        self.startRace(timeUntilStart)
        self.d_startRace(timeUntilStart)

    def d_startRace(self, timeUntilStart):
        self.sendUpdate('startRace', [globalClockDelta.localToNetworkTime(globalClockDelta.globalClock.getRealTime() + timeUntilStart)])

    def goToSpeedway(self, todo0, todo1):
        pass

    def genGag(self, slot, number, type):
        self.gags[slot] = [number, type]

    def d_genGag(self, slot, number, type):
        self.sendUpdate('genGag', [slot, number, type])

    def b_genGag(self, slot, number, type):
        self.genGag(slot, number, type)
        self.d_genGag(slot, number, type)

    def dropAnvilOn(self, todo0, todo1, todo2):
        pass

    def shootPiejectile(self, todo0, todo1, todo2):
        pass

    def racerDisconnected(self, todo0):
        pass

    def setPlace(self, todo0, todo1, todo2, todo3, todo4, todo5, todo6, todo7, todo8, todo9):
        pass

    def setCircuitPlace(self, todo0, todo1, todo2, todo3, todo4, todo5):
        pass

    def endCircuitRace(self):
        pass

    def setRaceZone(self, todo0, todo1):
        pass

    def hasGag(self, slot, requestedGag, index):
        avId = self.air.getAvatarIdFromSender()
        if not avId in self.avatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to get gag in a race they\'re not in!')
            return
        if self.raceType == RaceGlobals.Practice:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to gain gag in a practice race!')
            return
        places = sorted(self.avatarProgress, key=self.avatarProgress.get)
        avPlace = places.index(avId)
        gag = self.gags[slot]
        if not gag[0]:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to pick up a gag that doesn\'t exist!')
            return
        gagIndex = gag[1]
        realGag = RaceGlobals.GagFreq[avPlace][gagIndex]
        if realGag != requestedGag:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to get the wrong gag!')
            return
        self.gags[slot] = [0, 0]
        self.avatarGags[avId] = requestedGag
        taskMgr.doMethodLater(5, self.__regenGag, 'regenGag%i-%i' % (slot, self.doId), [slot])

    def __regenGag(self, index):
        gagId = random.randint(0, 5)
        self.b_genGag(index, 1, gagId)

    def racerLeft(self, avId):
        realAvId = self.air.getAvatarIdFromSender()
        if realAvId != avId:
            self.air.writeServerEvent('suspicious', realAvId, 'Toon tried to make another quit race!')
            return
        if not avId in self.avatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to leave race they\'re not in!')
            return
        
        if self.circuitLoop and self.finishedAvatars:
            if avId in self.quitAvatars:
                return
            
            self.quitAvatars.append(avId)
            self.checkForNextRace()
        else:
            self.avatars.remove(avId)
            if avId in self.quitAvatars:
                self.quitAvatars.remove(avId)
            if set(self.finishedAvatars) == set(self.avatars) or len(self.avatars) == 0:
                self.requestDelete()
    
    def checkForNextRace(self):
        if len(self.quitAvatars) >= len(self.avatars):
            trackId = self.circuitLoop[0]
            self.nextRace = DistributedRaceAI(self.air, self.circuitPoints, self.circuitWinnings)
            self.nextRace.setZoneId(self.zoneId)
            self.nextRace.setTrackId(trackId)
            self.nextRace.setRaceType(self.raceType)
            self.nextRace.setAvatars(self.avatars)
            self.nextRace.setCircuitLoop(self.circuitLoop)
            self.nextRace.setStartingPlaces(range(len(self.avatars)))
            self.nextRace.setLapCount(3)
            taskMgr.doMethodLater(3, self.startNewRace, self.uniqueName('next-race'), extraArgs=[trackId])
    
    def startNewRace(self, trackId, task=None):
        self.nextRace.generateWithRequired(self.zoneId)
        self.sendUpdate('setRaceZone', [self.zoneId, trackId])

    def heresMyT(self, avId, laps, currentLapT, timestamp):
        realAvId = self.air.getAvatarIdFromSender()
        if not avId == realAvId:
            self.air.writeServerEvent('suspicious', realAvId, 'Toon tried to send a message as another toon!')
            return
        if not avId in self.avatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon not in race tried to send update to race!')
            return
        if laps == self.lapCount:
            self.avatarFinished(avId)
        self.avatarProgress[avId] = laps + currentLapT

    def avatarFinished(self, avId):
        if not avId in self.avatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to finish in a race they\'re not in!')
            return

        if avId in self.finishedAvatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to finish in a race twice!')
            return
        self.finishedAvatars.append(avId)

        av = self.air.doId2do.get(avId)
        place = len(self.finishedAvatars)
        listPlace = place + (4 - len(self.avatarProgress)) - 1
        entryFee = RaceGlobals.getEntryFee(self.trackId, self.raceType)
        bonus = 0
        totalTime = globalClockDelta.networkToLocalTime(globalClockDelta.getRealNetworkTime()) - self.startTime
        qualify = False
        if totalTime < RaceGlobals.getQualifyingTime(self.trackId):
            qualify = True
            self.air.leaderboardMgr.submitRace(self.trackId, av.getName(), totalTime)
        if self.raceType == RaceGlobals.Practice:
            winnings = RaceGlobals.PracticeWinnings
            trophies = []
        elif qualify:
            winnings = entryFee * RaceGlobals.Winnings[listPlace]
            trophies = self.calculateTrophies(avId, place == 1, qualify, totalTime)
        else:
            winnings = 0
            trophies = []
        av.b_setTickets(av.getTickets() + winnings)
        if av.getTickets() > RaceGlobals.MaxTickets:
            av.b_setTickets(RaceGlobals.MaxTickets)
        points = []
        if self.circuitPoints:
            avIndex = self.avatars.index(avId)
            points = self.circuitPoints[avIndex]
            points[0] += points[1]
            points[1] = RaceGlobals.CircuitPoints[place - 1]
        self.sendUpdate('setPlace', [avId, totalTime, place, entryFee, qualify, max((winnings-entryFee), 0), bonus, trophies, points, 0])
        if self.circuitPoints:
            self.circuitWinnings[avIndex] += winnings
            self.sendUpdate('setCircuitPlace', [avId, place, entryFee, self.circuitWinnings[avIndex], bonus, trophies])
            
            if len(self.finishedAvatars) == len(self.avatars):
                del self.circuitLoop[0]
                self.sendUpdate('setCircuitLoop', [self.circuitLoop])
                self.sendUpdate('endCircuitRace')

    def calculateTrophies(self, avId, won, qualify, time):
        av = self.air.doId2do[avId]
        kartingHistory = av.getKartingHistory()
        avTrophies = av.getKartingTrophies()
        numTrophies = 0
        for i in range(30):
            if avTrophies[i] != 0:
                numTrophies += 1
        oldLaffBoost = int(numTrophies/10)
        genre = RaceGlobals.getTrackGenre(self.trackId)
        trophies = []
        if won:
            kartingHistory[genre] += 1
            kartingHistory[3] += 1
            if kartingHistory[3] > RaceGlobals.TotalWonRaces:
                avTrophies[RaceGlobals.TotalWins] = 1
                trophies.append(RaceGlobals.TotalWins)
            for i in range(3):
                if kartingHistory[genre] >= RaceGlobals.WonRaces[i] and avTrophies[RaceGlobals.AllWinsList[genre][i]] != 1:
                    avTrophies[RaceGlobals.AllWinsList[genre][i]] = 1
                    trophies.append(RaceGlobals.AllWinsList[genre][i])
        if qualify:
            kartingHistory[genre + 4] += 1
            kartingHistory[7] += 1
            if kartingHistory[7] >= RaceGlobals.TotalQualifiedRaces and avTrophies[RaceGlobals.TotalQuals] != 1:
                avTrophies[RaceGlobals.TotalQuals] = 1
                trophies.append(RaceGlobals.TotalQuals)
            for i in range(3):
                if kartingHistory[genre + 4] >= RaceGlobals.QualifiedRaces[i] and avTrophies[RaceGlobals.AllQualsList[genre][i]] != 1:
                    avTrophies[RaceGlobals.AllQualsList[genre][i]] = 1
                    trophies.append(RaceGlobals.AllQualsList[genre][i])
        av.b_setKartingHistory(kartingHistory)
        pKartingBest = av.getKartingPersonalBestAll()
        trackIndex = TTLocalizer.KartRace_TrackNames.keys().index(self.trackId)
        if pKartingBest[trackIndex] > time or not pKartingBest[trackIndex]:
            pKartingBest[trackIndex] = time
            av.b_setKartingPersonalBest(pKartingBest)
        gTourTrophy = True
        for bestTime in pKartingBest:
            if not bestTime:
                gTourTrophy = False
        if gTourTrophy:
            if avTrophies[RaceGlobals.GrandTouring] != 1:
                avTrophies[RaceGlobals.GrandTouring] = 1
                trophies.append(RaceGlobals.GrandTouring)
        newLaffBoost = int((len(trophies) + numTrophies)/10)
        if newLaffBoost - oldLaffBoost != 0:
            for i in range(newLaffBoost):
                if avTrophies[RaceGlobals.TrophyCups[i]] != 1:
                    avTrophies[RaceGlobals.TrophyCups[i]] = 1
                    trophies.append(RaceGlobals.TrophyCups[i])
            av.b_setMaxHp(av.getMaxHp() + newLaffBoost - oldLaffBoost)
            av.toonUp(av.getMaxHp())
        av.b_setKartingTrophies(avTrophies)
        return trophies

    def requestThrow(self, x, y, z):
        avId = self.air.getAvatarIdFromSender()
        if not avId in self.avatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to throw a gag in a race they\'re not in!')
        if self.avatarGags[avId] == RaceGlobals.BANANA:
            gag = DistributedGagAI(self.air)
            gag.setRace(self.doId)
            gag.setOwnerId(avId)
            gag.setPos(x, y, z)
            gag.setType(0)
            gag.setInitTime(globalClockDelta.getRealNetworkTime())
            gag.setActivateTime(globalClockDelta.getRealNetworkTime())
            gag.generateWithRequired(self.zoneId)
            self.livingGags.append(gag)
        elif self.avatarGags[avId] == RaceGlobals.TURBO:
            pass
        elif self.avatarGags[avId] == RaceGlobals.ANVIL:
            places = sorted(self.avatarProgress, key=self.avatarProgress.get, reverse=True)
            for i in places:
                if not i in self.finishedAvatars and not self.currentlyAffectedByAnvil[i]:
                    currAvatar = i
                    break
            self.currentlyAffectedByAnvil[avId] = True
            taskMgr.doMethodLater(RaceGlobals.AnvilSquishDuration, self.unsquish, 'unsquish-%i' % currAvatar, [currAvatar])
            self.sendUpdate('dropAnvilOn', [avId, currAvatar, globalClockDelta.getRealNetworkTime()])
        elif self.avatarGags[avId] == RaceGlobals.PIE:
            places = sorted(self.avatarProgress, key=self.avatarProgress.get)
            avPlace = places.index(avId)
            if avPlace + 1 == len(places):
                target = 0
            else:
                target = places[avPlace + 1]
            self.sendUpdate('shootPiejectile', [avId, target, 0])
        else:
            self.air.writeServerEvent('suspicious', avId, 'Toon use race gag while not having one!')
        self.avatarGags[avId] = 0

    def unsquish(self, avId):
        self.currentlyAffectedByAnvil[avId] = False

    def playerLeave(self, avId):
        self.sendUpdate('racerDisconnected', [avId])
        if avId in self.avatars:
            self.avatars.remove(avId)
        count = 0
        for aK in self.avatarKarts:
            if aK[0] == avId and aK[1] in self.air.doId2do:
                self.air.doId2do[aK[1]].handleUnexpectedExit()
                del self.avatarKarts[count]
                break
            count += 1
        if len(self.avatars) == 0:
            self.requestDelete()
        else:
            self.checkForNextRace()

    def requestKart(self):
        pass
        avId = self.air.getAvatarIdFromSender()
        accId = self.air.getAccountIdFromSender()
        if not avId in self.avatars:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to request kart in race they\'re not in!')
            return
        for aK in self.avatarKarts:
            if aK[0] == avId:
                self.air.doId2do[aK[1]].request('Controlled', avId, accId)
                self.air.doId2do[aK[1]].sendUpdate('setInput', [0])
