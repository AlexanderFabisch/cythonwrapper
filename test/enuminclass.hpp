#include <string>


class MyEnumClass
{
public:
    enum MyEnum
    {
        FIRSTOPTION,
        SECONDOPTION,
        THIRDOPTION
    };

    static std::string enumToString(MyEnum e)
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
};
