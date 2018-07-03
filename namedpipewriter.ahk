Menu, Tray, Icon, shell32.dll, 19

ptr := A_PtrSize ? "Ptr" : "UInt"
char_size := A_IsUnicode ? 2 : 1

pipe_name := "\\.\pipe\testpipe"

WriteToPipe(msg) {
    global pipe
    global char_size
    global ptr
    If !DllCall("WriteFile", ptr, pipe, "str", msg, "uint", StrLen(msg)*char_size, "uint*", 0, ptr, 0) {
        MsgBox WriteFile failed: %ErrorLevel%/%A_LastError%
    }
}

If ErrorLevel
    ExitApp

pipe := DllCall("CreateNamedPipe", "str", pipe_name, "uint", 3, "uint", 5, "uint", 1, "uint", 65536, "uint", 65536, "uint", 300, ptr, 0, ptr)
DllCall("ConnectNamedPipe", ptr, pipe, ptr, 0)
return

^!u::
    WriteToPipe("-1")
    return

^!i::
    WriteToPipe("+1")
    return
