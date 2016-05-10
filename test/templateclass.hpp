template<typename T>
class A
{
    T a;
public:
    A(T a) : a(a) {}
    T get()
    {
        return a;
    }
};