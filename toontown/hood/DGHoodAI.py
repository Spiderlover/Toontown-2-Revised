from toontown.toonbase import ToontownGlobals
from toontown.safezone.DistributedDGFlowerAI import DistributedDGFlowerAI
from SZHoodAI import SZHoodAI
from toontown.toon import NPCToons
from toontown.safezone import ButterflyGlobals
from toontown.safezone.DistributedButterflyAI import DistributedButterflyAI
from toontown.ai import DistributedTrickOrTreatTargetAI
from toontown.ai import DistributedWinterCarolingTargetAI
from toontown.ai import HolidayGlobals

class DGHoodAI(SZHoodAI):
    notify = directNotify.newCategory('SZHoodAI')
    notify.setInfo(True)
    HOOD = ToontownGlobals.DaisyGardens

    def createZone(self):
        self.notify.info("Creating zone... Daisy Gardens")
        SZHoodAI.createZone(self)
        self.butterflies = []

        self.spawnObjects()

        self.flower = DistributedDGFlowerAI(self.air)
        self.flower.generateWithRequired(self.HOOD)
        self.createButterflies()

        if HolidayGlobals.WhatHolidayIsIt() == 'Winter':
            self.WinterCarolingTargetManager = DistributedWinterCarolingTargetAI.DistributedWinterCarolingTargetAI(self.air)
            self.WinterCarolingTargetManager.generateWithRequired(5626)
            
            self.WinterCarolingTargetManager = DistributedWinterCarolingTargetAI.DistributedWinterCarolingTargetAI(self.air)
            self.WinterCarolingTargetManager.generateWithRequired(5626)

        elif HolidayGlobals.WhatHolidayIsIt() == 'Halloween':
            self.TrickOrTreatTargetManager = DistributedTrickOrTreatTargetAI.DistributedTrickOrTreatTargetAI(self.air)
            self.TrickOrTreatTargetManager.generateWithRequired(5620)

            self.TrickOrTreatTargetManager = DistributedTrickOrTreatTargetAI.DistributedTrickOrTreatTargetAI(self.air)
            self.TrickOrTreatTargetManager.generateWithRequired(5620)

    def createButterflies(self):
        playground = ButterflyGlobals.DG
        for area in range(ButterflyGlobals.NUM_BUTTERFLY_AREAS[playground]):
            for b in range(ButterflyGlobals.NUM_BUTTERFLIES[playground]):
                butterfly = DistributedButterflyAI(self.air)
                butterfly.setArea(playground, area)
                butterfly.setState(0, 0, 0, 1, 1)
                butterfly.generateWithRequired(self.HOOD)
                self.butterflies.append(butterfly)
