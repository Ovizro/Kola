from libc.stdio cimport stdin, puts
from cpython cimport PyObject, PyLong_FromString, PyFloat_FromString, PyUnicode_FromStringAndSize, \
    PyUnicode_FromFormat, PyErr_Format, PY_MINOR_VERSION
from ._lexer cimport *


cdef extern from "Python.h":
    """
    #include "frameobject.h"
    void __inline kola_set_error(PyObject* exc_type, const char* filename, int lineno, char* text) {
        const char* format = "unknown symbol '%s'";
        if (*text == '\\n') format = "end of line in incurrect place";
        PyErr_Format(exc_type, format, text);

    #if PY_VERSION_HEX >= 0x03080000
        _PyTraceback_Add("<koilang>", filename, lineno);
    #else
        PyCodeObject* code = NULL;
        PyFrameObject* frame = NULL;
        PyObject* globals = NULL;
        PyObject *exc, *val, *tb;

        PyErr_Fetch(&exc, &val, &tb);

        globals = PyDict_New();
        if (!globals) goto end;
        code = PyCode_NewEmpty(filename, "<compile>", lineno);
        if (!code) goto end;
        frame = PyFrame_New(
            PyThreadState_Get(),
            code,
            globals,
            NULL
        );
        if (!frame) goto end;

        frame->f_lineno = lineno;
        PyErr_Restore(exc, val, tb);
        PyTraceBack_Here(frame);

    end:
        Py_XDECREF(code);
        Py_XDECREF(frame);
        Py_XDECREF(globals);
    #endif
    }
    """
    void kola_set_error(object exc_type, const char* filename, int lineno, char* text) except *


cdef class Token:
    cdef readonly:
        TokenSyn syn
        object val


cdef class BaseLexer:
    cdef:
        char* _filename
        YY_BUFFER_STATE buffer
    cdef readonly int lineno

    cpdef void ensure(self)
    cpdef void close(self)
    cdef void set_error(self) except *
    cdef Token next_koken(self)