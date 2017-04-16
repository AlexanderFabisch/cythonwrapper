import os
from clang import cindex


def _find_clang():
    """Find installation of libclang.

    python-clang does not know where to find libclang, so we have to do this
    here almost manually.
    """
    SUPPORTED_VERSIONS = ["3.8", "3.7", "3.6", "3.5"]
    for clang_version in SUPPORTED_VERSIONS:
        lib_path = "/usr/lib/llvm-%s/lib/" % clang_version
        if os.path.exists(lib_path):
            cindex.Config.set_library_path(lib_path)
            lib_file = os.path.join(
                lib_path, "libclang-%s.so" % clang_version)
            clang_incdir = "/usr/lib/clang/%s.0/include/" % clang_version
            if not os.path.exists(clang_incdir):
                raise ImportError("Could not find clang include directory. "
                                  "Checked '%s'." % clang_incdir)
            if not os.path.exists(lib_file):
                continue
            return clang_version, clang_incdir
    raise ImportError("Could not find a valid installation of libclang-dev. "
                      "Only versions %s are supported at the moment."
                      % SUPPORTED_VERSIONS)


# This must be done globally and exactly once:
CLANG_VERSION, CLANG_INCDIR = _find_clang()
