Menu, Tray, Icon, shell32.dll, 19

ptr := A_PtrSize ? "Ptr" : "UInt"
; char_size := A_IsUnicode ? 2 : 1
char_size := 1

pipe_name := "\\.\pipe\testpipe"

If ErrorLevel
    ExitApp

pipe := DllCall("CreateNamedPipe", "str", pipe_name, "uint", 3, "uint", 4, "uint", 1, "uint", 65536, "uint", 65536, "uint", 300, ptr, 0, ptr)
DllCall("ConnectNamedPipe", ptr, pipe, ptr, 0)
return

^!u::
    PipeMsg := "-1"
    If !DllCall("WriteFile", ptr, pipe, "str", PipeMsg, "uint", (StrLen(PipeMsg)+1)*char_size, "uint*", 0, ptr, 0) {
        MsgBox WriteFile failed: %ErrorLevel%/%A_LastError%
    }
    return

^!i::
    PipeMsg := "+1"
    If !DllCall("WriteFile", ptr, pipe, "str", PipeMsg, "uint", (StrLen(PipeMsg)+1)*char_size, "uint*", 0, ptr, 0) {
        MsgBox WriteFile failed: %ErrorLevel%/%A_LastError%
    }
    return
