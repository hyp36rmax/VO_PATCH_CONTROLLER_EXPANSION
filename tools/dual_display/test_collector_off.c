/* Compile the real launch gate; every observer/file/process API is forbidden Off. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <wchar.h>
#define MAX_PATH 260
#define TRUE 1
#define FALSE 0
#define CREATE_NO_WINDOW 0
#define ERROR_ALREADY_EXISTS 183
#define WAIT_OBJECT_0 0
typedef wchar_t WCHAR;typedef unsigned DWORD;typedef uintptr_t HANDLE;typedef int BOOL;
typedef struct {unsigned cb;} STARTUPINFOW;
typedef struct {HANDLE hThread,hProcess;} PROCESS_INFORMATION;
typedef struct {int mode,profile,primary,secondary,reasons;} VoSelection;
static struct {int mode;} saved;
static unsigned state_writes;
static int SetEnvironmentVariableA(const char *key,const char *value){assert(key&&value);state_writes++;return 1;}
static unsigned vo_diagnostic_level(void){return 0;}
static unsigned unexpected(void){assert(!"Off must not start a collector or access diagnostic paths");return 0;}
#define GetModuleFileNameW(...) unexpected()
#define GetCurrentProcessId(...) unexpected()
#define GetTickCount(...) unexpected()
#define CreateEventW(...) unexpected()
#define GetLastError(...) unexpected()
#define CloseHandle(...) unexpected()
#define CreateProcessW(...) unexpected()
#define WaitForMultipleObjects(...) unexpected()
#define TerminateProcess(...) unexpected()
#define WaitForSingleObject(...) unexpected()
#define event(...) unexpected()
#include "collector_start.h"
int main(void){VoSelection s={0,1,0,-1,0};assert(vo_collector(&s));assert(state_writes==6);puts("PASS production Off launch: effective display state preserved; no diagnostic path, event, process or wait APIs");return 0;}
