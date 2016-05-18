class MyClassA
{
    MyClassA() {}
public:
    MyClassA(int a) {}
};


MyClassA factory()
{
    return MyClassA(5);
}
