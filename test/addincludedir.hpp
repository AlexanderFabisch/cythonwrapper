#include "somefunction.hpp"

double length(double a, double b)
{
    const absA = a > 0 ? a : -a;
    const absB = b > 0 ? b : -b;
    return absA + absB;
}
