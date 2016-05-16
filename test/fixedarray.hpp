#include <string>
#include <sstream>


std::string toString(double myArray[5])
{
    std::stringstream ss;
    ss << "[";
    for(unsigned int i = 0; i < 5; i++)
    {
        ss << myArray[i];
        if(i < 4)
            ss << ", ";
    }
    ss << "]";
    return ss.str();
}
