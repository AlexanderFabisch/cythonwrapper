#include <string>


enum MyEnum
{
    FIRSTOPTION,
    SECONDOPTION,
    THIRDOPTION
};


std::string enumToString(MyEnum e)
{
    switch(e)
    {
    case FIRSTOPTION:
        return "first";
    case SECONDOPTION:
        return "second";
    case THIRDOPTION:
        return "third";
    default:
        return "invalid";
    }
}
