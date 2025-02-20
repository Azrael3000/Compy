import unittest

import compy_utilities as u

class TestCompyUtilities(unittest.TestCase):
    def testconvDay_InputInteger_OutputString(self):
        day = 20100312

        day_str = u.convDay(day)

        self.assertEqual(day_str, "2010-03-12")

    def testconvDay_InputString_OutputInteger(self):
        day = "2010-03-12"

        day_int = u.convDay(day)

        self.assertEqual(day_int, 20100312)

    def testconvDay_InputEmptyString_OutputNone(self):
        day = ""

        ret = u.convDay(day)

        self.assertEqual(ret, None)
