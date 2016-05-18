class MyClassA
{
    void operator=(const MyClassA& other) {}
public:
    MyClassA() {}
    MyClassA(int a) {}
};


MyClassA factory()
{
    return MyClassA(5);
}
