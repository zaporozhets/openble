// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

`timescale 1ns / 1ps

`default_nettype none

// CRC polynomial coefficients: x^24 + x^10 + x^9 + x^6 + x^4 + x^3 + x + 1
// CRC width:                   24 bits

module serial_crc24 (
    input wire aclk,
    input wire aresetn,

    input wire restart,

    input wire [23:0]  init_preset,
    input wire         in_tdata,
    input wire         in_tvalid,

    output wire [23:0] crc_out
);
  reg [23:0] lfsr = 0;

  assign crc_out = lfsr;

  always @(posedge aclk)
    if (~aresetn | restart) begin
      lfsr <= init_preset;
    end else if (in_tvalid) begin
      lfsr[0]  <= in_tdata ^ lfsr[23];
      lfsr[1]  <= lfsr[0] ^ (in_tdata ^ lfsr[23]);
      lfsr[2]  <= lfsr[1];
      lfsr[3]  <= lfsr[2] ^ (in_tdata ^ lfsr[23]);
      lfsr[4]  <= lfsr[3] ^ (in_tdata ^ lfsr[23]);
      lfsr[5]  <= lfsr[4];
      lfsr[6]  <= lfsr[5] ^ (in_tdata ^ lfsr[23]);
      lfsr[7]  <= lfsr[6];
      lfsr[8]  <= lfsr[7];
      lfsr[9]  <= lfsr[8] ^ (in_tdata ^ lfsr[23]);
      lfsr[10] <= lfsr[9] ^ (in_tdata ^ lfsr[23]);
      lfsr[11] <= lfsr[10];
      lfsr[12] <= lfsr[11];
      lfsr[13] <= lfsr[12];
      lfsr[14] <= lfsr[13];
      lfsr[15] <= lfsr[14];
      lfsr[16] <= lfsr[15];
      lfsr[17] <= lfsr[16];
      lfsr[18] <= lfsr[17];
      lfsr[19] <= lfsr[18];
      lfsr[20] <= lfsr[19];
      lfsr[21] <= lfsr[20];
      lfsr[22] <= lfsr[21];
      lfsr[23] <= lfsr[22];
    end

endmodule

`resetall
