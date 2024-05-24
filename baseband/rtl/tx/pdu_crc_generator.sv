// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>

`resetall  //
`timescale 1ns / 1ps  //
`default_nettype none  //
`include "ble_types.svh"  //

module pdu_crc_generator (
    input wire aclk,
    input wire aresetn,

    input wire restart,

    output wire event_payload,
    output wire event_end,


    input wire ble_pdu_type_t pdu_type,

    input wire [23:0] crc_init,
    input wire [23:0] packet_hdr,

    input  wire [31:0] payload_tdata,
    input  wire        payload_tvalid,
    output reg         payload_tready,
    output wire        payload_restart,

    output wire fsm_tx_state_t fsm_state,

    // Master interface
    output wire output_tdata,
    output wire output_tvalid,
    input  wire output_tready,
    output wire output_tlast
);

  assign payload_restart = restart;
  //***************************************************************************
  // Receiver state machine
  //***************************************************************************
  fsm_tx_state_t state;
  fsm_tx_state_t previous_fsm_state;

  //assign fsm_state = state;




  wire [7:0] hdr_payload_byte_length = packet_hdr[15:8];

  wire [23:0] crc_out;
  reg [7:0] payload_remaining_bytes = 0;

  localparam integer MaxPduChunkLengthBits = 32;
  reg [$clog2(MaxPduChunkLengthBits):0] pdu_chunk_length_bits = 0;

  reg [31:0] pdu_chunk_tdata = 0;
  reg pdu_chunk_tvalid = 0;
  wire pdu_chunk_tready;
  reg pdu_chunk_tlast = 0;

  assign event_end = output_tvalid & output_tlast & output_tready;
  assign event_payload = (previous_fsm_state != state) & (state == FsmTxFinishCrcCalulation);

  always @(posedge aclk) begin : FSM
    if (~aresetn) begin

      payload_remaining_bytes <= 0;
      payload_tready <= 0;

      pdu_chunk_length_bits <= 0;
      pdu_chunk_tdata <= 0;
      pdu_chunk_tvalid <= 0;
      pdu_chunk_tlast <= 0;

      state <= FsmTxIdle;
      previous_fsm_state <= FsmTxIdle;
    end else begin
      case (state)
        FsmTxIdle: begin
          state <= FsmTxIdle;
        end
        FsmTxInit: begin
          payload_remaining_bytes <= 0;
          payload_tready <= 0;

          pdu_chunk_length_bits <= 0;
          pdu_chunk_tdata <= 0;
          pdu_chunk_tvalid <= 0;
          pdu_chunk_tlast <= 0;
          state <= FsmTxSendingHdr;
        end
        FsmTxSendingHdr: begin
          payload_tready <= 0;
          payload_remaining_bytes <= 0;

          // Prepate header for the next state
          pdu_chunk_length_bits <= 16;  // TODO: add 24bit header support
          pdu_chunk_tdata <= packet_hdr;
          pdu_chunk_tvalid <= 1;
          pdu_chunk_tlast <= 0;

          state <= FsmTxWaitingHdrToSend;
        end
        FsmTxWaitingHdrToSend: begin
          if (pdu_chunk_tvalid & pdu_chunk_tready) begin
            pdu_chunk_tvalid <= 0;
            payload_tready <= 1;
            payload_remaining_bytes <= hdr_payload_byte_length;
            state <= FsmTxSendingPayload;
          end
        end
        FsmTxSendingPayload: begin
          if (payload_tvalid & payload_tready) begin
            payload_tready   <= 0;
            pdu_chunk_tdata  <= payload_tdata;
            pdu_chunk_tvalid <= 1;

            if (payload_remaining_bytes > 3) begin
              payload_remaining_bytes <= payload_remaining_bytes - 4;
              pdu_chunk_length_bits   <= 32;
            end else begin
              payload_remaining_bytes <= 0;
              pdu_chunk_length_bits   <= payload_remaining_bytes * 8;
            end

          end

          if (pdu_chunk_tvalid & pdu_chunk_tready) begin
            pdu_chunk_tvalid <= 0;
            if (payload_remaining_bytes) begin
              payload_tready <= 1;
            end else begin
              payload_tready <= 0;
              state <= FsmTxFinishCrcCalulation;
            end
          end
        end
        FsmTxFinishCrcCalulation: begin
          if (pdu_chunk_tready) begin
            // One extra cycle to finish CRC calculation
            state <= FsmTxSendingCrc;
          end
        end
        FsmTxSendingCrc: begin
          pdu_chunk_tlast <= 1;
          pdu_chunk_tvalid <= 1;
          pdu_chunk_tdata <= swap24(crc_out);
          pdu_chunk_length_bits <= 24;
          state <= FsmTxWaitingToFinish;
        end
        FsmTxWaitingToFinish: begin
          if (pdu_chunk_tvalid & pdu_chunk_tready) begin
            pdu_chunk_tlast <= 0;
            pdu_chunk_tvalid <= 0;
            state <= FsmTxDone;
          end
        end
        FsmTxDone: begin
          state <= FsmTxDone;
        end

        default: state <= FsmTxIdle;
      endcase

      if (restart) begin
        state <= FsmTxInit;
      end
      previous_fsm_state <= state;
    end
  end




  serializer #(
      .C_DATA_WIDTH(MaxPduChunkLengthBits)
  ) serializer_inst (
      .aclk(aclk),
      .aresetn(aresetn),
      .restart(restart),
      .input_length(pdu_chunk_length_bits),
      .input_tdata(pdu_chunk_tdata),
      .input_tvalid(pdu_chunk_tvalid),
      .input_tready(pdu_chunk_tready),
      .input_tlast(pdu_chunk_tlast),

      .output_tdata (output_tdata),
      .output_tvalid(output_tvalid),
      .output_tready(output_tready),
      .output_tlast (output_tlast)
  );

  serial_crc24 crc_inst (
      .aclk(aclk),
      .aresetn(aresetn),
      .restart(restart),
      .init_preset(crc_init),
      .input_tdata(output_tdata),
      .input_tvalid(output_tvalid & output_tready),
      .crc_out(crc_out)
  );

  function automatic [23:0] swap24(input logic [23:0] data);
    integer i;
    for (i = 0; i < 24; i = i + 1) begin
      swap24[i] = data[23-i];
    end
  endfunction
endmodule

`resetall
