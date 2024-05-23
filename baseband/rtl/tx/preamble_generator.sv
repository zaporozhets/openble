// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>


`timescale 1ns / 1ps
//
`default_nettype none
//
`include "ble_types.svh"

module preamble_generator (
    input wire aclk,
    input wire aresetn,

    input wire restart,

    input wire ble_phy_t phy,

    input  wire input_tdata,
    input  wire input_tvalid,
    output reg  input_tready,
    input  wire input_tlast,

    output reg  output_tdata,
    output reg  output_tvalid,
    input  wire output_tready,
    output reg  output_tlast
);

  localparam integer Preamble1MLength = 8;
  localparam logic [Preamble1MLength-1:0] Preamble1MPattern = 8'hAA;

  localparam integer Preamble2MLength = 16;
  localparam logic [Preamble2MLength-1:0] Preamble2MPattern = 16'hAAAA;

  localparam integer CodedPreambleLength = 80;
  localparam logic [CodedPreambleLength-1:0] CodedPreamblePattern = {10{8'b00111100}};

  typedef enum logic [2:0] {
    FsmIdle                 = 0,
    FsmInit,
    FsmWaitingForAccessWord,
    FsmSendingPreamble,
    FsmSendingData
  } fsm_state_t;

  reg first_tdata;
  reg first_tlast;

  fsm_state_t state;
  reg [$clog2(CodedPreambleLength):0] counter;
  reg [$clog2(CodedPreambleLength):0] preamble_len;
  reg [CodedPreambleLength-1:0] preamble;



  always @(posedge aclk) begin
    if (~aresetn) begin
      counter <= 0;

      first_tdata <= 0;
      first_tlast <= 0;

      output_tdata <= 0;
      output_tvalid <= 0;
      output_tlast <= 0;

      input_tready <= 1;

      state <= FsmIdle;

      preamble <= 0;
    end else begin
      case (state)
        FsmIdle: begin
          output_tvalid <= 0;
          input_tready <= 0;
          state <= FsmIdle;
        end
        FsmInit: begin
          state <= FsmWaitingForAccessWord;
          output_tvalid <= 0;
          input_tready <= 0;
        end
        FsmWaitingForAccessWord: begin
          input_tready <= 1;

          // Waiting for the first bit of access address so we can use it to calculate preamble
          if (input_tvalid & input_tready) begin
            input_tready <= 0;
            first_tdata <= input_tdata;
            first_tlast <= input_tlast;

            preamble <= get_preamble(phy, input_tdata);
            preamble_len <= get_preamble_len(phy);
            
            counter <= 1;
            output_tdata <= get_preamble(phy, input_tdata) & 1;
            output_tvalid <= 1;
            output_tlast <= 0;

            state <= FsmSendingPreamble;
          end
        end
        FsmSendingPreamble: begin
          input_tready  <= 0;

          if (output_tvalid & output_tready) begin
            counter <= counter + 1;
            output_tvalid <= 1;
            output_tdata  <= preamble[counter];
            output_tlast  <= 0;

            if (preamble_len <= counter) begin
              // Send 
              output_tdata <= first_tdata;
              output_tlast <= first_tlast;
              output_tvalid <= 1;
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
              input_tready <= 0;
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

  // Returns preamble value based on phy type
  function logic [CodedPreambleLength-1:0] get_preamble(ble_phy_t phy, logic acc_first_bit);

    // For 1M and 2M phy!
    // The first bit of the preamble (in transmission order)
    // shall be the same as the LSB of the Access Address.
    case (phy)
      BlePhy1M: begin
        get_preamble = (acc_first_bit) ? ~Preamble1MPattern : Preamble1MPattern;
      end
      BlePhy2M: begin
        get_preamble = (acc_first_bit) ? ~Preamble2MPattern : Preamble2MPattern;  
      end
      BlePhyCoded: begin
        get_preamble = CodedPreamblePattern; 
      end
    endcase
  endfunction

  // Returns preamble length based on phy type
  function logic [$clog2(CodedPreambleLength):0] get_preamble_len(ble_phy_t phy);
    case (phy)
      BlePhy1M: begin
        get_preamble_len = Preamble1MLength;
      end
      BlePhy2M: begin
        get_preamble_len = Preamble2MLength;        
      end
      BlePhyCoded: begin
        get_preamble_len = CodedPreambleLength;   
      end
    endcase
  endfunction

endmodule

`resetall
