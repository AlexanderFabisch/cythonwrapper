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

    void setVec(double* vec, unsigned size)
    {
        if(this->vec)
            delete[] this->vec;
        this->vec = new double[size];
        for(unsigned i = 0; i < size; i++)
            this->vec[i] = vec[i];
        this->size = size;
    }

    void getVec(double* vec, unsigned size)
    {
        if(!this->vec || size != this->size)
            throw std::invalid_argument("Bullshit!");
        for(unsigned i = 0; i < size; i++)
            vec[i] = this->vec[i];
    }

    bool isEmpty()
    {
        return size == 0;
    }

    void p()
    {
        for(unsigned i = 0; i < size; i++)
            std::cout << vec[i] << ", ";
        std::cout << std::endl;
    }

    std::string info()
    {
        return std::string("This class contains a raw double array.");
    }
};

}

#endif TEST_HPP
