bits 32
org SECTION_VA
dd wndproc,pump,idle,present,context,keyboard
wndproc:
    cmp dword [function],0
    je .pass
    push ebp
    mov ebp,esp
    push dword [ebp+20]
    push dword [ebp+16]
    push dword [ebp+12]
    push 0
    push context
    push dword [ebp+8]
    call [function]
    pop ebp
    test eax,eax
    jz .pass
    xor eax,eax
    ret 16
.pass:
    jmp ORIGINAL_WNDPROC
; Preserve the existing owned-controller pump even while paused. Its samples
; are offered to the overlay AFTER assignment and claim-press suppression.
pump:
    push ebp
    mov ebp,esp
    push ebx
    cmp dword [attempted],0
    jne .loaded
    mov dword [attempted],1
    push dllname
    call [LOADLIB]
    test eax,eax
    jz .loaded
    push exportname
    push eax
    call [GETPROC]
    mov [function],eax
.loaded:
    cmp dword [function],0
    je .poll
    push 0
    push 0
    push 0
    push 2
    push context
    push dword [HWND]
    call [function]
.poll:
    push dword [ebp+24]
    push dword [ebp+20]
    push dword [ebp+16]
    push dword [ebp+12]
    push dword [ebp+8]
%if ORIGINAL_PUMP
    call ORIGINAL_PUMP
%else
    call [PEEKMSG]
%endif
    mov ebx,eax
    test eax,eax
    jz .done
    cmp dword [function],0
    je .done
    mov eax,[ebp+8]
    ; Mouse messages must pass through cnc-ddraw's existing coordinate
    ; conversion before the game WndProc seam handles source pixels.
    cmp dword [eax+4],0x200
    jb .message
    cmp dword [eax+4],0x20e
    jbe .done
.message:
    push dword [eax+12]
    push dword [eax+8]
    push dword [eax+4]
    push 0
    push context
    push dword [eax]
    call [function]
    test eax,eax
    jz .done
    mov eax,[ebp+8]
    mov dword [eax+4],0
.done:
    mov eax,ebx
    pop ebx
    pop ebp
    ret 20
idle:
    ; Keep the original paused idle path. Never force FRAME/Flip here.
    pushfd
    pushad
    cmp dword [function],0
    je .original
    push 0
    push 0
    push 0
    push 1
    push context
    push dword [HWND]
    call [function]
.original:
    popad
    popfd
    call ORIGINAL_IDLE
    pushfd
    pushad
    cmp dword [function],0
    je .done
    push 0
    push 0
    push 0
    push 5
    push context
    push dword [HWND]
    call [function]
.done:
    popad
    popfd
    ret
present:
%if ORIGINAL_PRESENT
    call ORIGINAL_PRESENT
%else
    mov eax,[PRIMARY]
%endif
    pushfd
    cmp dword [function],0
    je .done
    pushad
    push 0
    push 0
    push 0
    push 3
    push context
    push dword [HWND]
    call [function]
    popad
.done:
    popfd
    ret
keyboard:
    ; After the original DirectInput read/reacquire, before P1 handlers.
    ; Preserve every register and replay the displaced compare exactly.
    pushad
    cmp dword [function],0
    je .done
    push 0
    push KEYBUFFER
    push 0
    push 4
    push context
    push dword [HWND]
    call [function]
.done:
    popad
    cmp dword [KEYCHECK],0
    ret
align 4
function: dd 0
attempted: dd 0
context:
    dd 84,PRIMARY,BACK,INACTIVE,GAMEMODE,MODE,SUBMODE,MOVIEFLAG
    dd GPAUSE,GRESUME,ALLOWED,FRAME,CUSTOM1,DZTHR1,DEVICES
    dd BINDS1,COND,TWINBINDS,HORIBINDS
    dd MODE2,CDSTOP
dllname: db 'vooverlay.dll',0
exportname: db 'VonOverlayStep',0
