# CAN Frame Contract

Project: quadruped_mvp
Bus: can_fd
Bitrate: 1000 kbps
Joint count: 12

## Frames
- emergency_stop: 0x100
- command_base: 0x200
- telemetry_base: 0x300
- heartbeat_ms: 20
