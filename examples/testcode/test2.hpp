#pragma once
#include "test1.hpp"
#include <iostream>

namespace test {

class B : public A
{
    unsigned size;
public:
    B(unsigned size) : size(size) {}
};

class Factory
{
public:
    A* make()
    {
        return new B(5);
    }
};

void shutdown()
{
    std::cout << "Shutting down" << std::endl;
}

}
