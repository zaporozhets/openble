`timescale 1ns / 1ps
//
`default_nettype none

// Implements whitener and de-whitener using a 7-bit linear
// feedback shift register with the polynomial x^7 + x^4 + 1.
// Before whitening or de-whitening, the shift register
// is initialized with data from init input.
module whitening (
    input wire aclk,
    input wire aresetn,

    input wire bypass,

    input wire restart,
    input wire [5:0] channel,

    input  wire input_tdata,
    input  wire input_tvalid,
    output wire input_tready,
    input  wire input_tlast,

    output wire output_tdata,
    output wire output_tvalid,
    input  wire output_tready,
    output  wire output_tlast
);
  reg [6:0] lfsr = 0;
  reg input_tready_int = 0;
  reg output_tdata_int = 0;
  reg output_tvalid_int = 0;
  reg output_tlast_int = 0;

  assign input_tready  = (bypass) ? output_tready : input_tready_int;
  assign output_tdata  = (bypass) ? input_tdata : output_tdata_int;
  assign output_tvalid = (bypass) ? input_tvalid : output_tvalid_int;
  assign output_tlast = (bypass) ? input_tlast : output_tlast_int;

  // Before whitening or de-whitening, the shift register is initialized with a sequence
  // that is derived from the physical channel index
  wire [6:0] init_sequence = {
    channel[0], channel[1], channel[2], channel[3], channel[4], channel[5], 1'b1
  };


  always @(posedge aclk) begin
    if (~aresetn | restart) begin
      lfsr <= init_sequence;
      input_tready_int <= 1;
      output_tvalid_int <= 0;
      output_tdata_int <= 0;
      output_tlast_int <= 0;
    end else begin
      if (input_tready_int & input_tvalid) begin
        lfsr[0] <= lfsr[6];
        lfsr[1] <= lfsr[0];
        lfsr[2] <= lfsr[1];
        lfsr[3] <= lfsr[2];
        lfsr[4] <= lfsr[3] ^ lfsr[6];
        lfsr[5] <= lfsr[4];
        lfsr[6] <= lfsr[5];
        input_tready_int <= 0;

        output_tdata_int <= lfsr[6] ^ input_tdata;
        output_tvalid_int <= 1;
        output_tlast_int <= input_tlast;
      end

      if (output_tvalid_int & output_tready) begin
        output_tvalid_int <= 0;
        input_tready_int  <= 1;
      end
    end
  end

endmodule

`resetall
