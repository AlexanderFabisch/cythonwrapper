# Example

This is a little example for demonstration purposes. You can build and test
the Cython extenion with the following commands:

```
$ pywrap -h
... prints the help message

$ pywrap test*.hpp --modulename test --outdir out

$ cd out/

$ python setup.py build_ext -i
...

$ cp ../test.py .

$ python test.py 
...
```

Take a look at the header files, the test script and the generated
Cython files to find out what happens under the hood.

