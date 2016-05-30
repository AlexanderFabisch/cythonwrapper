class Operators
{
public:
    int v;
    bool b;

    Operators() : v(0), b(false) {}

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

    int operator%(int a)
    {
        return 5 % a;
    }

    bool operator&&(bool b)
    {
        return true && b;
    }

    bool operator||(bool b)
    {
        return false || b;
    }

    Operators& operator+=(int a)
    {
        v += a;
        return *this;
    }

    Operators& operator-=(int a)
    {
        v -= a;
        return *this;
    }

    Operators& operator*=(int a)
    {
        v *= a;
        return *this;
    }

    Operators& operator/=(int a)
    {
        v /= a;
        return *this;
    }

    Operators& operator%=(int a)
    {
        v %= a;
        return *this;
    }

    Operators& operator&=(bool b)
    {
        this->b &= b;
        return *this;
    }

    Operators& operator|=(bool b)
    {
        this->b |= b;
        return *this;
    }
};
