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
sigint  (-?{uint})
hex     0x[0-9A-Za-z]+
bin     0b[01]+
point   \.{digit}+
float   (({sigint}\.?{digit}*)|{point})(e|E-?{digit}+)?
literal {letter_}({letter_}|{digit})*
string  \"([^\"]|(\\\r?\n)|(\\\"))*\"
text    [^#\n\r \t]((.|\\\r?\n)*[^\r\n\\ \t])?

%s COMMAND
%s ARGUMENT

%%

{ws}                            {}
\\\r?\n                         {}
\r?\n                           {
    if (YY_START == COMMAND) {
        yyterminate();
    }
    BEGIN INITIAL;
}
<INITIAL>#              {BEGIN COMMAND;}
<COMMAND>{literal}      {BEGIN ARGUMENT; return(CMD);}
<COMMAND>{uint}         {BEGIN ARGUMENT; return(CMD_N);}
<INITIAL>{text}         {return(TEXT);}

<ARGUMENT>\(            {return(SLP);}
<ARGUMENT>\)            {return(SRP);}

<ARGUMENT>{string}      {return(STRING);}

<ARGUMENT>":"           {return(CLN);}
<ARGUMENT>\,            {return(CMA);}

<ARGUMENT>{sigint}      {return(NUM);}
<ARGUMENT>{hex}         {return(NUM_H);}
<ARGUMENT>{bin}         {return(NUM_B);}
<ARGUMENT>{float}       {return(NUM_F);}
<ARGUMENT>{literal}     {return(LITERAL);}
<<EOF>>                         {
    if (YY_START == COMMAND) {
        yyterminate();
    }
    return(EOF);
}

%%

int get_stat() {
    return YY_START;
}

void set_stat(int stat) {
    BEGIN stat;
}