template<typename T>
class A
{
public:
    T a;
    A(T a) : a(a) {}
    T get()
    {
        return a;
    }
};