#!/bin/bash

g++-4.8 -std=c++11 -o bin/FeedbackDisplay src/FeedbackDisplay_V2.cpp 'sdl2-config --cflags --libs' -lSDL2_image -Iinlucde