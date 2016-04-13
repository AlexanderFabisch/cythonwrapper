class Operators
{
public:
    Operators() {}

    int operator()(int a)
    {
        return 2 * a;
    }

    int operator[](int a)
    {
        return a;
    }

    int operator+(int a)
    {
        return 5 + a;
    }

    int operator-(int a)
    {
        return 5 - a;
    }

    int operator*(int a)
    {
        return 5 * a;
    }

    int operator/(int a)
    {
        return 5 / a;
    }
};
