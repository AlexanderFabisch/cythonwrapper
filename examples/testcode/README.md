# Example Rotations

This is a little example for demonstration purposes. You can build and test
the Cython extenion with the following commands:

```
$ pywrap -h
... prints the help message

$ pywrap *.hpp --modulename rotations --outdir result

$ cd result/

$ python setup.py build_ext -i
...

$ python example.py
...
```

Take a look at the header files, the test script and the generated
Cython files to find out what happens under the hood.
