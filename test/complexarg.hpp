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
    const A& a;
public:
    B(const A& a) : a(a) {}
    std::string getString()
    {
        return a.getString();
    }
};