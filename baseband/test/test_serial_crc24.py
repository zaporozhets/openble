# 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

import logging
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from cocotbext.axi import AxiStreamFrame, AxiStreamBus, AxiStreamSource

from helpers import setup_test, rtl_dir

class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)
        cocotb.start_soon(Clock(dut.aclk, 2, units="ns").start())
        self.source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "input"), dut.aclk, dut.aresetn, False, byte_lanes=1)

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

@cocotb.test()
async def run_test_preset_555555(dut):

    tb = TB(dut)
    await tb.reset()

    tb.dut.init_preset.value = 0x555555
    tb.dut.restart.value = 1
    await RisingEdge(dut.aclk)
    await RisingEdge(dut.aclk)
    dut.restart.value = 0

    input_bistream = [
        # PDU: 00 03 42 4C 45
        0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,1,1,0,0,1,0,1,0,1,0,0,0,1,0,
        # CRC: 29 0A CE
        1,0,0,1,0,1,0,0,0,1,0,1,0,0,0,0,0,1,1,1,0,0,1,1,
    ]

    test_frame = AxiStreamFrame(input_bistream)
    await tb.source.send(test_frame)
    await tb.source.wait()

    # give one extra clock to get data
    await RisingEdge(tb.dut.aclk)

    assert 0 == tb.dut.crc_out.value

def test_serial_crc24():
    setup_test(
        "test_serial_crc24",
        "serial_crc24",
        [
            os.path.join(rtl_dir, "serial_crc24.sv"),
        ]
    )
