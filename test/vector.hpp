#ifndef TEST_HPP
#define TEST_HPP

class A
{
public:
    double norm(double* vec, unsigned size)
    {
      double norm = 0.0;
      for(unsigned i = 0; i < size; i++)
        norm += vec[i] * vec[i];
      return norm;
    }
};

#endif
