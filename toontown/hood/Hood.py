from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase.ToontownGlobals import *
from toontown.distributed.ToontownMsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from toontown.minigame import Purchase
from direct.gui import OnscreenText
from toontown.building import SuitInterior
import QuietZoneState
import ZoneUtil
from toontown.toonbase import TTLocalizer
from toontown.toon.Toon import teleportDebug
from toontown.dna.DNAParser import *

class Hood(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('Hood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        StateData.StateData.__init__(self, doneEvent)
        self.loader = 'not initialized'
        self.parentFSM = parentFSM
        self.dnaStore = dnaStore
        self.loaderDoneEvent = 'loaderDone'
        self.id = None
        self.hoodId = hoodId
        self.titleText = None
        self.titleColor = (1, 1, 1, 1)
        self.holidayStorageDNADict = {}
        self.spookySkyFiles = None
        self.snowySkyFile = 'phase_3.5/models/props/BR_sky'
        self.mmlSkyFile = 'phase_6/models/props/MM_sky'
        self.daySkyFile = 'phase_3.5/models/props/TT_sky'
        self.nightSkyFile = 'phase_8/models/props/DL_sky'
        self.oldSky = None
        self.newSky = None
        self.halloweenLights = []
        return

    def enter(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        hoodText = self.getHoodText(zoneId)
        self.titleText = OnscreenText.OnscreenText(hoodText, fg=self.titleColor, font=getSignFont(), pos=(0, -0.5), scale=TTLocalizer.HtitleText, drawOrder=0, mayChange=1)
        self.fsm.request(requestStatus['loader'], [requestStatus])

    def getHoodText(self, zoneId):
        hoodText = base.cr.hoodMgr.getFullnameFromId(self.id)
        if self.id != Tutorial:
            streetName = StreetNames.get(ZoneUtil.getCanonicalBranchZone(zoneId))
            if streetName:
                hoodText = hoodText + '\n' + streetName[-1]
        return hoodText

    def spawnTitleText(self, zoneId):
        hoodText = self.getHoodText(zoneId)
        self.doSpawnTitleText(hoodText)

    def doSpawnTitleText(self, text):
        self.titleText.setText(text)
        self.titleText.show()
        self.titleText.setColor(Vec4(*self.titleColor))
        self.titleText.clearColorScale()
        self.titleText.setFg(self.titleColor)
        seq = Sequence(Wait(0.1), Wait(6.0), self.titleText.colorScaleInterval(0.5, Vec4(1.0, 1.0, 1.0, 0.0)), Func(self.titleText.hide))
        seq.start()

    def hideTitleText(self):
        if self.titleText:
            self.titleText.hide()

    def exit(self):
        taskMgr.remove('titleText')
        if self.titleText:
            self.titleText.cleanup()
            self.titleText = None
        base.localAvatar.stopChat()
        return

    def load(self):
        if self.storageDNAFile:
            loader.loadDNA(self.storageDNAFile).store(self.dnaStore)
        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            for holiday in holidayIds:
                for storageFile in self.holidayStorageDNADict.get(holiday, []):
                    loader.loadDNA(storageFile).store(self.dnaStore)

            if ToontownGlobals.HALLOWEEN_COSTUMES not in holidayIds and ToontownGlobals.SPOOKY_COSTUMES not in holidayIds or not self.spookySkyFile:
                self.sky = loader.loadModel(self.skyFile)
                self.sky.setTag('sky', 'Regular')
                self.sky.setScale(1.0)
                self.sky.setFogOff()
            else:
                self.sky = loader.loadModel(self.spookySkyFile)
                self.sky.setTag('sky', 'Halloween')
        if not newsManager:
            self.sky = loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.sky.setFogOff()

    def unload(self):
        if hasattr(self, 'loader'):
            self.notify.info('Aggressively cleaning up loader: %s' % self.loader)
            self.loader.exit()
            self.loader.unload()
            del self.loader
        del self.fsm
        del self.parentFSM
        self.dnaStore.reset(scope='hood')
        del self.dnaStore
        #self.sky.removeNode()
        del self.sky
        self.ignoreAll()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def isSameHood(self, status):
        return status['hoodId'] == self.hoodId and status['shardId'] == None

    def enterFinal(self):
        pass

    def exitFinal(self):
        pass

    def enterQuietZone(self, requestStatus):
        teleportDebug(requestStatus, 'Hood.enterQuietZone: status=%s' % requestStatus)
        self._quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self._quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self._quietZoneDoneEvent)
        self._enterWaitForSetZoneResponseMsg = self.quietZoneStateData.getEnterWaitForSetZoneResponseMsg()
        self.acceptOnce(self._enterWaitForSetZoneResponseMsg, self.handleWaitForSetZoneResponse)
        self._quietZoneLeftEvent = self.quietZoneStateData.getQuietZoneLeftEvent()
        if base.placeBeforeObjects:
            self.acceptOnce(self._quietZoneLeftEvent, self.handleLeftQuietZone)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self._quietZoneDoneEvent)
        self.ignore(self._quietZoneLeftEvent)
        self.ignore(self._enterWaitForSetZoneResponseMsg)
        del self._quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None
        return

    def loadLoader(self, requestStatus):
        pass

    def handleWaitForSetZoneResponse(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'safeZoneLoader':
            if not loader.inBulkBlock:
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToPlayground, safeZoneCountMap[self.id], 1, TTLocalizer.TIP_GENERAL, 0)
            self.loadLoader(requestStatus)
            loader.endBulkLoad('hood')
        elif loaderName == 'townLoader':
            if not loader.inBulkBlock:
                zoneId = requestStatus['zoneId']
                toPhrase = StreetNames[ZoneUtil.getCanonicalBranchZone(zoneId)][0]
                streetName = StreetNames[ZoneUtil.getCanonicalBranchZone(zoneId)][-1]
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToStreet % {'to': toPhrase,
                 'street': streetName}, townCountMap[self.id], 1, TTLocalizer.TIP_STREET, 0)
            self.loadLoader(requestStatus)
            loader.endBulkLoad('hood')
        elif loaderName == 'minigame':
            pass
        elif loaderName == 'cogHQLoader':
            print 'should be loading HQ'

    def handleLeftQuietZone(self):
        status = self.quietZoneStateData.getRequestStatus()
        teleportDebug(status, 'handleLeftQuietZone, status=%s' % status)
        teleportDebug(status, 'requesting %s' % status['loader'])
        self.fsm.request(status['loader'], [status])

    def handleQuietZoneDone(self):
        if not base.placeBeforeObjects:
            status = self.quietZoneStateData.getRequestStatus()
            self.fsm.request(status['loader'], [status])

    def enterSafeZoneLoader(self, requestStatus):
        self.accept(self.loaderDoneEvent, self.handleSafeZoneLoaderDone)
        self.loader.enter(requestStatus)
        self.spawnTitleText(requestStatus['zoneId'])

    def exitSafeZoneLoader(self):
        taskMgr.remove('titleText')
        self.hideTitleText()
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleSafeZoneLoaderDone(self):
        doneStatus = self.loader.getDoneStatus()
        teleportDebug(doneStatus, 'handleSafeZoneLoaderDone, doneStatus=%s' % doneStatus)
        if self.isSameHood(doneStatus) and doneStatus['where'] != 'party' or doneStatus['loader'] == 'minigame':
            teleportDebug(doneStatus, 'same hood')
            self.fsm.request('quietZone', [doneStatus])
        else:
            teleportDebug(doneStatus, 'different hood')
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def startSky(self):
        self.sky.reparentTo(camera)
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def stopSky(self):
        taskMgr.remove('skyTrack')
        if self.sky:
            self.sky.reparentTo(hidden)

    def startSpookySky(self):
        if not self.spookySkyFile:
            return
        if hasattr(self, 'sky') and self.sky:
            self.stopSky()
        self.sky = loader.loadModel(self.spookySkyFile)
        self.sky.setTag('sky', 'Halloween')
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def endSpookySky(self):
        if hasattr(self, 'sky') and self.sky:
            self.sky.reparentTo(hidden)
        if hasattr(self, 'sky'):
            self.sky = loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.startSky()

    def startSnowySky(self):
        if hasattr(self, 'sky') and self.sky:
            self.stopSky()
        self.sky = loader.loadModel(self.snowySkyFile)
        self.sky.setTag('sky', 'Winter')
        self.sky.setScale(1.0)
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(1, 1, 1, 1)
        self.sky.setBin('background', 100)
        self.sky.setFogOff()
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def endSnowySky(self):
        if hasattr(self, 'sky') and self.sky:
            self.sky.reparentTo(hidden)
        if hasattr(self, 'sky'):
            self.sky = loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.startSky()

    def end(self):
        self.sky = self.newSky
        self.oldSky = None
        self.newSky = None

    def skyTransition(self, sky):
        if self.id != DonaldsDreamland or self.id != DonaldsDock or self.id != TheBrrrgh:
            self.oldSky = self.sky
            if sky == 'mml':
                self.newSky = loader.loadModel(self.mmlSkyFile)
                self.newSky.setTag('sky', 'MML')
            if sky == 'day':
                self.newSky = loader.loadModel(self.daySkyFile)
                self.newSky.setTag('sky', 'Day')
            if sky == 'night':
                self.newSky = loader.loadModel(self.nightSkyFile)
                self.newSky.setTag('sky', 'Night')
            if sky == 'rain':
                self.newSky = loader.loadModel(self.snowySkyFile)
                self.newSky.setTag('sky', 'Rain')
            if self.oldSky:
                self.oldSky.setTransparency(TransparencyAttrib.MDual, 1)
            if self.newSky:
                self.newSky.setTransparency(TransparencyAttrib.MDual, 1)
                self.newSky.setScale(1.0)
                self.newSky.setDepthTest(0)
                self.newSky.setDepthWrite(0)
                self.newSky.setColorScale(1, 1, 1, 0)
                self.newSky.setBin('background', 100)
                self.newSky.setFogOff()
                self.newSky.setZ(0.0)
                self.newSky.setHpr(0.0, 0.0, 0.0)
                ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
                self.newSky.node().setEffect(ce)
                self.newSky.reparentTo(camera)
                newFadeIn = LerpColorScaleInterval(self.newSky, 5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0), blendType='easeInOut')
                if self.oldSky:
                    oldFadeOut = LerpColorScaleInterval(self.oldSky, 5, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='easeInOut')
                else:
                    oldFadeOut = Wait(0) # Just do that to please the sequence so it doesnt crash
                Sequence(
                    Parallel(
                        newFadeIn,
                        oldFadeOut
                    ),
                    Func(self.oldSky.reparentTo, hidden),
                    Func(self.end)
                ).start()