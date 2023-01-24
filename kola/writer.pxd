from libc.stdio cimport FILE, fopen, fclose, fputs
from libc.stdint cimport uint8_t
from ._cutil cimport unicode2string


cdef extern from "Python.h":
    object PyOS_FSPath(object path)
    const char* PyUnicode_AsUTF8AndSize(str unicode, Py_ssize_t* size) except NULL


cdef class KoiLangWriter:
    cdef:
        FILE* fp
        Py_ssize_t cur_indent
    cdef readonly:
        object path
        str encoding
        uint8_t indent
