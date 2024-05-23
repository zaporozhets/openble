# 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

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

    def set_idle_generator(self, generator=None):
        if generator:
            self.source.set_pause_generator(generator())

    def set_backpressure_generator(self, generator=None):
        if generator:
            self.sink.set_pause_generator(generator())

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


def cycle_pause():
    return itertools.cycle([1, 1, 1, 0])

@cocotb.test()
async def run_test_basic(dut):
    tb = TB(dut)
    await tb.reset()

    tb.set_idle_generator(cycle_pause)
    tb.set_backpressure_generator(cycle_pause)


    # Channel index: 38
    dut.channel.value = 38
    dut.bypass.value = 0
    dut.restart.value = 1
    await RisingEdge(dut.aclk)
    await RisingEdge(dut.aclk)
    dut.restart.value = 0
    await RisingEdge(dut.aclk)
    await RisingEdge(dut.aclk)


    # PDU and CRC before whitening:
    input_bistream = [
        0,1,0,0,0,0,1,0, 1,0,0,1,0,0,0,0, 0,1,1,0,0,1,0,1, 1,0,1,0,0,1,0,1, 0,0,1,0,0,1,0,1, 1,1,0,0,0,1,0,1, 0,1,0,0,0,1,0,1,
        1,0,0,0,0,0,1,1, 1,0,0,0,0,0,0,0, 0,1,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 1,0,1,1,0,1,0,1, 0,0,1,0,1,1,0,1, 1,1,0,1,0,1,1,1,
    ]

    # PDU and CRC after whitening:
    expected_output_data = [
        0,0,1,0,1,0,0,1, 0,0,1,1,0,0,1,1, 0,1,0,0,0,1,1,1, 1,0,1,0,0,0,0,1, 1,0,1,1,1,1,1,1, 1,0,1,1,1,1,1,0, 1,1,0,0,0,0,1,0,
        0,1,1,1,0,0,1,0, 0,1,0,1,1,0,0,0, 1,1,1,0,0,1,0,1, 0,0,1,1,0,1,0,1, 1,1,1,1,0,1,1,1, 1,1,1,1,0,0,1,1, 1,0,1,0,0,1,0,1,
    ]

    test_frame = AxiStreamFrame(input_bistream)
    await tb.source.send(test_frame)

    output_data = await tb.sink.recv()

    assert tb.sink.empty()
    assert bytes(output_data) == bytes(expected_output_data)

@cocotb.test()
async def run_test_bypass(dut):

    tb = TB(dut)
    await tb.reset()

    tb.set_idle_generator(cycle_pause)
    tb.set_backpressure_generator(cycle_pause)


    # Channel index: 38
    dut.channel.value = 38
    dut.bypass.value = 1
    dut.restart.value = 1
    await RisingEdge(dut.aclk)
    await RisingEdge(dut.aclk)
    dut.restart.value = 0
    await RisingEdge(dut.aclk)
    await RisingEdge(dut.aclk)


    # PDU and CRC before whitening:
    input_bistream = [
        0,1,0,0,0,0,1,0, 1,0,0,1,0,0,0,0, 0,1,1,0,0,1,0,1, 1,0,1,0,0,1,0,1, 0,0,1,0,0,1,0,1, 1,1,0,0,0,1,0,1, 0,1,0,0,0,1,0,1,
        1,0,0,0,0,0,1,1, 1,0,0,0,0,0,0,0, 0,1,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 1,0,1,1,0,1,0,1, 0,0,1,0,1,1,0,1, 1,1,0,1,0,1,1,1,
    ]

    test_frame = AxiStreamFrame(input_bistream)
    await tb.source.send(test_frame)

    output_data = await tb.sink.recv()

    assert tb.sink.empty()
    assert bytes(output_data) == bytes(input_bistream)

def test_whitening():
    setup_test(
        "test_whitening",
        "whitening",
        [
            os.path.join(rtl_dir, "whitening.sv"),
        ]
    )
