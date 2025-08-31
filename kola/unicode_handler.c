#include "Python.h"
#include "_cutil.h"

#ifdef HAVE_WCHAR_H
    #include <wchar.h>
#endif

PyObject* _decode_utf8(const char **sPtr, const char *end)
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
PyObject* decode_escapes(const char* s, Py_ssize_t len) {
    PyObject *v = NULL;

    /* check for integer overflow */
    if ((uint64_t)len > SIZE_MAX / 6) {
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
                p--;
                s += 2;
                if (s >= end) {
                    break;
                }
            } else if (*s == '\n') {
                p--;
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

PyObject* filter_text(PyObject* string) {
    Py_ssize_t len = PyUnicode_GET_LENGTH(string);
    Py_UCS4 maxchar = PyUnicode_MAX_CHAR_VALUE(string);
    PyObject* result = PyUnicode_New(len, maxchar);
    if (!result) {
        return NULL;
    }
    
    Py_ssize_t offset = 0;
    Py_ssize_t new_len = 0;
    
    for (Py_ssize_t i = 0; i < len; ++i) {
        Py_UCS4 chr = PyUnicode_READ_CHAR(string, i);
        if (chr == '\\') {
            offset++;
            i++;
            if (i >= len) {
                if (PyUnicode_WriteChar(result, new_len, '\\') == -1)
                    goto bad;
                new_len++;
                break;
            }
            
            Py_UCS4 tc = PyUnicode_READ_CHAR(string, i);
            switch (tc) {
            case '\n':
                offset++;
                break;
            case '\r':
                if (i + 1 < len && PyUnicode_READ_CHAR(string, i + 1) == '\n') {
                    i++;
                    offset += 2;
                }
                break;
            default:
                if (PyUnicode_WriteChar(result, new_len, '\\') == -1)
                    goto bad;
                new_len++;
                if (PyUnicode_WriteChar(result, new_len, tc) == -1)
                    goto bad;
                new_len++;
                offset--;
                break;
            }
        } else {
            if (PyUnicode_WriteChar(result, new_len, chr) == -1)
                goto bad;
            new_len++;
        }
    }
    
    if (new_len != len) {
        if (PyUnicode_Resize(&result, new_len) < 0) {
            goto bad;
        }
    }
    
    return result;

bad:
    Py_DECREF(result);
    return NULL;
}