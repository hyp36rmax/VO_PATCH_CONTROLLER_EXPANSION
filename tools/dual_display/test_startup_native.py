"""Compile production table validator and memory writer with protection doubles."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent;out=Path(sys.argv[1]).resolve()
s=(here/'startup_runtime.h').read_text();apply=s[s.index('static int vo_activate'):s.index('__declspec(dllexport)')]
fixture=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "startup_plan.h"
typedef unsigned DWORD;
#define PAGE_EXECUTE_READWRITE 64
static unsigned char *memory;static unsigned protection[20000];static unsigned fail_page=~0u;
static int VirtualProtect(void *address,size_t size,DWORD next,DWORD *old){
 size_t offset=(unsigned char*)address-memory;assert(size==4096&&offset%4096==0);
 unsigned page=(unsigned)(offset/4096);assert(page<20000);
 if(page==fail_page&&next==64)return 0;
 *old=protection[page];protection[page]=next;return 1;
}
static void *GetCurrentProcess(void){return NULL;}
static int FlushInstructionCache(void *p,void *m,size_t n){(void)p;(void)n;assert(m==memory);return 1;}
'''
test=r'''
int main(int argc,char **argv){
 assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);fseek(f,0,SEEK_END);size_t size=(size_t)ftell(f);rewind(f);
 unsigned char *file=malloc(size);assert(fread(file,1,size,f)==size);fclose(f);
 unsigned nt=vo_word(file+60),opt=nt+24,sections=file[nt+6]|file[nt+7]<<8;
 unsigned mapped=vo_word(file+opt+56);memory=calloc(mapped,1);assert(memory);
 unsigned tab=opt+(file[nt+20]|file[nt+21]<<8);const unsigned char *table=NULL;unsigned bytes=0;
 for(unsigned i=0;i<sections;i++){
  const unsigned char *s=file+tab+i*40;unsigned va=vo_word(s+12),raw=vo_word(s+20),len=vo_word(s+16);
  memcpy(memory+va,file+raw,len);
  if(!memcmp(s,".voboot",7)){table=file+raw+512;bytes=vo_word(s+8)-512;}
 }
 assert(table&&bytes);unsigned mapped_profiles=vo_word(table+8);uint32_t crc=vo_crc(table,bytes);
 unsigned char *original=malloc(mapped);memcpy(original,memory,mapped);
 for(unsigned profile=0;profile<5;profile++){
  const unsigned char *plan=NULL;unsigned n=0;
  assert(vo_startup_plan(table,bytes,crc,profile,mapped_profiles,&plan,&n));
  assert(!vo_startup_plan(table,bytes,crc^1,profile,mapped_profiles,&plan,&n));
  assert(!vo_startup_plan(table,bytes-1,vo_crc(table,bytes-1),profile,mapped_profiles,&plan,&n));
  assert(!vo_startup_plan(table,bytes,crc,5,mapped_profiles,&plan,&n));
  assert(vo_startup_plan(table,bytes,crc,profile,mapped_profiles,&plan,&n));
  for(unsigned p=0;p<20000;p++)protection[p]=32;
  memcpy(memory,original,mapped);fail_page=~0u;
  assert(vo_activate(memory,plan,n,mapped_profiles));
  for(unsigned p=0;p<20000;p++)assert(protection[p]==32);
  if(n){
   memcpy(memory,original,mapped);const unsigned char *c=plan;VoStartupWrite w=vo_startup_write(&c);
   VoStartupWrite last=w;for(unsigned i=1;i<n;i++)last=vo_startup_write(&c);
   fail_page=last.offset/4096;assert(!vo_activate(memory,plan,n,mapped_profiles));
   assert(!memcmp(memory,original,mapped));for(unsigned p=0;p<20000;p++)assert(protection[p]==32);
   fail_page=~0u;memory[w.offset]^=1;unsigned char *bad=malloc(mapped);memcpy(bad,memory,mapped);
   assert(!vo_activate(memory,plan,n,mapped_profiles));assert(!memcmp(memory,bad,mapped));free(bad);
  }
 }
 free(original);free(memory);free(file);puts("PASS native CRC/bounds/plan validation, preflight mismatch and protection failure, original page protection restoration");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'test.c';p.write_text(fixture+apply+test)
 subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(here),str(p),'-o',td+'/test'],check=True)
 for edition in ['retail','jpre']:subprocess.run([td+'/test',str(out/(edition+'-internal.exe'))],check=True)
