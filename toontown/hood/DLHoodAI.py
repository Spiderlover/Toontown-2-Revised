from toontown.toonbase import ToontownGlobals
from SZHoodAI import SZHoodAI
from toontown.toon import NPCToons
from toontown.ai import DistributedTrickOrTreatTargetAI
from toontown.ai import DistributedResistanceEmoteMgrAI
from toontown.ai import DistributedWinterCarolingTargetAI
from toontown.ai import HolidayGlobals
class DLHoodAI(SZHoodAI):
    notify = directNotify.newCategory('SZHoodAI')
    notify.setInfo(True)
    HOOD = ToontownGlobals.DonaldsDreamland

    def createZone(self):
        self.notify.info("Creating zone... Donald's Dreamland")

        SZHoodAI.createZone(self)
        self.spawnObjects()

        if HolidayGlobals.WhatHolidayIsIt() == 'Winter':
            self.WinterCarolingTargetManager = DistributedWinterCarolingTargetAI.DistributedWinterCarolingTargetAI(self.air)
            self.WinterCarolingTargetManager.generateWithRequired(9720)


            self.WinterCarolingTargetManager = DistributedWinterCarolingTargetAI.DistributedWinterCarolingTargetAI(self.air)
            self.WinterCarolingTargetManager.generateWithRequired(9720)

        if HolidayGlobals.WhatHolidayIsIt() == 'Halloween':
            self.TrickOrTreatTargetManager = DistributedTrickOrTreatTargetAI.DistributedTrickOrTreatTargetAI(self.air)
            self.TrickOrTreatTargetManager.generateWithRequired(9619)


            self.TrickOrTreatTargetManager = DistributedTrickOrTreatTargetAI.DistributedTrickOrTreatTargetAI(self.air)
            self.TrickOrTreatTargetManager.generateWithRequired(9619)
