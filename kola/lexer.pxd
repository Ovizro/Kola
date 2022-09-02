from libc.stdio cimport stdin, FILE, fopen, fclose, EOF
from libc.string cimport strchr
from cpython cimport PyObject, PyLong_FromString, PyFloat_FromString, PyUnicode_FromStringAndSize, \
    PyBytes_FromStringAndSize, PyErr_Format, PY_MINOR_VERSION

from ._helper cimport *


cdef extern from *:
    str PyUnicode_FromFormat(const char*, ...)


cdef extern from "_helper.h":
    struct yy_buffer_state:
        pass
    ctypedef yy_buffer_state *YY_BUFFER_STATE

    char* yytext
    int yyleng
    int yylineno
    YY_BUFFER_STATE yy_current_buffer

    int get_stat()
    void set_stat(int stat)

    int yylex() nogil
    void yyrestart(FILE *input_file) nogil
    YY_BUFFER_STATE yy_create_buffer(FILE* file, int size) nogil
    YY_BUFFER_STATE yy_scan_buffer(char * text, Py_ssize_t size) nogil
    YY_BUFFER_STATE yy_scan_bytes(const char * text, int len) nogil
    void yy_switch_to_buffer(YY_BUFFER_STATE new_buffer) nogil
    void yy_flush_buffer(YY_BUFFER_STATE b) nogil
    void yy_delete_buffer(YY_BUFFER_STATE b) nogil


cdef class Token:
    cdef:
        Token next     # used in grammar parser
    cdef readonly:
        TokenSyn syn
        object val
        bytes raw_val
        int lineno
    
    cpdef int get_flag(self)
    

cdef class BaseLexer:
    cdef:
        char* _filename
        YY_BUFFER_STATE buffer
    cdef readonly:
        int lineno
        int stat

    cpdef void ensure(self)
    cpdef void close(self)
    cdef void set_error(self) except *
    cdef Token next_token(self)


cdef class FileLexer(BaseLexer):
    cdef:
        bytes _filenameo
        FILE* fp
    
    cpdef void close(self)


cdef class StringLexer(BaseLexer):
    cdef readonly bytes content