// 2024 Taras Zaporozhets <zaporozhets.taras@gmail.com>


`ifndef BLE_TYPES_SVH
`define BLE_TYPES_SVH


typedef enum logic [1:0] {
  BlePhy1M    = 0,
  BlePhy2M    = 1,
  BlePhyCoded = 2
} ble_phy_t;

parameter integer PreambleLength = 8;
parameter integer AccessCodeLength = 32;


`endif
