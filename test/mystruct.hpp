#include <vector>
#include <sstream>


struct A
{
    int a;
    std::vector<double> b;
};


std::string print_mystruct_a(const A& a)
{
    std::stringstream ss;
    ss << "a = " << a.a << ", ";
    for(unsigned i = 0; i < a.b.size(); i++)
        ss << "b[" << i << "] = " << a.b[i] << ", ";
    return ss.str();
}


typedef struct
{
    int a;
} B;


std::string print_mystruct_b(const B& b)
{
    std::stringstream ss;
    ss << "a = " << b.a;
    return ss.str();
}
