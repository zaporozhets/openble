// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

`resetall  //
`timescale 1 ns / 1 ps  //
`default_nettype none  //

module serializer #(
    // Width of input data bus
    parameter integer C_DATA_WIDTH = 32
) (
    input wire aclk,
    input wire aresetn,

    input wire restart,

    input  wire [$clog2(C_DATA_WIDTH):0] input_length,
    input  wire [      C_DATA_WIDTH-1:0] input_tdata,
    input  wire                          input_tvalid,
    output reg                           input_tready,
    input  wire                          input_tlast,

    output reg  output_tdata,
    output reg  output_tvalid,
    input  wire output_tready,
    output reg  output_tlast
);

  // Serialize decoded data
  reg [C_DATA_WIDTH-1:0] shift_buffer_data = 0;
  reg [$clog2(C_DATA_WIDTH):0] shift_buffer_length = 0;
  reg [$clog2(C_DATA_WIDTH):0] shift_buffer_index = 0;
  reg shift_buffer_tlast;
  always @(posedge aclk) begin
    if (~aresetn | restart) begin
      shift_buffer_index <= 0;
      shift_buffer_length <= 0;
      shift_buffer_data <= 0;
      shift_buffer_tlast <= 0;

      input_tready <= 1;

      output_tvalid <= 0;
      output_tdata <= 0;
      output_tlast <= 0;
    end else begin
      if (input_tready & input_tvalid) begin
        input_tready <= 0;

        shift_buffer_data <= input_tdata;
        shift_buffer_length <= input_length;
        shift_buffer_index <= 1;
        shift_buffer_tlast <= input_tlast;
        output_tdata <= input_tdata[0];
        output_tvalid <= 1;
      end

      if (output_tvalid & output_tready) begin
        if (shift_buffer_index < shift_buffer_length) begin
          shift_buffer_index <= shift_buffer_index + 1;
          output_tvalid <= 1;
          /* verilator lint_off WIDTH */
          output_tdata <= shift_buffer_data[shift_buffer_index];
          /* verilator lint_on WIDTH */
          if ((shift_buffer_index + 1) == shift_buffer_length) begin
            output_tlast <= shift_buffer_tlast;
          end
        end else begin
          output_tvalid <= 0;
          output_tdata  <= 0;
          output_tlast  <= 0;
          input_tready  <= 1;
        end
      end
    end
  end
endmodule

`resetall
