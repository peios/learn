---
title: Wire Protocol
type: concept
description: The binary message protocol between the host and guest agent — message framing, types, and payload formats.
related:
  - provium/architecture/how-provium-works
  - provium/architecture/guest-agent
---

The host and guest agent communicate over vsock using a binary message protocol. Every interaction is a request-response pair: the host sends a message, the agent processes it and sends a response.

## Message framing

Every message has a 5-byte header followed by an optional payload:

```
[type: u8] [length: u32 LE] [payload: length bytes]
```

| Field | Size | Description |
|---|---|---|
| type | 1 byte | Message type identifier |
| length | 4 bytes | Payload length in little-endian byte order |
| payload | variable | Message-specific data (0 to 16 MiB) |

The maximum payload size is 16 MiB (16,777,216 bytes).

## Host to agent messages

| Type | Code | Description |
|---|---|---|
| `MSG_EXEC` | `0x01` | Execute a shell command |
| `MSG_WRITE_FILE` | `0x02` | Write data to a file |
| `MSG_READ_FILE` | `0x03` | Read a file |
| `MSG_SHUTDOWN` | `0x04` | Shut down the guest |
| `MSG_SYSCALL` | `0x05` | Execute a syscall with integer and buffer args |
| `MSG_IOCTL` | `0x06` | Execute an ioctl |
| `MSG_EXEC_ASYNC` | `0x07` | Start a command in the background |
| `MSG_JOB_WAIT` | `0x08` | Wait for a background job |
| `MSG_JOB_KILL` | `0x09` | Kill a background job |
| `MSG_IOCTL_BUF` | `0x0A` | Ioctl with embedded buffer pointers |
| `MSG_SPAWN_WORKER` | `0x0B` | Fork the agent process |
| `MSG_SYSCALL_PTR` | `0x0C` | Syscall with embedded pointer patching |

## Agent to host messages

| Type | Code | Description |
|---|---|---|
| `MSG_READY` | `0x80` | Agent initialized and ready |
| `MSG_EXEC_RESULT` | `0x81` | Command exit code + stdout + stderr |
| `MSG_FILE_DATA` | `0x82` | File contents or write acknowledgment |
| `MSG_ERROR` | `0x83` | Error message string |
| `MSG_SYSCALL_RESULT` | `0x84` | Syscall return value + output buffers |
| `MSG_JOB_STARTED` | `0x85` | Background job started (job ID + PID) |
| `MSG_JOB_RESULT` | `0x86` | Background job completed (exit code + stdout + stderr) |
| `MSG_WORKER_STARTED` | `0x87` | Worker spawned (vsock port + PID) |

## Payload formats

### MSG_EXEC (0x01)

Payload: the command string (UTF-8).

### MSG_EXEC_RESULT (0x81)

```
[exit_code: i32] [stdout_len: u32] [stdout: bytes] [stderr_len: u32] [stderr: bytes]
```

### MSG_WRITE_FILE (0x02)

```
[path_len: u32] [path: bytes] [data: remaining bytes]
```

### MSG_READ_FILE (0x03)

Payload: the file path (UTF-8).

### MSG_SYSCALL (0x05)

```
[nr: u32] [nargs: u32] [nbuf: u32]
[{arg_idx: i32, buf_len: u32} × nbuf]     # buffer specs
[args: i64 × nargs]                        # integer arguments
[buf_data: bytes]                           # concatenated buffer data
```

The agent allocates guest memory for each buffer, copies the data, replaces the corresponding arg with the buffer's address, and executes the syscall. After the syscall, buffer contents are returned in the response.

### MSG_SYSCALL_RESULT (0x84)

```
[result: i64] [buf_data: bytes]
```

The `buf_data` contains the output buffers in spec order, with sizes matching the input specs.

### MSG_SYSCALL_PTR (0x0C)

Extends `MSG_SYSCALL` with embedded pointer patching:

```
[nr: u32] [nargs: u32] [nbuf: u32] [nptr: u32]
[{arg_idx: i32, buf_len: u32} × nbuf]
[{buf_idx: u32, ptr_offset: u32, data_len: u32, is_output: u8, pad: 3} × nptr]
[args: i64 × nargs]
[buf_data: bytes]
[ptr_input_data: bytes]
```

For each pointer spec, the agent allocates a sub-buffer, optionally copies input data into it, and writes the sub-buffer's address into the parent buffer at `ptr_offset`. Output sub-buffers are returned after the buffer outputs.

### MSG_SPAWN_WORKER (0x0B)

```
[flags: u32]
```

Flags: `0` = fork, `1` = clone with CLONE_THREAD.

### MSG_WORKER_STARTED (0x87)

```
[port: u32] [pid: i32]
```

The worker listens on the returned vsock port. The host opens a new connection to that port.

## Connection lifecycle

1. Host launches QEMU with a vsock device (unique CID)
2. Agent starts in the guest, listens on port 5123
3. Host connects to `vsock://CID:5123`
4. Agent sends `MSG_READY`
5. Host sends requests, agent sends responses (synchronous)
6. Host sends `MSG_SHUTDOWN` or closes the connection
