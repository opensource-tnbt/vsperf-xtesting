#!/usr/bin/env python

# pylint: disable=missing-docstring
import json
import os
import sys
import time

from xtesting.core import testcase
from vsperf_controller.py as vsc

class VsperfXt(testcase.Testcase):

    def run(self, **kwargs):
        vcontroller = vsc.VsperfController()
        try:
            self.start_time = time.time()
            os.environ("VSPERF_TEST")=self.case_name
            os.makedirs(self.res_dir, exist_ok=True)
            # This will run the actual test
            vcontroller.run()
            # This will bring all the results to results folder.
            vcontroller.get_results(self.res_dir)
            self.stop_time = time.time()
        except Exception:  # pylint: disable=broad-except
            print("Unexpected error:", sys.exc_info()[0])
            self.result = 0
            self.stop_time = time.time()
