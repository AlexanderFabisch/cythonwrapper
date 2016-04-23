# Example tinyfiledialogs

This is an example that shows how we can wrap the library
[tinyfiledialogs](https://sourceforge.net/projects/tinyfiledialogs/).

Clone the repository into this directory:

    git clone git://git.code.sf.net/p/tinyfiledialogs/code tinyfiledialogs-code

Now, we can wrap the library:

```
$ pywrap tinyfiledialogs-code/tinyfiledialogs.h --sources tinyfiledialogs-code/tinyfiledialogs.c --modulename tfd --outdir result

$ cd result/

$ python setup.py build_ext -i
...

$ python example.py
```
