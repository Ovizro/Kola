#ifndef _INCLUDE_HELPER_
#define _INCLUDE_HELPER_ 

#include <stdint.h>

enum TokenSyn {
    CMD=1, CMD_N, TEXT, LITERAL, STRING, NUM, NUM_H, NUM_B, NUM_F, CLN, CMA, SLP, SRP
} TokenSyn;

static const uint8_t yy_goto[7][8] = {
    15,  63,  0,   0,   0,  0,   0, 0,     // CMD | CMD_N | TEXT
    34,  162, 35,  117, 0,  151, 0, 40,    // LITERAL   
    17,  49,  35,  117, 0,  151, 0, 40,    // NUM | STRING
    0,   0,   134, 0,   0,  0,   0, 6,     // CLN
    0,   0,   100, 0,   4,  0,   8, 0,     // CMA
    0,   3,   0,   0,   0,  0,   0, 0,     // SLP
    0,   0,   65,  0,   81, 0,   81, 0     // SRP
};


#ifdef Py_PYTHON_H
#define ERR_MSG(msg) return "[%d]" # msg

static const char* get_format(int code) {
    switch (code)
    {
    case 1:
        ERR_MSG(unknown symbol '%s');
    case 10:
        ERR_MSG(end of line in incurrect place);
    
    default:
        ERR_MSG(unknown syntax);
    }
}

#include "frameobject.h"
// For Cython limiting, error setting function has to define here 
static void __inline kola_set_error(PyObject* exc_type, int errorno,
                            const char* filename, int lineno, char* text) 
{
    PyErr_Format(exc_type, get_format(errorno), errorno, text);

    // add traceback in .kola file
#if PY_VERSION_HEX >= 0x03080000
    _PyTraceback_Add("<kola>", filename, lineno);
#else
    PyCodeObject* code = NULL;
    PyFrameObject* frame = NULL;
    PyObject* globals = NULL;
    PyObject *exc, *val, *tb;

    PyErr_Fetch(&exc, &val, &tb);

    globals = PyDict_New();
    if (!globals) goto end;
    code = PyCode_NewEmpty(filename, "<kola>", lineno);
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
#endif

#endif