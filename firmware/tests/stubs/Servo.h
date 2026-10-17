// A do-nothing Servo for firmware/tests/test_sketch.cpp (the real one is Arduino's library).
#pragma once
struct Servo { void attach(int) {} void write(int) {} };
