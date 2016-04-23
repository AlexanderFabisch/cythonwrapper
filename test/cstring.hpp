int length(char const * const input)
{
    int i = 0;
    while(input[i] != 0)
        i++;
    return i;
}

char const * helloworld()
{
    return "hello world";
}