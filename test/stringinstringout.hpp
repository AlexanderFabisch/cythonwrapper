#include <string>


class A
{
    std::string concat(const std::string& s1, const std::string& s2)
    {
        return s1 + s2;
    }
public:
    std::string end(const std::string& s)
    {
        return concat(s, ".");
    }
};