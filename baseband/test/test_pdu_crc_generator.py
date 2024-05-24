# 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

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
        self.source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "payload"), dut.aclk, dut.aresetn, False)
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

# The reference packet is described as bytes in transmission order (the leftmost
# byte in a line is transmitted first). Inside a byte, bits are transmitted LSB first.
# Access address: D6 BE 89 8E
# PDU: 00 03 42 4C 45
# CRC: 29 0A CE
@cocotb.test()
async def run_test(dut):

    tb = TB(dut)
    await tb.reset()

    pkt_header = 0x0300
    input_bistream = [
        0x42, 0x4C, 0x45
    ]

    #self.dut.pdu_type.value = pdu_type.value
    dut.crc_init.value = 0x555555
    dut.packet_hdr.value = pkt_header

    dut.restart.value = 1
    await RisingEdge(dut.aclk)
    await RisingEdge(dut.aclk)
    dut.restart.value = 0


    expected_output_data = [
        # PDU: 00 03 42 4C 45
        0,0,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 0,1,0,0,0,0,1,0, 0,0,1,1,0,0,1,0, 1,0,1,0,0,0,1,0,
        # CRC: 29 0A CE
        1,0,0,1,0,1,0,0, 0,1,0,1,0,0,0,0, 0,1,1,1,0,0,1,1,
    ]

    test_frame = AxiStreamFrame(input_bistream)
    await tb.source.send(test_frame)

    output_data =  bytes(await tb.sink.recv())

    expected = bytes(expected_output_data)

    assert len(output_data) == len(expected)
    assert output_data == bytes(expected_output_data)

def test_serial_crc24():
    setup_test(
        "test_pdu_crc_generator",
        "pdu_crc_generator",
        [
            os.path.join(rtl_dir, "tx/pdu_crc_generator.sv"),
            os.path.join(rtl_dir, "serial_crc24.sv"),
            os.path.join(rtl_dir, "serializer.sv"),
        ]
    )
