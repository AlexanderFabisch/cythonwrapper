#include <string>


class MyClassA
{
    int i;
public:
    MyClassA(int i = 5) : i(i) {}
    int mult(int j = 6)
    {
        return i * j;
    }
    int multDouble(double d = 7.0)
    {
        return (double) i * d;
    }
    int half(bool b = false)
    {
        if(b)
            return i / 2;
        else
            return i;
    }
    std::string append(std::string s = "abc")
    {
        return s + "def";
    }
};