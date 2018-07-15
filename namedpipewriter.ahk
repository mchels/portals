Menu, Tray, Icon, shell32.dll, 19

PIPE_ACCESS_OUTBOUND := 2
PIPE_NOWAIT := 1
PIPE_TYPE_MESSAGE := 4
ptr := A_PtrSize ? "Ptr" : "UInt"
char_size := A_IsUnicode ? 2 : 1
pipe_name := "\\.\pipe\ahk_py_pipe"

dwOpenMode := PIPE_ACCESS_OUTBOUND
dwPipeMode := PIPE_TYPE_MESSAGE + PIPE_NOWAIT
nMaxInstances := 1
nOutBufferSize := 4096
nInBufferSize := 4096
nDefaultTimeOut := 300
lpSecurityAttributes := 0
lpOverlapped := 0

pipe := DllCall("CreateNamedPipe"
    , "str", pipe_name
    , "uint", dwOpenMode
    , "uint", dwPipeMode
    , "uint", nMaxInstances
    , "uint", nOutBufferSize
    , "uint", nInBufferSize
    , "uint", nDefaultTimeOut
    , ptr, lpSecurityAttributes)
DllCall("ConnectNamedPipe", ptr, pipe, ptr, lpOverlapped)

WriteToPipe(msg) {
    global pipe
    global char_size
    global ptr
    global lpOverlapped
    lpNumberOfBytesWritten := 0
    errcode := DllCall("WriteFile"
        , ptr, pipe
        , "str", msg
        , "uint", StrLen(msg)*char_size
        , "uint*", lpNumberOfBytesWritten
        , ptr, lpOverlapped)
    If !errcode {
        MsgBox WriteFile failed: %ErrorLevel%/%A_LastError%
    }
}

^!u::
    WriteToPipe("-1")
    return

^!i::
    WriteToPipe("+1")
    return

^F12::
    WriteToPipe("Quit")
