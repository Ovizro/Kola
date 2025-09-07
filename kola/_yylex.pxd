from libc.stdio cimport FILE
from ._cutil cimport yyscan_t, LexerData

cdef extern from "lex.yy.c":
    ctypedef LexerData* YY_EXTRA_TYPE
    ctypedef void* YY_BUFFER_STATE

    # main parser
    int yylex(yyscan_t yyscanner) nogil
    
    int yylex_init(yyscan_t* ptr_yy_globals) nogil
    int yylex_init_extra(YY_EXTRA_TYPE yy_user_defined, yyscan_t* ptr_yy_globals) nogil
    int yylex_destroy(yyscan_t yyscanner) nogil
    void yyrestart(FILE* input_file, yyscan_t yyscanner) nogil
    bint yylex_check(yyscan_t yyscanner) nogil

    # Accessor  methods (get/set functions) to struct members.
    int yyget_lineno(yyscan_t yyscanner) nogil
    int yyget_column(yyscan_t yyscanner) nogil
    FILE *yyget_in(yyscan_t yyscanner) nogil
    FILE *yyget_out(yyscan_t yyscanner) nogil
    int yyget_leng(yyscan_t yyscanner) nogil
    char* yyget_text(yyscan_t yyscanner) nogil
    void yyset_lineno(int _line_number, yyscan_t yyscanner) nogil
    void yyset_column(int _column_no , yyscan_t yyscanner) nogil
    void yyset_in(FILE* _in_str , yyscan_t yyscanner) nogil
    void yyset_out(FILE* _out_str , yyscan_t yyscanner) nogil

    void yypush_buffer_state(YY_BUFFER_STATE new_buffer, yyscan_t yyscanner) nogil
    void yypop_buffer_state(yyscan_t yyscanner) nogil
    YY_BUFFER_STATE yy_create_buffer(FILE* file, int size, yyscan_t yyscanner) nogil
    YY_BUFFER_STATE yy_scan_buffer(char* base, Py_ssize_t size, yyscan_t yyscanner) nogil
    YY_BUFFER_STATE yy_scan_bytes(const char* text, int len, yyscan_t yyscanner) nogil