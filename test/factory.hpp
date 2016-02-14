class A
{
public:
    A() {}
    int get()
    {
        return 5;
    }
};

class AFactory
{
public:
    A* make()
    {
        return new A();
    }
};