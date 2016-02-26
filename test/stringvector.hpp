#ifndef TEST_HPP
#define TEST_HPP

#include <string>
#include <vector>
#include <sstream>

class A
{
public:
    std::string concat(const std::vector<std::string>& substrings)
    {
        std::stringstream ss;
        for(unsigned i = 0; i < substrings.size(); i++)
          ss << substrings[i];
        return ss.str();
    }
};

#endif TEST_HPP
