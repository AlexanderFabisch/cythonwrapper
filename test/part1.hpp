#include "part2.hpp"

using namespace NamespaceB;


namespace NamespaceA
{

class ClassA
{
public:
    ClassA() {}
    ClassB* make()
    {
        return new ClassB;
    }
};

}