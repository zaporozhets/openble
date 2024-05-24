#!/usr/bin/env python

import itertools
import logging
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from cocotbext.axi import AxiStreamFrame, AxiStreamBus, AxiStreamSource, AxiStreamSink

from helpers import setup_test, rtl_dir

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



async def generate_and_compare(dut, access_code , input_data, expected_output_data):
    tb = TB(dut)
    await tb.reset()

    expected_output_data = bytes(expected_output_data)

    dut.access_code.value = access_code
    dut.restart.value = 1
    await RisingEdge(dut.aclk)
    dut.restart.value = 0
    await RisingEdge(dut.aclk)

    test_frame = AxiStreamFrame(input_data)
    await tb.source.send(test_frame)

    output_data = bytes(await tb.sink.recv())

    assert tb.sink.empty()
    assert output_data == expected_output_data

async def run_test(dut):

    input_data = [
        # PDU: 00 03 42 4C 45
        0,0,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 0,1,0,0,0,0,1,0, 0,0,1,1,0,0,1,0, 1,0,1,0,0,0,1,0,
        # CRC: 29 0A CE
        1,0,0,1,0,1,0,0, 0,1,0,1,0,0,0,0, 0,1,1,1,0,0,1,1,
    ]

    expected_output_data = [
        # Access code
        0,1,1,0,1,0,1,1, 0,1,1,1,1,1,0,1, 1,0,0,1,0,0,0,1, 0,1,1,1,0,0,0,1,
        # PDU: 00 03 42 4C 45
        0,0,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 0,1,0,0,0,0,1,0, 0,0,1,1,0,0,1,0, 1,0,1,0,0,0,1,0,
        # CRC: 29 0A CE
        1,0,0,1,0,1,0,0, 0,1,0,1,0,0,0,0, 0,1,1,1,0,0,1,1,
    ]

    await generate_and_compare(dut, 0x8E89BED6, input_data, expected_output_data)

def test_access_code_generator():
    setup_test(
        "test_access_code_generator",
        "access_code_generator",
        [
            os.path.join(rtl_dir, "tx/access_code_generator.sv"),
        ]
    )
