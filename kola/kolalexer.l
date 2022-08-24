%option noyywrap yylineno

%{
    #include <string.h>
    #include "_helper.h"


    #define ECHO yyterminate()
%}

delim   [ \t]
ws      {delim}+
letter  [A-Za-z]
letter_ ({letter}|_)
digit   [0-9]
uint    ([1-9]{digit}*|0)
hex     0x[0-9A-Za-z]+
bin     0b[01]+
float   (-?{digit}+)(\.{digit}+)?(e-?{digit}+)?
literal {letter_}({letter_}|{digit})*
string  \"([^\"]|\\\r?\n|\\\")*\"
text    [^#\n\r \t]((.|\\\n)*[^\r\n\\ \t])?

%s COMMAND
%s ARGUMENT
%s ARGUMENT_D

%%

{ws}                            {}
\\\r?\n                         {}
\r?\n                           {
    if (YY_START != INITIAL && YY_START != ARGUMENT) {
        yyterminate();
    }
    BEGIN INITIAL;
}
<INITIAL>#                      {BEGIN COMMAND;}
<COMMAND>{literal}              {BEGIN ARGUMENT; return(CMD);}
<COMMAND>{uint}                 {BEGIN ARGUMENT; return(CMD_N);}
<INITIAL>{text}                 {return(TEXT);}

<ARGUMENT>\(                    {BEGIN ARGUMENT_D; return(SLP);}
<ARGUMENT_D>\)                  {BEGIN ARGUMENT; return(SRP);}

<ARGUMENT,ARGUMENT_D>{string}     {return(STRING);}

<ARGUMENT_D>":"                 {return(CLN);}
<ARGUMENT_D>\,                  {return(CMA);}

<ARGUMENT,ARGUMENT_D>{uint}     {return(NUM);}
<ARGUMENT,ARGUMENT_D>{hex}      {return(NUM_H);}
<ARGUMENT,ARGUMENT_D>{bin}      {return(NUM_B);}
<ARGUMENT,ARGUMENT_D>{float}    {return(NUM_F);}
<ARGUMENT,ARGUMENT_D>{literal}  {return(LITERAL);}
<<EOF>>                         {
    if (YY_START != INITIAL && YY_START != ARGUMENT) {
        yyterminate();
    }
    return(EOF);
}

%%