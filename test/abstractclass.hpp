class AbstractClass
{
protected:
    AbstractClass() {}
public:
    virtual ~AbstractClass() {}
    virtual double square() = 0;
    virtual AbstractClass* clone() = 0;
};

class DerivedClass : public AbstractClass
{
    double d;
public:
    DerivedClass(double d) : d(d) {}

    virtual double square()
    {
        return d * d;
    }

    virtual AbstractClass* clone()
    {
        return new DerivedClass(d);
    }
};
