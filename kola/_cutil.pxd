from libc.stdio cimport FILE
from libc.stdint cimport uint8_t, uint64_t
from cpython cimport PyObject


cdef extern from "<stdarg.h>":
    ctypedef struct va_list
    void va_start(va_list ap, const char* last_arg) nogil
    void va_end(va_list ap) nogil

cdef extern from "Python.h":
    PyObject* _PyType_Lookup(type t, str name)
    
    ctypedef uint64_t Py_UCS4
    
    str PyUnicode_FromFormat(const char* format, ...)
    Py_UCS4 PyUnicode_READ_CHAR(str unicode, Py_ssize_t index)
    int PyUnicode_WriteChar(
        str unicode, Py_ssize_t index, Py_UCS4 character) except -1

    enum PyUnicode_Kind:
        PyUnicode_WCHAR_KIND = 0
        PyUnicode_1BYTE_KIND = 1
        PyUnicode_2BYTE_KIND = 2
        PyUnicode_4BYTE_KIND = 4

    ctypedef struct _PyUnicodeWriter:
        PyObject* buffer
        void* data
        PyUnicode_Kind kind
        Py_UCS4 maxchar
        Py_ssize_t size
        Py_ssize_t pos

        # minimum number of allocated characters (default: 0)
        Py_ssize_t min_length

        # minimum character (default: 127, ASCII)
        Py_UCS4 min_char

        # If non-zero, overallocate the buffer (default: 0).
        unsigned char overallocate

        # If readonly is 1, buffer is a shared string (cannot be modified)
        # and size is set to 0.
        unsigned char readonly_ "readonly"
    
    void _PyUnicodeWriter_Init(_PyUnicodeWriter *writer)
    int _PyUnicodeWriter_Prepare(_PyUnicodeWriter *writer, Py_ssize_t length, Py_UCS4 maxchar) except -1
    int _PyUnicodeWriter_PrepareKind(_PyUnicodeWriter *writer, PyUnicode_Kind kind) except -1
    int _PyUnicodeWriter_WriteChar(_PyUnicodeWriter *writer, Py_UCS4 ch) except -1
    int _PyUnicodeWriter_WriteStr(_PyUnicodeWriter *writer, str string) except -1
    int _PyUnicodeWriter_WriteASCIIString(_PyUnicodeWriter *writer, const char* string, Py_ssize_t len) except -1
    str _PyUnicodeWriter_Finish(_PyUnicodeWriter *writer)
    void _PyUnicodeWriter_Dealloc(_PyUnicodeWriter *writer)


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
        ANNOTATION
    const uint8_t yy_goto[7][8]

    const int LFLAG_DISABLED
    const int LFLAG_ISANNOTATION
    const int LFLAG_NOLSTRIP
    
    ctypedef struct LexerData:
        const char* filename
        uint8_t command_threshold
        uint8_t flag
    ctypedef void* yyscan_t

    void kola_set_error(object exc_type, int errorno, const char* filename, int lineno, const char* text) except *
    void kola_set_errcause(object exc_type, int errorno, const char* filename, int lineno, const char* text, object cause) except *

    FILE* kola_open(object raw_path, PyObject** out, const char* mod) except NULL

    const char* get_type_name(object obj) nogil
    const char* get_type_qualname(object obj) nogil
    const char* unicode2string(str __s, Py_ssize_t* s_len) except NULL
    str decode_escapes(const char* string, Py_ssize_t len)
    str filter_text(str string)
