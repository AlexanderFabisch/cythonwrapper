class Base1
{
public:
    virtual ~Base1() {}
    virtual int base1Method()
    {
        return 1;
    }
};

class Base2 : public Base1
{
public:
    virtual int base2Method()
    {
        return 2;
    };
};

class A : public Base2
{
public:
    virtual int aMethod()
    {
        return 3;
    }
};

class B : public Base2
{
public:
    virtual int base1Method()
    {
        return 4;
    }

    virtual int bMethod()
    {
        return 5;
    }
};