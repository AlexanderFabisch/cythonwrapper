#ifndef TEST_HPP
#define TEST_HPP

#include <string>
#include <vector>
#include <iostream>
#include <stdexcept>

namespace test {

class A
{
    double* vec;
    unsigned size;
public:
    A() : vec(0), size(0)
    {
    }

    ~A()
    {
        if(vec)
            delete[] vec;
    }

    void set_vec(double* vec, unsigned size)
    {
        if(this->vec)
            delete[] this->vec;
        this->vec = new double[size];
        for(unsigned i = 0; i < size; i++)
            this->vec[i] = vec[i];
        this->size = size;
    }

    void get_vec(double* vec, unsigned size)
    {
        if(!this->vec || size != this->size)
            throw std::invalid_argument("Bullshit!");
        for(unsigned i = 0; i < size; i++)
            vec[i] = this->vec[i];
    }

    void p()
    {
        for(unsigned i = 0; i < size; i++)
            std::cout << vec[i] << ", ";
        std::cout << std::endl;
    }
};

}

#endif TEST_HPP
