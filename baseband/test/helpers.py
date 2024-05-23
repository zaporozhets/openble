#!/usr/bin/env python

# 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

from enum import Enum

import os
import cocotb_test.simulator

tests_dir = os.path.dirname(__file__)
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'rtl'))
sim_dir = os.path.abspath(os.path.join(tests_dir, '..', 'sim'))
def setup_test(module, toplevel, verilog_sources):

    sim_build = os.path.join("sim_build", module)

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        sim_build=sim_build,
        includes=[rtl_dir]
    )

class ble_phy_t(Enum):
    BlePhy1M      = 0
    BlePhy2M      = 1
    BlePhyCoded   = 2

class ble_ci_t(Enum):
    BleCiS8 = 0
    BleCiS2 = 1


