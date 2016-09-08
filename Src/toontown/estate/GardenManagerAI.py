from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.distributed.PyDatagram import PyDatagram

from toontown.toonbase.ToontownBattleGlobals import NUM_GAG_TRACKS
from toontown.estate.DistributedGardenPlotAI import DistributedGardenPlotAI
from toontown.estate.DistributedGagTreeAI import DistributedGagTreeAI
from toontown.estate import GardenGlobals

from time import time

occupier2Class = {
    GardenGlobals.EmptyPlot: DistributedGardenPlotAI,
    GardenGlobals.TreePlot: DistributedGagTreeAI
}


class GardenManagerAI:
    notify = directNotify.newCategory('GardenManagerAI')

    def __init__(self, air, house):
        self.air = air
        self.house = house

        self.plots = []

    def loadGarden(self):
        if not self.house.hasGardenData():
            pass

        #self.createGardenFromData(self.house.getGardenData())
        self.giveOrganicBonus()

    def createBlankGarden(self):
        pass


    def createGardenFromData(self, gardenData):
        pass

    def updateGardenData(self):
        gardenData = PyDatagram()

        gardenData.addUint8(len(self.plots))
        for plot in self.plots:
            plot.pack(gardenData)

        self.house.b_setGardenData(gardenData.getMessage())

    def delete(self):
        for plot in self.plots:
            plot.requestDelete()

    def getTimestamp(self):
        return int(time())

    def constructTree(self, plotIndex, gagTrack, gagLevel):
        dg = PyDatagram()
        dg.addUint8(plotIndex)
        dg.addUint8(GardenGlobals.getTreeTypeIndex(gagTrack, gagLevel))  # Type Index
        dg.addInt8(0)  # Water Level
        dg.addInt8(0)  # Growth Level
        dg.addUint32(self.getTimestamp())
        dg.addUint8(0)  # Wilted State (False)
        gardenData = PyDatagramIterator(dg)

        plot = occupier2Class[GardenGlobals.TreePlot](self.air, self, self.house.housePos)
        plot.construct(gardenData)
        self.plots[plotIndex] = plot

        self.updateGardenData()

    def treeFinished(self, plotIndex):
        tree = self.plots[plotIndex]
        tree.generateWithRequired(self.house.zoneId)
        tree.setMovie(GardenGlobals.MOVIE_FINISHPLANTING, self.air.getAvatarIdFromSender())
        self.givePlantingSkill(self.air.getAvatarIdFromSender(), tree.gagLevel)

    def revertToPlot(self, plotIndex):
        dg = PyDatagram()
        dg.addUint8(plotIndex)
        gardenData = PyDatagramIterator(dg)

        plot = occupier2Class[GardenGlobals.EmptyPlot](self.air, self, self.house.housePos)
        plot.construct(gardenData)
        self.plots[plotIndex] = plot

        self.updateGardenData()

    def removeFinished(self, plotIndex):
        plot = self.plots[plotIndex]
        plot.generateWithRequired(self.house.zoneId)
        plot.setMovie(GardenGlobals.MOVIE_PLANT_REJECTED, self.air.getAvatarIdFromSender())

    def givePlantingSkill(self, avId, gagLevel):
        av = self.air.doId2do.get(avId)
        if not av:
            return
        currSkill = av.getShovelSkill()
        av.b_setShovelSkill(currSkill + 1 + gagLevel)

    def giveOrganicBonus(self):
        av = self.air.doId2do.get(self.house.avatarId)
        if not av:
            return
        trackBonus = [-1] * NUM_GAG_TRACKS
        treesGrown = {i: [] for i in xrange(NUM_GAG_TRACKS)}

        # Get all the trees that can give organic bonus.
        for plot in self.plots:
            if isinstance(plot, DistributedGagTreeAI):
                if plot.canGiveOrganic():
                    treesGrown[plot.gagTrack].append(plot.gagLevel)

        # Check if we have all previous trees for that track to give the bonus.
        def verify(l):
            if not max(l) == len(l) - 1:
                l.remove(max(l))
                if not l:
                    return
                verify(l)

        for level in treesGrown:
            if not treesGrown[level]:
                continue

            verify(treesGrown[level])

            if not treesGrown[level]:
                continue
            trackBonus[level] = max(treesGrown[level])

        av.b_setTrackBonusLevel(trackBonus)
