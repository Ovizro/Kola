%option noyywrap
%option yylineno
%option reentrant
%option outfile="kola/lex.yy.c"

%{
    #include <string.h>
    #include "_cutil.h"

    #define yy_command_threshold    yyextra->command_threshold
    #define yy_lflag                yyextra->flag
    #define yy_is_annotation        (yy_lflag & LFLAG_ISANNOTATION)
    #define yy_lstrip               (yy_lflag & LFLAG_NOLSTRIP)
    #define yyset_annotation()      do {yy_lflag |= LFLAG_ISANNOTATION;} while (0)
    #define yyunset_annotation()    do {yy_lflag &= ~LFLAG_ISANNOTATION;} while (0)

    #define ECHO yyterminate()

    #define YY_NO_UNISTD_H

    #ifdef _MSC_VER
        #include <io.h>
        #include <process.h>
    #else
        #include <unistd.h>
    #endif
%}

delim   [ \t]
ws      {delim}+
letter  [A-Za-z_]
digit   [0-9]
uint    ([1-9]{digit}*|0)
sigint  (-?{uint})
hex     0x[0-9A-Fa-f]+
bin     0b[01]+
float_e (e|E)-?{digit}+
float   ((({sigint}\.{digit}*)|(-?\.{digit}+)){float_e}?)|({sigint}{float_e})
literal {letter}({letter}|{digit})*
string  \"([^\"]|(\\\r?\n)|(\\\"))*\"
plain   ([^\r\n]|(\\\r?\n))+

%s COMMAND
%s PLAIN_TEXT
%s ARGUMENT

%%

{ws}                            {
    if (YY_START == INITIAL && yy_lstrip) yymore();
}
\\\r?\n                         {}
\r?\n                           {
    if (YY_START == COMMAND) {
        yyterminate();
    }
    BEGIN INITIAL;
}
<INITIAL>#+             {
    size_t prefix_len = yyleng - (size_t)(strchr(yytext, '#') - yytext);
    
    if (prefix_len == yy_command_threshold) {
        BEGIN COMMAND;
    }  else {
        if (prefix_len > yy_command_threshold) {
            yyset_annotation();
        } else {
            yyunset_annotation();
        }
        BEGIN PLAIN_TEXT;
        yyless(0);
    }
}
<INITIAL>[^#\n\r \t]    {BEGIN PLAIN_TEXT; yyless(0);}
<COMMAND>{literal}      {BEGIN ARGUMENT; return(CMD);}
<COMMAND>{uint}         {BEGIN ARGUMENT; return(CMD_N);}
<PLAIN_TEXT>{plain}     {return yy_is_annotation? ANNOTATION : TEXT;}

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

int yylex_check(yyscan_t yyscanner) {
    struct yyguts_t * yyg = (struct yyguts_t*)yyscanner;
    if (yy_lflag & LFLAG_DISABLED) return 0;
    return YY_CURRENT_BUFFER != NULL;
}