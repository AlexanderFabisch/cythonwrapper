class A
{
public:
    virtual ~A() {}
    virtual int afun()
    {
        return 1;
    }
};

class B : public A
{
public:
    virtual int bfun()
    {
        return 2;
    }
};