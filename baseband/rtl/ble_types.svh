// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>


`ifndef BLE_TYPES_SVH
`define BLE_TYPES_SVH


typedef enum {
  PHY_1M,
  PHY_2M,
  PHY_CODED
} ble_phy_t;

parameter integer PreambleLength = 8;
parameter integer AccessCodeLength = 32;

typedef enum {
  PDU_TYPE_ADVERTISING,
  PDU_TYPE_DATA,
  PDU_TYPE_ISO,
  PDU_TYPE_TEST
} ble_pdu_type_t;

function automatic ble_pdu_type_t bits_to_pdu_type(bit [1:0] input_bits);
  case (input_bits)
    2'b00:   return PDU_TYPE_ADVERTISING;
    2'b01:   return PDU_TYPE_DATA;
    2'b10:   return PDU_TYPE_ISO;
    2'b11:   return PDU_TYPE_TEST;
    default: return PDU_TYPE_ADVERTISING;
  endcase
endfunction

// The Coding Indicator (CI) consists of two bits
typedef enum {
  CI_S8,  // FEC Block 2 coded using S=8
  CI_S2   // FEC Block 2 coded using S=2
} ble_ci_t;

function automatic ble_ci_t bits_to_ci(bit [1:0] input_bits);
  case (input_bits)
    2'b00:   return CI_S8;
    2'b01:   return CI_S2;
    default: return CI_S8;
  endcase
endfunction

typedef enum {
  FsmTxIdle,
  FsmTxInit,
  FsmTxWaitingHdrToSend,
  FsmTxSendingHdr,
  FsmTxSendingPayload,
  FsmTxFinishCrcCalulation,
  FsmTxSendingCrc,
  FsmTxWaitingToFinish,
  FsmTxDone,
  FsmTxCancel
} fsm_tx_state_t;


`endif
