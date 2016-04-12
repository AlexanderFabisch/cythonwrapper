#include <vector>
#include <string>
#include <sstream>


struct A
{
    int a;
    std::vector<double> b;
};


std::string print_mystruct(const A& a)
{
    std::stringstream ss;
    ss << "a = " << a.a << ", ";
    for(unsigned i = 0; i < a.b.size(); i++)
        ss << "b[" << i << "] = " << a.b[i] << ", ";
    return ss.str();
}
