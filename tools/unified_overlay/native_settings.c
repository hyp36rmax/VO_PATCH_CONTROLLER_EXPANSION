#include "native_settings.h"
#include <stdio.h>
#include <string.h>
/* Addresses and byte encodings are checked against the original procedures
 * in both editions. Original snapshot/apply and F4 completion remain owners. */
static const uintptr_t globals[2][6]={
 {0x1add13c,0x1add134,0x1add138,0x1add148,0x1add144,0x1add140},
 {0x1ad7dc0,0x1ad7dc8,0x1ad7dc4,0x1ad7db8,0x1ad7dcc,0x1ad7dbc}
};
static const uintptr_t graphics[2][9]={
 {0x6c84d0,0x345d248,0x345d234,0x345d25c,0x682c8c,0x682c90,0x682c94,0x6bf598,0x6bf59c},
 {0x6c41e8,0x3457ea8,0x3457eb4,0x3457eb8,0x67ec14,0x67ec18,0x67ec1c,0x6bb2b0,0x6bb2b4}
};
#define WORD_AT(a) (*(unsigned*)(uintptr_t)(a))
static void f6(VoNativeSettings *s,int save){
 uintptr_t slot=s->edition?0x1cdca64:0x1ce1dbc;void *old=*(void**)slot;unsigned previous[6];
 *(void**)slot=s->scratch;
 for(unsigned i=0;i<6;i++){previous[i]=WORD_AT(globals[s->edition][i]);if(save)WORD_AT(globals[s->edition][i])=s->values[i];}
 ((void(__cdecl*)(void))(uintptr_t)(s->edition?(save?0x5c6800:0x5c67a5):(save?0x5cbf60:0x5cbf05)))();
 for(unsigned i=0;i<6;i++){if(!save)s->values[i]=WORD_AT(globals[s->edition][i]);WORD_AT(globals[s->edition][i])=previous[i];}
 *(void**)slot=old;
}
void vo_native_end(VoNativeSettings *s){if(s)memset(s,0,sizeof *s);}
int vo_native_begin(VoNativeSettings *s,HWND owner,const volatile LONG *mode,unsigned category){
 (void)owner;if(!s||s->host||category>5)return 0;
 int j=(uintptr_t)mode==0x1ae3594?0:(uintptr_t)mode==0x1adcdf0?1:-1;if(j<0)return 0;
 memset(s,0,sizeof *s);s->edition=j;s->category=category;s->host=(HWND)1;
 if(category){f6(s,0);return 1;}
 const unsigned char *site=(void*)(uintptr_t)(j?0x5c1d63:0x5c7494);
 if(*site!=0xe8){vo_native_end(s);return 0;}
 int32_t displacement;memcpy(&displacement,site+1,4);s->finish=(void*)(site+5+displacement);
 s->ui=(uintptr_t)s->finish-6439; /* installed UI_DLG_DONE */
 for(unsigned i=0;i<9;i++)s->values[i]=WORD_AT(graphics[j][i]);
 s->values[9]=WORD_AT(j?0x67d778:0x6817f0)==0;
 s->values[10]=WORD_AT(s->ui+0x1ec0);return 1;
}
static int combo_offset(unsigned id){
 if(id>=1000&&id<=1003)return 0x1e + id-1000;
 if(id>=1004&&id<=1006)return 0x23+id-1004;
 return id==1007?0x29:id==1013?0x22:id==1014?0x27:-1;
}
int vo_native_count(VoNativeSettings *s,unsigned id){if(!s->host||combo_offset(id)<0)return 0;return id==1007?4:(id<=1003||id==1013)?15:5;}
int vo_native_selected(VoNativeSettings *s,unsigned id){
 int o=combo_offset(id);if(!s->host||o<0)return -1;int n=s->scratch[o];
 if(id==1007)return (n+1)%4;return (id<=1003||id==1013)?(n==255?14:n-5):n;
}
int vo_native_select(VoNativeSettings *s,unsigned id,unsigned choice){
 if(choice>=(unsigned)vo_native_count(s,id))return 0;
 s->changed[combo_offset(id)]=255;
 s->scratch[combo_offset(id)]=id==1007?(choice+3)%4:(id<=1003||id==1013)?(choice==14?255:choice+5):choice;return 1;
}
int vo_native_choice(VoNativeSettings *s,unsigned id,unsigned choice,char *text,unsigned size){
 if(!text||!size||choice>=(unsigned)vo_native_count(s,id))return 0;
 static const char *difficulty[]={"Easy","Normal","Hard","Very Hard"};
 static const char *matches[]={"Once","Twice","3 Times","4 Times","5 Times"};
 if(id==1007)snprintf(text,size,"%s",difficulty[choice]);
 else if(id<=1003||id==1013){if(choice==14)snprintf(text,size,"DeathMatch");else snprintf(text,size,"%usecs",30+choice*5);}
 else snprintf(text,size,"%s",matches[choice]);return 1;
}
int vo_native_check(VoNativeSettings *s,unsigned id){
 if(!s->host)return 0;
 if(s->category==0){switch(id){
 case 1056:return !!s->values[10];case 1057:return !s->values[10];case 1058:return s->values[9];case 1059:return !s->values[9];
 case 1068:return s->values[0]==2;case 1069:return s->values[0]!=2;
 case 1070:return !(s->values[7]&2)&&!s->values[8];case 1073:return !!(s->values[7]&2);case 1071:return !(s->values[7]&2)&&!!s->values[8];
 case 1075:return !!s->values[1];case 1077:return !!s->values[4];case 1079:return !!s->values[5];case 1078:return !!s->values[6];default:return 0;}}
 if(s->category==3){switch(id){case 1074:return !!(s->scratch[0x2d]&1);case 1075:return !!(s->scratch[0x2d]&2);case 1076:return !!s->scratch[0x2e];case 1079:return !!s->values[3];case 1080:return !!s->values[4];case 1081:return !!s->values[5];default:return 0;}}
 if(s->category==4){switch(id){case 1076:return !!s->values[0];case 1077:return !!s->values[1];case 1078:return s->values[2]==0x22b;case 1079:return s->values[2]==0x235;default:return 0;}}return 0;
}
int vo_native_click(VoNativeSettings *s,unsigned id){
 if(!s->host)return 0;
 if(s->category==0){int i=id==1075?1:id==1077?4:id==1079?5:id==1078?6:-1;if(i<0)return 0;s->values[i]=!s->values[i];return 1;}
 if(s->category==3){if(id==1074||id==1075){unsigned bit=id==1074?1:2;s->scratch[0x2d]^=bit;s->changed[0x2d]|=bit;}else if(id==1076){s->scratch[0x2e]=!s->scratch[0x2e];s->changed[0x2e]=255;}else if(id>=1079&&id<=1081){s->values[id-1076]=!s->values[id-1076];s->value_mask|=1u<<(id-1076);}else return 0;return 1;}
 if(s->category==4&&(id==1076||id==1077)){s->values[id-1076]=!s->values[id-1076];s->value_mask|=1u<<(id-1076);return 1;}return 0;
}
int vo_native_radio(VoNativeSettings *s,unsigned first,unsigned last,unsigned id){
 if(!s->host||id<first||id>last)return 0;
 if(s->category==4&&(id==1078||id==1079)){s->values[2]=id==1078?0x22b:0x235;s->value_mask|=4;return 1;}
 if(s->category)return 0;
 switch(id){case 1056:case 1057:s->values[10]=id==1056;break;case 1058:case 1059:s->values[9]=id==1058;break;case 1068:case 1069:s->values[0]=id==1068?2:1;break;case 1070:case 1071:case 1073:s->values[7]=(s->values[7]&~2u)|(id==1073?2:0);s->values[8]=id==1071;break;default:return 0;}return 1;
}
int vo_native_defaults(VoNativeSettings *s){
 if(!s->host)return 0;
 if(s->category==1){for(unsigned i=1000;i<=1007;i++)vo_native_select(s,i,i==1001?6:i<=1003?12:i==1007?1:0);}
 else if(s->category==2){vo_native_select(s,1013,12);vo_native_select(s,1014,0);}
 else if(s->category==3){s->scratch[0x2d]|=3;s->scratch[0x2e]=1;s->scratch[0x28]=1;s->scratch[0x2b]=0;s->changed[0x2d]|=3;s->changed[0x2e]=s->changed[0x28]=s->changed[0x2b]=255;}
 else if(s->category==4){s->values[0]=s->values[1]=0;s->value_mask|=3;}
 else if(s->category==5){
  memcpy(s->scratch+0x14c,(void*)(uintptr_t)(s->edition?0x5f35e8:0x601d08),0x50);
  memcpy(s->scratch+0x19c,(void*)(uintptr_t)(s->edition?0x5f3638:0x601d58),0x78);
  memset(s->scratch+0xac,0,0xa0);memset(s->changed+0xac,255,0x168);
 }else return 0;return 1;
}
int vo_native_commit(VoNativeSettings *s){
 if(!s->host)return 0;
 if(s->category){
  /* Gameplay can update bookkeeping while the overlay is open. Merge only
   * explicitly edited bits/fields into a fresh original-authority snapshot. */
  VoNativeSettings current={0};current.edition=s->edition;f6(&current,0);
  for(unsigned i=0;i<sizeof s->scratch;i++)current.scratch[i]=(current.scratch[i]&~s->changed[i])|(s->scratch[i]&s->changed[i]);
  for(unsigned i=0;i<6;i++)if(s->value_mask&(1u<<i))current.values[i]=s->values[i];
  f6(&current,1);memcpy(s->scratch,current.scratch,sizeof s->scratch);memcpy(s->values,current.values,sizeof s->values);
  memset(s->changed,0,sizeof s->changed);s->value_mask=0;return 1;
 }
 for(unsigned i=0;i<9;i++)WORD_AT(graphics[s->edition][i])=i==7?s->values[i]&~1u:s->values[i];
 WORD_AT(s->ui+0x1ec8)=s->values[10];
 WORD_AT(s->edition?0x67d778:0x6817f0)=s->values[9]?0:0xffffffff;
 WORD_AT(s->edition?0x67d750:0x6817c8)=s->values[9]?1:0;
 /* Original field-rich/normal update routines. */
 ((void(__cdecl*)(void))(uintptr_t)(s->edition?(s->values[9]?0x4937ca:0x4938b1):(s->values[9]?0x494cf7:0x494dde)))();
 s->finish();return 1;
}

/* Original bookkeeping records, original formatting strings and machine names.
 * This is presentation only; Clear/Save share the original F6 snapshot/apply. */
int vo_native_score(VoNativeSettings *s,unsigned group,unsigned row,char *text,unsigned size){
 if(!s->host||s->category!=5||!text||!size||group>2||row>=(group==2?8u:10u))return 0;
 uintptr_t names=s->edition?0x6b8020:0x6bc2c0, ranks=s->edition?0x6b7fe0:0x6bc280;
 uintptr_t formats=s->edition?0x6b804c:0x6bc2ec;
 if(group<2){
  const unsigned char *r=s->scratch+(group?0x19c+row*12:0x14c+row*8);
  char name[4]={r[0],r[1],r[2],0};for(unsigned i=0;i<3;i++)if(name[i]=='|')name[i]='.';
  const char *machine=r[3]<10?((const char**)names)[r[3]]:"Unknown";
  unsigned value;memcpy(&value,r+4,4);
  if(!group){
   if(value==0xffffffff)snprintf(text,size,(const char*)(formats+0x1c),(const char*)(ranks+row*6));
   else snprintf(text,size,(const char*)formats,(const char*)(ranks+row*6),value/48/60,value/48%60,(value%48)*99/48,name,machine);
  }else{unsigned losses;memcpy(&losses,r+8,4);snprintf(text,size,(const char*)(formats+0x38),(const char*)(ranks+row*6),value,losses,name,machine);}
 }else{
  unsigned order[8]={0,1,2,3,4,5,6,7},count[10],total=0;
  for(unsigned i=0;i<10;i++){memcpy(count+i,s->scratch+0xac+16*i,4);total+=count[i];}
  if((int)total<=0)total=1;
  for(unsigned i=1;i<8;i++){unsigned k=order[i],n=i;while(n&&count[k]>count[order[n-1]]){order[n]=order[n-1];n--;}order[n]=k;}
  unsigned i=order[row];snprintf(text,size,(const char*)(formats+0x68),((const char**)names)[i],count[i],count[i]*100/total);
 }
 return 1;
}
