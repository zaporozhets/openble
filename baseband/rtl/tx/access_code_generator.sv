// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

`resetall  //
`timescale 1ns / 1ps  //
`default_nettype none  //

module access_code_generator (
    input wire aclk,
    input wire aresetn,

    input wire restart,

    input wire [31:0] access_code,

    input  wire input_tdata,
    input  wire input_tvalid,
    output reg  input_tready,
    input  wire input_tlast,

    output reg  output_tdata,
    output reg  output_tvalid,
    input  wire output_tready,
    output reg  output_tlast
);
  reg first_tdata = 0;
  reg first_tlast = 0;


  typedef enum logic [1:0] {
    FsmIdle              = 0,
    FsmInit,
    FsmSendingAccessCode,
    FsmSendingData
  } fsm_state_t;

  fsm_state_t state;

  localparam integer AccessCodeLength = 32;
  reg [$clog2(AccessCodeLength):0] counter;

  always @(posedge aclk) begin
    if (~aresetn) begin
      counter <= 0;

      output_tdata <= 0;
      output_tvalid <= 0;
      output_tlast <= 0;

      input_tready <= 0;

      state <= FsmIdle;
    end else begin
      case (state)
        FsmIdle: begin
          input_tready  <= 0;
          output_tvalid <= 0;
          output_tlast <= 0;
        end
        FsmInit: begin
          input_tready <= 0;
          output_tvalid <= 0;
          counter <= 1;
          output_tdata <= access_code[0];
          output_tvalid <= 1;
          output_tlast <= 0;
          state <= FsmSendingAccessCode;
        end
        FsmSendingAccessCode: begin
          if (output_tvalid & output_tready) begin
            counter <= counter + 1;
            if (AccessCodeLength > counter) begin
              output_tdata  <= access_code[counter];
              output_tvalid <= 1;
            end else begin
              output_tvalid <= 0;

              input_tready <= 1;
              state <= FsmSendingData;
            end
          end
        end
        FsmSendingData: begin
          if (input_tvalid & input_tready) begin
            input_tready  <= 0;

            output_tdata  <= input_tdata;
            output_tlast  <= input_tlast;
            output_tvalid <= 1;
          end

          if (output_tvalid & output_tready) begin
            output_tvalid <= 0;
            input_tready  <= 1;
            if (output_tlast) begin
              state <= FsmIdle;
            end
          end

        end
        default: state <= FsmIdle;
      endcase
      if (restart) begin
        state <= FsmInit;
      end
    end
  end
endmodule

`resetall
