#ifndef VO_INI_TRANSACTION_H
#define VO_INI_TRANSACTION_H
#include <windows.h>
#include <string.h>
/* Stage the original writer against a sibling temporary file. The original
 * section and path are restored before atomic replacement, including failure.
 * No second persistent settings file or alternate INI authority is introduced. */
typedef struct {char *path,*section;char old_path[264],old_section[40],target[MAX_PATH],temporary[MAX_PATH];int active; } VoIniTransaction;
static int vo_ini_begin(VoIniTransaction *t,unsigned j,const char *section){
 memset(t,0,sizeof *t);
 t->path=(char*)(uintptr_t)(j?0x1acb7f0:0x1ad0b98);t->section=(char*)(uintptr_t)(j?0x1acb9c0:0x1ad0b70);
 memcpy(t->old_path,t->path,sizeof t->old_path);memcpy(t->old_section,t->section,sizeof t->old_section);
 if(!memchr(t->old_path,0,sizeof t->old_path)||!t->old_path[0]||strlen(section)>=40)return 0;
 char *file;DWORD n=GetFullPathNameA(t->old_path,MAX_PATH,t->target,&file);
 if(!n||n>=MAX_PATH||!file)return 0;
 DWORD attributes=GetFileAttributesA(t->target);
 if(attributes!=INVALID_FILE_ATTRIBUTES&&(attributes&(FILE_ATTRIBUTE_READONLY|FILE_ATTRIBUTE_DIRECTORY)))return 0;
 char directory[MAX_PATH];memcpy(directory,t->target,(size_t)(file-t->target));directory[file-t->target]=0;
 if(!GetTempFileNameA(directory,"vux",0,t->temporary))return 0;
 if(attributes!=INVALID_FILE_ATTRIBUTES&&!CopyFileA(t->target,t->temporary,FALSE)){DeleteFileA(t->temporary);return 0;}
 strcpy(t->path,t->temporary);strcpy(t->section,section);t->active=1;return 1;
}
static int vo_ini_end(VoIniTransaction *t,int commit){
 if(!t->active)return 0;
 if(!WritePrivateProfileStringA(NULL,NULL,NULL,t->temporary))commit=0;
 memcpy(t->path,t->old_path,sizeof t->old_path);memcpy(t->section,t->old_section,sizeof t->old_section);t->active=0;
 if(commit){
  HANDLE file=CreateFileA(t->temporary,GENERIC_WRITE,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
  if(file==INVALID_HANDLE_VALUE)commit=0;
  else{commit=FlushFileBuffers(file);CloseHandle(file);}
 }
 if(commit)commit=MoveFileExA(t->temporary,t->target,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH);
 if(!commit)DeleteFileA(t->temporary);
 return commit;
}
#endif
