class MyClassA
{
    void operator=(const MyClassA& other) {}
public:
    MyClassA() {}
};


MyClassA factory()
{
    return MyClassA(5);
}
