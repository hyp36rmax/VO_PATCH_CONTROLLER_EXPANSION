#ifndef VO_STARTUP_PLAN_H
#define VO_STARTUP_PLAN_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct {uint32_t offset,size;const unsigned char *before,*after;} VoStartupWrite;
static uint32_t vo_word(const unsigned char *p){uint32_t n;memcpy(&n,p,4);return n;}
static uint32_t vo_crc(const unsigned char *p,size_t n){
 uint32_t c=~0u;while(n--){c^=*p++;for(unsigned b=0;b<8;b++)c=(c>>1)^(0xedb88320u&-(c&1u));}return ~c;
}
/* Validate every record in every profile before exposing a selected plan. */
static int vo_startup_plan(const unsigned char *table,size_t bytes,uint32_t crc,
 unsigned profile,uint32_t mapped,const unsigned char **selected,unsigned *count){
 if(bytes<20||bytes>32u*1024*1024||profile>=5||vo_crc(table,bytes)!=crc||
 vo_word(table)!=0x33504f56||vo_word(table+4)!=2||vo_word(table+8)!=mapped||vo_word(table+12)!=5||vo_word(table+16)>1)return 0;
 size_t pos=20;
 for(unsigned p=0;p<5;p++){
  if(bytes-pos<4)return 0;
  unsigned n=vo_word(table+pos);pos+=4;if(n>100000)return 0;
  if(p==profile){*selected=table+pos;*count=n;}
  uint32_t end=0;
  for(unsigned i=0;i<n;i++){
   if(bytes-pos<8)return 0;
   uint32_t off=vo_word(table+pos),len=vo_word(table+pos+4);pos+=8;
   if(!len||off<4096||off<end||off>mapped||len>mapped-off||len>(bytes-pos)/2)return 0;
   end=off+len;pos+=2*(size_t)len;
  }
 }
 return pos==bytes;
}
static VoStartupWrite vo_startup_write(const unsigned char **cursor){
 const unsigned char *p=*cursor;VoStartupWrite w={vo_word(p),vo_word(p+4),p+8,p+8+vo_word(p+4)};
 *cursor=p+8+2*(size_t)w.size;return w;
}
static int vo_startup_matches(const unsigned char *base,const unsigned char *plan,unsigned count){
 for(unsigned i=0;i<count;i++){VoStartupWrite w=vo_startup_write(&plan);if(memcmp(base+w.offset,w.before,w.size))return 0;}return 1;
}
#endif
