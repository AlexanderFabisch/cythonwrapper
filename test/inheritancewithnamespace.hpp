namespace NamespaceA
{

class ClassA
{
public:
    int methodA()
    {
        return 1;
    }
};

}

namespace NamespaceB
{

class ClassB : public NamespaceA::ClassA
{
public:
    int methodB()
    {
        return 2;
    }
};

}
