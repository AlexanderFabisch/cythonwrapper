#ifndef TEST_HPP
#define TEST_HPP

#include <string>
#include <vector>
#include <iostream>

namespace test {

class A
{
    int a;
public:
    A() : a(0)
    {
    }

    A(int a) : a(a)
    {
    }

    void p()
    {
        std::cout << a << std::endl;
    }
};

}

#endif TEST_HPP
