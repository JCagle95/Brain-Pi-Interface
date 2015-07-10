#include <SDL2/SDL.h>

class Position {
	public:
		int X, Y;
		int W, H;
		bool END;
		
		void Translocation(int, int);
		void Set(int, int, int, int);
		void rangeCheck(int, int);
};

void Position::Translocation(int Horizontal_Change, int Vertical_Change){
	X += Horizontal_Change;
	Y += Vertical_Change;
}
void Position::Set(int New_X, int New_Y, int New_W, int New_H){
	X = New_X;
	Y = New_Y;
	W = New_W;
	H = New_H;
}
void Position::rangeCheck(int Max_X, int Max_Y){
	if (X + W > Max_X)
		X = Max_X - W;
	else if (X < 0)
		X = 0;
	if (Y + H > Max_Y)
		Y = Max_Y - H;
	else if (Y < 0)
		Y = 0;
}


int EventDetection(SDL_Event event){
	while (SDL_PollEvent(&event)){
		if (event.type == SDL_KEYDOWN){
			SDL_KeyboardEvent Key = event.key;
			return Key.keysym.scancode;
		}
	}
	return 0;
}


bool Determine_Location(Position Object, Position Goal){
	if (Object.X + Object.W >= Goal.X && Object.X <= Goal.X + Goal.W
		&& Object.Y <= Goal.Y + Goal.H && Object.Y + Object.H >= Goal.Y)
		return true;
	else
		return false;
}
