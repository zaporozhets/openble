// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

`resetall  //
`timescale 1ns / 1ps  //
`default_nettype none  //
`include "ble_types.svh"

module fec_encoder (
    input wire aclk,
    input wire aresetn,
    input wire restart,

    input wire bypass,

    input wire ble_ci_t coding_indicator,

    input  wire input_tdata,
    input  wire input_tvalid,
    output wire input_tready,
    input  wire input_tlast,

    output wire output_tdata,
    output wire output_tvalid,
    input  wire output_tready,
    output wire output_tlast
);

  reg  input_tready_int;
  wire output_tdata_int;
  wire output_tvalid_int;
  wire output_tlast_int;

  assign input_tready  = (bypass) ? output_tready : input_tready_int;
  assign output_tdata  = (bypass) ? input_tdata : output_tdata_int;
  assign output_tvalid = (bypass) ? input_tvalid : output_tvalid_int;
  assign output_tlast  = (bypass) ? input_tlast : output_tlast_int;

endmodule

`resetall
