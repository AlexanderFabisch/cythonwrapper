#pragma once
#include "deppart2.hpp"


class A
{
public:
    B* make()
    {
        return new B();
    }
};
