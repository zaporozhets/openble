"""Module with helper functions for the baseband tests."""

from enum import Enum
import os
import cocotb_test.simulator

tests_dir = os.path.dirname(__file__)
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'rtl'))
sim_dir = os.path.abspath(os.path.join(tests_dir, '..', 'sim'))

def setup_test(module, toplevel, verilog_sources):
    """
    Set up the test environment for the given module.

    Args:
        module (str): Name of the module.
        toplevel (str): Name of the top-level module.
        verilog_sources (list): List of Verilog source files.

    Returns:
        None
    """
    sim_build = os.path.join("sim_build", module)

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        sim_build=sim_build,
        includes=[rtl_dir]
    )

class BlePhy(Enum):
    """Enumeration for BLE PHY types."""
    BLE_PHY_1M = 0
    BLE_PHY_2M = 1
    BLE_PHY_CODED = 2

class BleCi(Enum):
    """Enumeration for bluetooth coding indicator types."""
    BLE_CI_S8 = 0
    BLE_CI_S2 = 1
