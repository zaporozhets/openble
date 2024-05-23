# 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

import itertools
import logging
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from cocotbext.axi import AxiStreamFrame, AxiStreamBus, AxiStreamSource, AxiStreamSink

from helpers import setup_test, rtl_dir, BlePhy

class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)
        cocotb.start_soon(Clock(dut.aclk, 2, units="ns").start())

        self.source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "input"), dut.aclk, dut.aresetn, False, byte_lanes=1)
        self.sink = AxiStreamSink(AxiStreamBus.from_prefix(dut, "output"), dut.aclk, dut.aresetn, False, byte_lanes=1)

    async def reset(self):
        self.dut.aresetn.setimmediatevalue(0)
        await RisingEdge(self.dut.aclk)
        await RisingEdge(self.dut.aclk)
        self.dut.aresetn.value = 0
        await RisingEdge(self.dut.aclk)
        await RisingEdge(self.dut.aclk)
        self.dut.aresetn.value = 1
        await RisingEdge(self.dut.aclk)
        await RisingEdge(self.dut.aclk)


def idle_cycle_pause():
    return itertools.cycle([1, 1, 1, 1, 0])

def backpressure_cycle_pause():
    return itertools.cycle([1, 1, 1, 1, 1, 0])



async def generate_and_compare(dut, phy: BlePhy , input_data, expected_output_data):
    tb = TB(dut)
    await tb.reset()

    expected_output_data = bytes(expected_output_data)

    dut.phy.value = phy.value

    dut.restart.value = 1
    await RisingEdge(dut.aclk)
    dut.restart.value = 0
    await RisingEdge(dut.aclk)

    test_frame = AxiStreamFrame(input_data)
    await tb.source.send(test_frame)

    output_data = bytes(await tb.sink.recv())

    assert tb.sink.empty()
    assert output_data == expected_output_data

@cocotb.test()
async def run_test_1phy_55(dut):
    input_data = [
        # Access address
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    expected_output_data = [
        # Preamble
        0,1,0,1,0,1,0,1,
        # Access address
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    await generate_and_compare(dut, BlePhy.BLE_PHY_1M, input_data, expected_output_data)

@cocotb.test()
async def run_test_1phy_aa(dut):
    input_data = [
        # Access address
        1, 1, 1, 1, 1, 1, 1, 1,
    ]

    expected_output_data = [
        # Preamble
        1,0,1,0,1,0,1,0,
        # Access address
        1, 1, 1, 1, 1, 1, 1, 1,
    ]

    await generate_and_compare(dut, BlePhy.BLE_PHY_1M, input_data, expected_output_data)

@cocotb.test()
async def run_test_2phy_5555(dut):
    input_data = [
        # Access address
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    expected_output_data = [
        # Preamble
        0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,
        # Access address
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    await generate_and_compare(dut, BlePhy.BLE_PHY_2M, input_data, expected_output_data)

@cocotb.test()
async def run_test_2phy_aaaa(dut):
    input_data = [
        # Access address
        1, 1, 1, 1, 1, 1, 1, 1,
    ]

    expected_output_data = [
        # Preamble
        1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,
        # Access address
        1, 1, 1, 1, 1, 1, 1, 1,
    ]

    await generate_and_compare(dut, BlePhy.BLE_PHY_2M, input_data, expected_output_data)

@cocotb.test()
async def run_test_coded_phy(dut):
    input_data = [
        # Access address
        1, 1, 1, 1, 1, 1, 1, 1,
    ]

    expected_output_data = [
        # # Preamble
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        # Access address
        1, 1, 1, 1, 1, 1, 1, 1,

    ]

    await generate_and_compare(dut, BlePhy.BLE_PHY_CODED, input_data, expected_output_data)

def test_preamble_generator():
    setup_test(
        "test_preamble_generator",
        "preamble_generator",
        [
            os.path.join(rtl_dir, "tx/preamble_generator.sv"),
        ]
    )
