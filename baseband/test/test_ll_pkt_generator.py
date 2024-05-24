# 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

import itertools
import logging
import os


import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from cocotbext.axi import AxiStreamFrame, AxiStreamBus, AxiStreamSource, AxiStreamSink

from helpers import setup_test, rtl_dir, BleCi, BlePhy, BlePduType

class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        # 1/40Mhz = 25ns
        cocotb.start_soon(Clock(dut.aclk, 25, units="ns").start())
        self.source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "payload"), dut.aclk, dut.aresetn, False)
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

    async def set_transmitter_parameters(self, phy_type, coding_indicator, access_code, whitening_enabled, channel, pdu_type, crc_init, header):
        self.dut.phy_type.value = phy_type.value
        if coding_indicator is not None:
            self.dut.coding_indicator.value = coding_indicator.value

        self.dut.access_code.value = access_code
        self.dut.whitening_enabled.value = whitening_enabled
        self.dut.channel.value = channel
        self.dut.pdu_type.value = pdu_type.value
        self.dut.crc_init.value = crc_init
        self.dut.packet_hdr.value = header

        self.dut.task_start.value = 1
        await RisingEdge(self.dut.aclk)
        await RisingEdge(self.dut.aclk)
        self.dut.task_start.value = 0
        await RisingEdge(self.dut.aclk)
        await RisingEdge(self.dut.aclk)

    async def send_receive_and_comapre(self, input_bistream, expected_output_data):
        test_frame = AxiStreamFrame(input_bistream)
        await self.source.send(test_frame)

        output_data =  bytes(await self.sink.recv())

        expected = bytes(expected_output_data)

        assert len(output_data) == len(expected)
        assert output_data == bytes(expected_output_data)

def cycle_pause():
    return itertools.cycle([1, 1, 1, 0])

# TODO: Enable after adding coded phy: @cocotb.test()
async def run_test_codec_s8(dut):
    """
    Test function for Coded S8 PHY transmission.

    The reference packet is described as bytes in transmission order (the leftmost
    byte in a line is transmitted first). Inside a byte, bits are transmitted LSB first.
    Access address: D6 BE 89 8E
    PDU: 00 03 42 4C 45
    CRC: 29 0A CE
    """
    tb = TB(dut)
    await tb.reset()


    pkt_header = 0x0300
    input_data = [
        0x42, 0x4C, 0x45
    ]

    expected_output_data = [

        # Preamble
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        # Access address
        0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1,
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0,
        1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1,
        1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0,
        # FEC1 S8
        # CI S8
        1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0,
        # TERM1 S8
        1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1,

        # FEC2 S8
        #PDU
        0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1,
        0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1,
        1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0,
        1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1,
        1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1,
        0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0,
        1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1,
        # CRC
        0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1,
        0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1,
        0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0,
        0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0,
        # TERM2
        0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0
    ]

    await tb.set_transmitter_parameters(BlePhy.BLE_PHY_CODED, BleCi.BLE_CI_S8,0x8E89BED6, 0, 0, BlePduType.PDU_TYPE_ADVERTISING, 0x555555, pkt_header)

    await tb.send_receive_and_comapre(input_data, expected_output_data)


# TODO: Enable after adding coded phy: @cocotb.test()
async def run_test_codec_s2(dut):
    """
    Test function for Coded S2 PHY transmission.

    The reference packet is described as bytes in transmission order (the leftmost
    byte in a line is transmitted first). Inside a byte, bits are transmitted LSB first.
    Access address: D6 BE 89 8E
    PDU: 00 03 42 4C 45
    CRC: 29 0A CE
    """
    tb = TB(dut)
    await tb.reset()

    # The reference packet is described as bytes in transmission order (the leftmost
    # byte in a line is transmitted first). Inside a byte, bits are transmitted LSB first.
    # Access address: D6 BE 89 8E
    # PDU: 00 03 42 4C 45
    # CRC: 29 0A CE
    pkt_header = 0x0300
    input_data = [
        0x42, 0x4C, 0x45
    ]

    expected_output_data = [
         # FEC1 S8
        # Preamble
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        # Access address
        0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1,
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1, 1,1,0,0,
        0,0,1,1, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0,
        1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0, 0,0,1,1, 0,0,1,1, 0,0,1,1,
        1,1,0,0, 1,1,0,0, 1,1,0,0, 1,1,0,0,
        # CI S2
        0,0,1,1, 1,1,0,0, 0,0,1,1, 1,1,0,0,
        # TERM1 S2
        0,0,1,1, 0,0,1,1, 1,1,0,0, 1,1,0,0, 0,0,1,1, 0,0,1,1,

        # FEC2 S2
        #PDU
        0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1,
        1 ,1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
        1 ,0,
        # CRC
        0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1,
        0, 1, 0, 0, 0, 0, 0, 0, 1,
        # TERM2
        0, 1, 0, 0, 1, 1,
    ]

    await tb.set_transmitter_parameters(BlePhy.BLE_PHY_CODED, BleCi.BLE_CI_S2,0x8E89BED6, 0, 0, BlePduType.PDU_TYPE_ADVERTISING, 0x555555, pkt_header)

    await tb.send_receive_and_comapre(input_data, expected_output_data)


@cocotb.test()
async def run_test_1m_phy(dut):
    """
    Test function for 1M PHY transmission.

    The reference packet is described as bytes in transmission order (the leftmost
    byte in a line is transmitted first). Inside a byte, bits are transmitted LSB first.
    Access address: D6 BE 89 8E
    PDU: 00 03 42 4C 45
    CRC: 29 0A CE
    """
    tb = TB(dut)
    await tb.reset()


    pkt_header = 0x0300
    input_data = [
        0x42, 0x4C, 0x45
    ]

    expected_output_data = [
        # Preamble 8 bit for 1M PHY
        0,1,0,1,0,1,0,1,
        # Access code
        0,1,1,0,1,0,1,1, 0,1,1,1,1,1,0,1, 1,0,0,1,0,0,0,1, 0,1,1,1,0,0,0,1,
        # PDU: 00 03 42 4C 45
        0,0,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 0,1,0,0,0,0,1,0, 0,0,1,1,0,0,1,0, 1,0,1,0,0,0,1,0,
        # CRC: 29 0A CE
        1,0,0,1,0,1,0,0, 0,1,0,1,0,0,0,0, 0,1,1,1,0,0,1,1,
    ]

    await tb.set_transmitter_parameters(BlePhy.BLE_PHY_1M, None, 0x8E89BED6, 0, 0, BlePduType.PDU_TYPE_ADVERTISING, 0x555555, pkt_header)

    await tb.send_receive_and_comapre(input_data, expected_output_data)

@cocotb.test()
async def run_test_2m_phy(dut):
    """
    Test function for 2M PHY transmission.

    The reference packet is described as bytes in transmission order (the leftmost
    byte in a line is transmitted first). Inside a byte, bits are transmitted LSB first.
    Access address: D6 BE 89 8E
    PDU: 00 03 42 4C 45
    CRC: 29 0A CE
    """

    tb = TB(dut)
    await tb.reset()

    pkt_header = 0x0300
    input_data = [
        0x42, 0x4C, 0x45
    ]

    expected_output_data = [
        # Preamble 16 bit for 2M PHY
        0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,
        # Access code
        0,1,1,0,1,0,1,1, 0,1,1,1,1,1,0,1, 1,0,0,1,0,0,0,1, 0,1,1,1,0,0,0,1,
        # PDU: 00 03 42 4C 45
        0,0,0,0,0,0,0,0, 1,1,0,0,0,0,0,0, 0,1,0,0,0,0,1,0, 0,0,1,1,0,0,1,0, 1,0,1,0,0,0,1,0,
        # CRC: 29 0A CE
        1,0,0,1,0,1,0,0, 0,1,0,1,0,0,0,0, 0,1,1,1,0,0,1,1,
    ]

    await tb.set_transmitter_parameters(BlePhy.BLE_PHY_2M, None, 0x8E89BED6, 0, 0, BlePduType.PDU_TYPE_ADVERTISING, 0x555555, pkt_header)

    await tb.send_receive_and_comapre(input_data, expected_output_data)


def test_ll_pkt_generator():
    setup_test(
        "test_ll_pkt_generator",
        "ll_pkt_generator",
        [
            os.path.join(rtl_dir, "tx/ll_pkt_generator.sv"),
            os.path.join(rtl_dir, "tx/pdu_crc_generator.sv"),
            os.path.join(rtl_dir, "tx/preamble_generator.sv"),
            os.path.join(rtl_dir, "tx/access_code_generator.sv"),
            os.path.join(rtl_dir, "tx/fec_encoder.sv"),

            os.path.join(rtl_dir, "serial_crc24.sv"),
            os.path.join(rtl_dir, "serializer.sv"),
            os.path.join(rtl_dir, "whitening.sv"),
        ]
    )
