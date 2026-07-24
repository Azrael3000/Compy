"""Tests for the scoring rules: points per discipline, cards, DNS and
under-AP penalties. These decide who wins a competition, so they are the
most critical pure logic in the application."""
import unittest

import compy_testing


class TestAidaPoints(compy_testing.CompyDataTestCase):

    def setUp(self):
        super().setUp()
        self.data = self.newData()

    def testDepthDisciplineOnePointPerMeter(self):
        self.assertEqual(self.data.computePoints(52, 0., "WHITE", "", "CWT"), 52.)

    def testDepthDisciplinePenaltyIsSubtracted(self):
        self.assertEqual(self.data.computePoints(52, 3., "YELLOW", "", "CWT"), 49.)

    def testStaticFifthOfAPointPerSecond(self):
        # 2:05 = 125 s -> 25 points
        self.assertEqual(self.data.computePoints(125, 0., "WHITE", "", "STA"), 25.)

    def testDynamicHalfAPointPerMeter(self):
        self.assertEqual(self.data.computePoints(100, 0., "WHITE", "", "DYN"), 50.)

    def testRedCardGivesZeroPoints(self):
        self.assertEqual(self.data.computePoints(100, 0., "RED", "", "CWT"), 0.)

    def testDnsGivesZeroPoints(self):
        self.assertEqual(self.data.computePoints(None, 0., "WHITE", "DNS", "CWT"), 0.)

    def testMissingRpGivesZeroPoints(self):
        self.assertEqual(self.data.computePoints(None, 0., "WHITE", "", "CWT"), 0.)

    def testPenaltyCanNotMakePointsNegative(self):
        self.assertEqual(self.data.computePoints(10, 99., "YELLOW", "", "CWT"), 0.)


class TestCmasPoints(compy_testing.CompyDataTestCase):

    def setUp(self):
        super().setUp()
        self.data = self.newData()
        # switch scoring rules without persisting a competition
        self.data.comp_type_ = "cmas"

    def testDynamicQuarterPointPerHalfMeter(self):
        # 103.5 m -> 207 half meters -> 51.75 points
        self.assertEqual(self.data.computePoints(103.5, 0., "WHITE", "", "DYN"), 51.75)

    def testStaticSameAsAida(self):
        self.assertEqual(self.data.computePoints(125, 0., "WHITE", "", "STA"), 25.)


class TestUnderApPenalty(compy_testing.CompyDataTestCase):

    def setUp(self):
        super().setUp()
        self.data = self.newData()

    def testOnlyYellowCardGetsUnderApPenalty(self):
        self.assertEqual(self.data.getUnderApPenalty(50, 45, "CWT", "WHITE"), 0)
        self.assertEqual(self.data.getUnderApPenalty(50, 45, "CWT", "RED"), 0)

    def testDepthOnePointPerMissingMeter(self):
        self.assertEqual(self.data.getUnderApPenalty(50, 45, "CWT", "YELLOW"), 5.)

    def testDynamicHalfAPointPerMissingMeter(self):
        self.assertEqual(self.data.getUnderApPenalty(100, 90, "DYN", "YELLOW"), 5.)

    def testStaticFifthOfAPointPerMissingSecond(self):
        self.assertEqual(self.data.getUnderApPenalty(150, 130, "STA", "YELLOW"), 4.)

    def testReachedApGetsNoPenalty(self):
        self.assertEqual(self.data.getUnderApPenalty(50, 50, "CWT", "YELLOW"), 0.)
        self.assertEqual(self.data.getUnderApPenalty(50, 55, "CWT", "YELLOW"), 0.)

    def testPenaltyIsRoundedToOneDecimal(self):
        self.assertEqual(self.data.getUnderApPenalty(150, 129, "STA", "YELLOW"), 4.2)


if __name__ == '__main__':
    unittest.main()
