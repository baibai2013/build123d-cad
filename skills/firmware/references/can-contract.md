# CAN Contract

Generated CAN frame spec includes:

- command frame id base
- telemetry frame id base
- emergency-stop frame id
- heartbeat period
- expected joint count

Future firmware generators should consume the same contract instead of inventing
frame IDs ad hoc.
