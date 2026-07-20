"""Tests for judge management and the QR-code hash authentication that
protects the judge pages. A forged hash must be rejected without touching
any state."""
import unittest

import compy_testing


class TestJudgeAuthentication(compy_testing.CompyDataTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.app.app_context():
            import compy_data
            data = compy_data.CompyData(cls.db, cls.app)
            data.changeName("Judge Test Open", False)
            cls.comp_id = data.id_
            data.addJudge("Judy", "Judge")
            judges = {}
            data.getJudgeData(judges)
            cls.judge_id = judges["judges"][0]["id"]

    def setUp(self):
        super().setUp()
        self.data = self.newData(self.comp_id)

    def fetchJudgeHash(self):
        qr_code, first_name, last_name, judge_url = self.data.getJudgeQrCode(
            self.judge_id, "http://localhost:5000/")
        self.assertEqual((first_name, last_name), ("Judy", "Judge"))
        self.assertTrue(qr_code.startswith("data:image/png;base64,"))
        return judge_url.split("hash=")[1]

    def testDuplicateJudgeIsRejected(self):
        self.assertEqual(self.data.addJudge("Judy", "Judge"), 1)

    def testValidHashIsAccepted(self):
        judge_hash = self.fetchJudgeHash()
        validator = self.newData()

        ret, content = validator.getCompDataAndValidateJudge(
            self.comp_id, self.judge_id, judge_hash)

        self.assertEqual(ret, 0)
        self.assertEqual(content["comp_name"], "Judge Test Open")
        self.assertEqual(content["first_name"], "Judy")
        self.assertEqual(validator.id_, self.comp_id)

    def testForgedHashIsRejectedWithoutSideEffects(self):
        validator = self.newData()

        ret, content = validator.getCompDataAndValidateJudge(
            self.comp_id, self.judge_id, "deadbeef")

        self.assertEqual(ret, -1)
        self.assertIsNone(content)
        # a failed validation must not leave the competition id behind
        self.assertIsNone(validator.id_)

    def testHashOfOtherCompetitionIsRejected(self):
        judge_hash = self.fetchJudgeHash()
        validator = self.newData()

        # comp 1 is the default competition, the judge belongs to comp_id
        ret, content = validator.getCompDataAndValidateJudge(
            1, self.judge_id, judge_hash)

        self.assertEqual(ret, -1)

    def testNonAlphanumericHashIsRejected(self):
        validator = self.newData()
        ret, content = validator.getCompDataAndValidateJudge(
            self.comp_id, self.judge_id, "'; DROP TABLE judge; --")
        self.assertEqual(ret, -1)

    def testJudgeNotInOtherCompetition(self):
        other_comp = self.newData(1)
        self.assertIsNone(other_comp.isJudgeInCompetition(self.judge_id))

    def testDeleteJudge(self):
        self.data.addJudge("Temp", "Judge")
        judges = {}
        self.data.getJudgeData(judges)
        temp_judge = [judge for judge in judges["judges"]
                      if judge["first_name"] == "Temp"][0]

        self.data.deleteJudge(temp_judge["id"])

        judges_after = {}
        self.data.getJudgeData(judges_after)
        names_after = [judge["first_name"] for judge in judges_after["judges"]]
        self.assertNotIn("Temp", names_after)


if __name__ == '__main__':
    unittest.main()
