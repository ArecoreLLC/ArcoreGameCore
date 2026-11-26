"""Synthetic Canvas contract check; actual projection/rendering needs Unreal.
Run with Python; CXX may select a g++/clang++ compatible compiler.
"""
import os
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix="world-ring-") as folder:
    root = Path(folder)
    (root / "GameFramework").mkdir()
    (root / "CoreMinimal.h").write_text(r'''#pragma once
#include <cmath>
#include <algorithm>
using int32 = int;
constexpr float PI = 3.14159265358979323846f;
struct FVector {
    double X,Y,Z;
    FVector(double x=0,double y=0,double z=0):X(x),Y(y),Z(z){}
    bool ContainsNaN() const { return !std::isfinite(X)||!std::isfinite(Y)||!std::isfinite(Z); }
    FVector operator+(FVector b) const { return {X+b.X,Y+b.Y,Z+b.Z}; }
};
struct FLinearColor {};
struct FMath {
    static bool IsFinite(float v) { return std::isfinite(v); }
    static float Abs(float v) { return std::abs(v); }
    static float Cos(float v) { return std::cos(v); }
    static float Sin(float v) { return std::sin(v); }
    template<class T> static T Clamp(T v,T a,T b) { return std::clamp(v,a,b); }
};
''')
    (root / "GameFramework/HUD.h").write_text(r'''#pragma once
#include "CoreMinimal.h"
struct AHUD {
    int lines=0; bool behind=false;
    FVector Project(FVector v) { return {v.X,v.Y,behind ? -1. : 1.}; }
    void DrawLine(double,double,double,double,FLinearColor,float) { ++lines; }
};
''')
    (root / "test.cpp").write_text(r'''#include "WorldRing.h"
#include <cassert>
#include <limits>
int main() {
    using namespace Arcore::Unreal;
    auto count=[](float progress,float radius=10.f,int segments=48,bool behind=false) {
        AHUD hud; hud.behind=behind;
        DrawWorldProgressRing(hud,{0,0,0},radius,progress,{},{},2.f,segments);
        return hud.lines;
    };
    assert(count(0)==48); assert(count(-10)==48);
    assert(count(.5f)==96); assert(count(1)==96); assert(count(10)==96);
    assert(count(std::numeric_limits<float>::quiet_NaN())==0);
    assert(count(std::numeric_limits<float>::infinity())==0);
    assert(count(.5f,-1)==0); assert(count(.5f,10,1)==16);
    assert(count(.5f,10,1000)==256); assert(count(.5f,10,48,true)==0);
    AHUD ring; DrawWorldRing(ring,{0,0,0},10,{}); assert(ring.lines==48);
    AHUD arc; DrawWorldArc(arc,{0,0,0},10,0,-PI,{}); assert(arc.lines==48);
    AHUD invalid; DrawWorldProgressRing(invalid,{0,0,0},10,.5f,{},{},-1); assert(invalid.lines==0);
}
''')
    exe = root / "contract.exe"
    subprocess.run([os.environ.get("CXX", "g++"), "-std=c++17", "-I"+str(root),
                    "-I"+str(Path(__file__).resolve().parents[1]), str(root / "test.cpp"),
                    "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print("PASS: WorldRing synthetic Canvas contracts (not a renderer test)")
