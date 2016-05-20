#include <new>
#include <typeinfo>
#include <stdexcept>
#include <ios>


void throwBadAlloc()
{
    throw std::bad_alloc();
}

void throwBadCast()
{
    throw std::bad_cast();
}

void throwDomainError()
{
    throw std::domain_error("message");
}

void throwInvalidArgument()
{
    throw std::invalid_argument("message");
}

void throwIosBaseFailure()
{
    throw std::ios_base::failure("message");
}

void throwOutOfRange()
{
    throw std::out_of_range("message");
}

void throwOverflowError()
{
    throw std::overflow_error("message");
}

void throwRangeError()
{
    throw std::range_error("message");
}

void throwUnderflowError()
{
    throw std::underflow_error("message");
}

void throwOther()
{
    throw std::runtime_error("message");
}