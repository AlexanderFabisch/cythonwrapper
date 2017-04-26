CXX := c++
LIBNAME := libmylib.so

all: $(LIBNAME)

$(LIBNAME):
	$(CXX) mylib.cpp -shared -o $(LIBNAME)

clean:
	rm $(LIBNAME)