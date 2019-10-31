#SingleInstance force
#Persistent
Menu, Tray, Icon, shell32.dll, 19
Gui +LastFound ; Required for hWnd := WinExist() below.

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
HSHELL_WINDOWCREATED := 1

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

; https://autohotkey.com/board/topic/80644-how-to-hook-on-to-shell-to-receive-its-messages/
hWnd := WinExist()
DllCall("RegisterShellHookWindow", UInt, hWnd)
MsgNum := DllCall("RegisterWindowMessage", Str, "SHELLHOOK")
OnMessage(MsgNum, "CallbackFunction")


Return ; Auto-execute section ends here: https://autohotkey.com/docs/Scripts.htm#auto



; Hotkey definitions
; ==============================================================================
#left::
    msg := "{""pc"": {""snap_active_in_drc"": [-1]}}"
    WriteToPipe(msg)
    return

#right::
    msg := "{""pc"": {""snap_active_in_drc"": [1]}}"
    WriteToPipe(msg)
    return

#up::
    msg := "{""pc"": {""maximize_active"": []}}"
    WriteToPipe(msg)
    return

+#left::
    msg := "{""pc"": {""move_focus_in_drc"": [-1]}}"
    WriteToPipe(msg)
    return

+#right::
    msg := "{""pc"": {""move_focus_in_drc"": [1]}}"
    WriteToPipe(msg)
    return

RAlt & PgUp::
    msg := "{""convert_clipboard_path"": []}"
    WriteToPipe(msg)
    return

^!F12::
    msg := "{""exit"": []}"
    WriteToPipe(msg)
    return



; Function definitions. These do not have to be in the auto-execute section.
; ==============================================================================
CallbackFunction(wParam, lParam) {
    global HSHELL_WINDOWCREATED
	If (wParam = HSHELL_WINDOWCREATED) {
        new_hwnd := lParam
        msg := "{""snap_created_window"": [""" . new_hwnd .  """]}"
        WriteToPipe(msg)
    }
}

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
