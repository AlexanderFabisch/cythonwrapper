#pragma once
#include <string>
#include <sstream>

namespace Rotations {

class Quaternion
{
    double* q;
public:
    Quaternion() : q(new double[4])
    {
    }

    virtual ~Quaternion()
    {
        delete[] q;
    }

    void set(double w, double x, double y, double z)
    {
        double norm = w * w + x * x + y * y + z * z;
        q[0] = w / norm;
        q[1] = x / norm;
        q[2] = y / norm;
        q[3] = z / norm;
    }

    double w()
    {
        return q[0];
    }

    double x()
    {
        return q[1];
    }

    double y()
    {
        return q[2];
    }

    double z()
    {
        return q[3];
    }

    std::string toString()
    {
        std::stringstream ss;
        ss << "Quaternion(" << w() << ", " << x() << ", " << y()
            << ", " << z() << ")";
        return ss.str();
    }
};

}
