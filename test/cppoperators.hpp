class Operators
{
public:
    int operator()(int a)
    {
        return 2 * a;
    }

    int operator[](int a)
    {
        return a;
    }
};
