#include <string>


class ClassA
{
public:
    class ClassB
    {
    public:
        int myfun()
        {
            return 123;
        }

        static int mystatfun()
        {
            return 124;
        }
    };
};
