from libc.stdio cimport FILE
from libc.stdint cimport uint8_t
from cpython cimport PyObject

cdef extern from "_cutil.h":
    enum TokenSyn:
        CMD
        CMD_N
        TEXT
        LITERAL
        STRING
        NUM
        NUM_H
        NUM_B
        NUM_F
        CLN
        CMA
        SLP
        SRP
    const uint8_t yy_goto[7][8]
    void kola_set_error(object exc_type, int errorno, const char* filename, int lineno, const char* text) except *
    void kola_set_errcause(object exc_type, int errorno, const char* filename, int lineno, const char* text, object cause) except *

    const char* unicode2string(str __s, Py_ssize_t* s_len) except NULL
    str decode_escapes(const char* string, Py_ssize_t len)
    PyObject* filter_text(str string) except NULL

    FILE* kola_open(object raw_path, PyObject** out, const char* mod) except NULL