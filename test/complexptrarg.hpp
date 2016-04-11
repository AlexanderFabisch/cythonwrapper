#include <string>


class A
{
    std::string s;
public:
    A() : s("test") {}
    std::string getString() const
    {
        return s;
    }
};


class B
{
    A* a;
public:
    B(A* a) : a(a) {}
    std::string getString()
    {
        return a->getString();
    }
};
