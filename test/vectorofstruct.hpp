#include <vector>

struct MyStruct
{
    int value;
    bool active;
};


int sumOfActivatedEntries(const std::vector<MyStruct>& entries)
{
    int sum = 0;
    for(unsigned i = 0; i < entries.size(); i++)
    {
        if(entries[i].active)
        {
            sum += entries[i].value;
        }
    }
    return sum;
}
