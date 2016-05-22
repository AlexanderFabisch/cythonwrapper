import os
import sys
from .cython import make_cython_wrapper, write_files, run_setup
from .utils import remove_files
from .defaultconfig import Config


class CppFinder(object):
    def __init__(self, import_path="."):
        self.config = Config()
        self.import_path = import_path

    def find_module(self, fullname, path):
        header_ending = None
        for ending in self.config.cpp_header_endings:
            if os.path.exists(fullname + "." + ending):
                header_ending = ending
                break
        if header_ending is None:
            return None

        header = fullname + "." + header_ending
        lib = fullname + ".so"
        if not os.path.exists(lib):
            files = make_cython_wrapper(header, [], config=self.config)
            files["setup_import.py"] = files["setup.py"]
            del files["setup.py"]

            write_files(files)
            try:
                run_setup("setup_import.py")
            finally:
                filenames = [fullname + ".cpp"]
                filenames.extend(files.keys())
                remove_files(filenames)

        return None


sys.meta_path.append(CppFinder())
