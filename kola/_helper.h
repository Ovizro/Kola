#ifndef _INCLUDE_HELPER_
#define _INCLUDE_HELPER_ 

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

static enum TokenSyn {
    CMD=1, CMD_N, TEXT, LITERAL, STRING, NUM, NUM_H, NUM_B, NUM_F, CLN, CMA, SLP, SRP
} TokenSyn;

static const uint8_t yy_goto[7][8] = {
    {15,  63,  0,   0,   0,  0,   0, 0},     // CMD | CMD_N | TEXT
    {34,  162, 35,  117, 0,  151, 0, 40},    // LITERAL   
    {17,  49,  35,  117, 0,  151, 0, 40},    // NUM | STRING
    {0,   0,   134, 0,   0,  0,   0, 6},     // CLN
    {0,   0,   100, 0,   4,  0,   8, 0},     // CMA
    {0,   3,   0,   0,   0,  0,   0, 0},     // SLP
    {0,   0,   65,  0,   81, 0,   81, 0}     // SRP
};

#ifndef FLEX_SCANNER
struct yy_buffer_state;
typedef struct yy_buffer_state* YY_BUFFER_STATE;
extern int yylineno;
extern int yyleng;
extern char* yytext;

int get_stat();
void set_stat(int stat);

int yylex();
void yyrestart(FILE *input_file);

void yy_switch_to_buffer(YY_BUFFER_STATE new_buffer);
void yy_load_buffer_state();
YY_BUFFER_STATE yy_create_buffer(FILE *file, int size);
void yy_delete_buffer(YY_BUFFER_STATE b);
void yy_init_buffer(YY_BUFFER_STATE b, FILE *file);
void yy_flush_buffer(YY_BUFFER_STATE b);

YY_BUFFER_STATE yy_scan_buffer(char *base, size_t size);
YY_BUFFER_STATE yy_scan_string(const char *yy_str);
YY_BUFFER_STATE yy_scan_bytes(const char *bytes, int len);
#endif

#ifdef Py_PYTHON_H
#define ERR_CASE(syn, act) case (act << 4) + syn
#define ERR_MSG(msg) return "[%d] " # msg

static const char* get_format(int code) {
    switch (code)
    {
    case 1:
        ERR_MSG(unknown symbol '%s');
    case 2:
        ERR_MSG(command '%s' not found);
    case 3:
        ERR_MSG(an error occured during handling command '%s');
    case 4:
        ERR_MSG(an error occured during handling text '%s');
    case 5:
        ERR_MSG(cannot decode string %s);
    case 10:
        ERR_MSG(end of line in incurrect place);
    case 28:
        ERR_MSG(keyword must be a literal);
    case 201:
    case 202:
    case 210:
        ERR_MSG(bad argument count);
    }
    
    switch (code & 0x0F)
    {
    case CMD:
    case CMD_N:
    case TEXT:
        ERR_MSG(end of line in incurrect place);
    }
    ERR_MSG(unknown syntax);
}

#include "frameobject.h"
// For Cython limiting, error setting function has to define here 
static void __inline kola_set_error(PyObject* exc_type, int errorno,
                            const char* filename, int lineno, const char* text) 
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

static void __inline kola_set_errcause(PyObject* exc_type, int errorno,
                            const char* filename, int lineno, const char* text, PyObject* cause) 
{
    PyErr_Format(exc_type, get_format(errorno), errorno, text);
    
    PyObject *exc, *val, *tb;
    PyErr_Fetch(&exc, &val, &tb);
    if (cause == Py_None) {
        PyException_SetContext(val, NULL);
    } else {
        Py_INCREF(cause);
        PyException_SetCause(val, cause);
    }
    #if PY_VERSION_HEX >= 0x03080000
        PyErr_Restore(exc, val, tb);
        _PyTraceback_Add("<kola>", filename, lineno);
    #else
        PyCodeObject* code = NULL;
        PyFrameObject* frame = NULL;
        PyObject* globals = NULL;
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

static PyObject* _decode_utf8(const char **sPtr, const char *end)
{
    const char *s;
    const char *t;
    t = s = *sPtr;
    while (s < end && (*s & 0x80)) {
        s++;
    }
    *sPtr = s;
    return PyUnicode_DecodeUTF8(t, s - t, NULL);
}

// from cpython:string_parser.decode_unicode_with_escapes
static PyObject* decode_string(const char* s, Py_ssize_t len) {
    PyObject *v = NULL;

    /* check for integer overflow */
    if (len > SIZE_MAX / 6) {
        return NULL;
    }
    /* "ä" (2 bytes) may become "\U000000E4" (10 bytes), or 1:5
       "\ä" (3 bytes) may become "\u005c\U000000E4" (16 bytes), or ~1:6 */
    PyObject *u = PyBytes_FromStringAndSize((char *)NULL, len * 6);
    if (u == NULL) {
        return NULL;
    }

    char *buf;
    char *p;
    p = buf = PyBytes_AsString(u);
    if (p == NULL) {
        return NULL;
    }
    const char *end = s + len;
    while (s < end) {
        if (*s == '\\') {
            *p++ = *s++;
            if (s >= end || *s & 0x80) {
                strcpy(p, "u005c");
                p += 5;
                if (s >= end) {
                    break;
                }
            } else if (s + 1 < end && *s == '\r' && s[1] == '\n') {
                s += 2;
                if (s >= end) {
                    break;
                }
            } else if (*s == '\n') {
                s++;
                if (s >= end) {
                    break;
                }
            }
        }
        if (*s & 0x80) {
            PyObject *w;
            int kind;
            const void *data;
            Py_ssize_t w_len;
            Py_ssize_t i;
            w = _decode_utf8(&s, end);
            if (w == NULL) {
                Py_DECREF(u);
                return NULL;
            }
            kind = PyUnicode_KIND(w);
            data = PyUnicode_DATA(w);
            w_len = PyUnicode_GET_LENGTH(w);
            for (i = 0; i < w_len; i++) {
                Py_UCS4 chr = PyUnicode_READ(kind, data, i);
                sprintf(p, "\\U%08x", chr);
                p += 10;
            }
            /* Should be impossible to overflow */
            assert(p - buf <= PyBytes_GET_SIZE(u));
            Py_DECREF(w);
        }
        else {
            *p++ = *s++;
        }
    }
    len = p - buf;
    s = buf;
    v = PyUnicode_DecodeUnicodeEscape(s, len, NULL);
    return v;
}

static PyObject* filter_text(PyObject* string) {
    Py_ssize_t len = PyUnicode_GET_LENGTH(string);
    Py_ssize_t offset = 0;
    for (Py_ssize_t i = 0; i < len; ++i) {
        Py_UCS4 chr = PyUnicode_READ_CHAR(string, i);
        if (chr == '\\') {
            offset++;
            Py_UCS4 tc = PyUnicode_READ_CHAR(string, ++i);
            switch (tc) {
            case '\n':
                offset++;
                break;
            case '\r':
                if (PyUnicode_ReadChar(string, i + 1) == '\n') {
                    i++;
                    offset += 2;
                    break;
                }
            default:
                if (PyUnicode_WriteChar(string, i - offset, '\\') == -1) goto bad;
                if (PyUnicode_WriteChar(string, i - offset, tc) == -1) goto bad;
                break;
            }
        } else if (offset) {
            if (PyUnicode_WriteChar(string, i - offset, chr) == -1) goto bad;
        }
    }
    if (offset)
        PyUnicode_Resize(&string, len - offset);
    return string;
bad:
    return NULL;
}
#endif

#ifdef __cplusplus
}
#endif
#endif