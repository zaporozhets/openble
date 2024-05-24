// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

`resetall  //
`timescale 1ns / 1ps  //
`default_nettype none  //
`include "ble_types.svh"

module ll_pkt_generator (
    input wire aclk,
    input wire aresetn,


    input wire task_start,
    // input wire task_cancel,

    output wire event_payload,
    output wire event_end,

    input wire ble_phy_t             phy_type,
    input wire ble_ci_t              coding_indicator,
    input wire                [31:0] access_code,
    input wire                [ 5:0] channel,
    input wire                       whitening_enabled,
    input wire ble_pdu_type_t        pdu_type,
    input wire                [23:0] crc_init,
    input wire                [23:0] packet_hdr,

    input  wire [31:0] payload_tdata,
    input  wire        payload_tvalid,
    output reg         payload_tready,
    output reg         payload_restart,

    output wire [3:0] fsm_state,

    // Master interface
    output wire output_tdata,
    output wire output_tvalid,
    input  wire output_tready,
    output wire output_tlast
);
  wire restart = task_start;


  wire pkt_tdata;
  wire pkt_tvalid;
  wire pkt_tready;
  wire pkt_tlast;

  //***************************************************************************
  // Generates PDU and CRC stream
  //***************************************************************************
  pdu_crc_generator pdu_crc_generator_inst (
      .aclk(aclk),
      .aresetn(aresetn),

      .restart(restart),

      .event_payload(event_payload),
      .event_end(event_end),

      .pdu_type  (pdu_type),
      .crc_init  (crc_init),
      .packet_hdr(packet_hdr),

      .payload_tdata  (payload_tdata),
      .payload_tvalid (payload_tvalid),
      .payload_tready (payload_tready),
      .payload_restart(payload_restart),

      .fsm_state(fsm_state),

      .output_tdata (pkt_tdata),
      .output_tvalid(pkt_tvalid),
      .output_tready(pkt_tready),
      .output_tlast (pkt_tlast)
  );

  //***************************************************************************
  // Data whitening is used to avoid long sequences of zeros or ones, e.g.,
  // 0b0000000 or 0b1111111, in the data bit stream. Whitening shall be applied on
  // the PDU and CRC of all Link Layer packets and is performed after the CRC
  //***************************************************************************
  wire whitened_tdata;
  wire whitened_tvalid;
  wire whitened_tready;
  wire whitened_tlast;

  whitening ble_whitening (
      .aclk(aclk),
      .aresetn(aresetn),

      .bypass (~whitening_enabled),
      .restart(restart),
      .channel(channel),

      .input_tdata (pkt_tdata),
      .input_tvalid(pkt_tvalid),
      .input_tready(pkt_tready),
      .input_tlast (pkt_tlast),

      .output_tdata (whitened_tdata),
      .output_tvalid(whitened_tvalid),
      .output_tready(whitened_tready),
      .output_tlast (whitened_tlast)
  );

  //***************************************************************************
  // Assembles preamble, access code and whitened PDU into one stream
  //***************************************************************************
  wire pkt_with_acc_tdata;
  wire pkt_with_acc_tvalid;
  wire pkt_with_acc_tready;
  wire pkt_with_acc_tlast;
  access_code_generator access_code_generator_inst (
      .aclk   (aclk),
      .aresetn(aresetn),
      .restart(restart),

      .access_code(access_code),

      .input_tdata (whitened_tdata),
      .input_tvalid(whitened_tvalid),
      .input_tready(whitened_tready),
      .input_tlast (whitened_tlast),

      .output_tdata (pkt_with_acc_tdata),
      .output_tvalid(pkt_with_acc_tvalid),
      .output_tready(pkt_with_acc_tready),
      .output_tlast (pkt_with_acc_tlast)
  );

  //***************************************************************************
  // FEC encoder
  //***************************************************************************
  wire pkt_without_preamble_tdata;
  wire pkt_without_preamble_tvalid;
  wire pkt_without_preamble_tlast;
  wire pkt_without_preamble_tready;
  fec_encoder fec_encoder_dut (
      .aclk   (aclk),
      .aresetn(aresetn),
      .restart(restart),

      .bypass          (phy_type != PHY_CODED),
      .coding_indicator(coding_indicator),

      .input_tdata (pkt_with_acc_tdata),
      .input_tvalid(pkt_with_acc_tvalid),
      .input_tready(pkt_with_acc_tready),
      .input_tlast (pkt_with_acc_tlast),

      .output_tdata (pkt_without_preamble_tdata),
      .output_tvalid(pkt_without_preamble_tvalid),
      .output_tready(pkt_without_preamble_tready),
      .output_tlast (pkt_without_preamble_tlast)
  );

  preamble_generator preamble_generator_inst (
      .aclk(aclk),
      .aresetn(aresetn),
      .restart(restart),

      .phy(phy_type),

      .input_tdata (pkt_without_preamble_tdata),
      .input_tvalid(pkt_without_preamble_tvalid),
      .input_tready(pkt_without_preamble_tready),
      .input_tlast (pkt_without_preamble_tlast),

      .output_tdata (output_tdata),
      .output_tvalid(output_tvalid),
      .output_tready(output_tready),
      .output_tlast (output_tlast)
  );

endmodule

`resetall
