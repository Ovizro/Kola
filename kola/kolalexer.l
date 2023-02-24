%option noyywrap yylineno

%{
    #include <string.h>
    #include "_cutil.h"

    #define ECHO yyterminate()
    #define YY_DECL int yylex(int command_threshold)
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
float_e (e|E)-?{digit}+
float   ((({sigint}\.{digit}*)|(-?\.{digit}+)){float_e}?)|({sigint}{float_e})
literal {letter_}({letter_}|{digit})*
string  \"([^\"]|(\\\r?\n)|(\\\"))*\"
plain   ([^\r\n]|(\\\r?\n))+
text    [^#\n\r \t]{plain}*

%s COMMAND
%s COMMENT
%s PLAIN_TEXT
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
<INITIAL>#+             {
    if (yyleng == command_threshold) {
        BEGIN COMMAND;
    } else if (yyleng > command_threshold) {
        BEGIN COMMENT;
        yymore();
    } else {
        BEGIN PLAIN_TEXT;
        yymore();
    }
}
<COMMAND>{literal}      {BEGIN ARGUMENT; return(CMD);}
<COMMAND>{uint}         {BEGIN ARGUMENT; return(CMD_N);}
<COMMENT>{plain}        {return(ANNOTATION);}
<PLAIN_TEXT>{plain}     {return(TEXT);}
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
<<EOF>>                 {
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