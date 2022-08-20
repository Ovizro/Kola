from libc.stdio cimport FILE, EOF, fopen, fclose

cdef extern from "lex.yy.c":
    enum TokenSyn:
        CMD
        CMD_N
        TEXT
        CONCAT
        LITERAL
        STR
        NUM
        NUM_H
        NUM_B
        NUM_F
        CLN
        CMA
        SLP
        SRP

    struct yy_buffer_state:
        pass
    ctypedef yy_buffer_state *YY_BUFFER_STATE

    char* yytext
    int yyleng
    int yylineno
    YY_BUFFER_STATE yy_current_buffer

    int yylex() nogil
    void yyrestart(FILE *input_file) nogil
    YY_BUFFER_STATE yy_create_buffer(FILE* file, int size) nogil
    YY_BUFFER_STATE yy_scan_bytes(const char * text, int len) nogil
    void yy_switch_to_buffer(YY_BUFFER_STATE new_buffer) nogil
    void yy_flush_buffer(YY_BUFFER_STATE b) nogil
    void yy_delete_buffer(YY_BUFFER_STATE b) nogil