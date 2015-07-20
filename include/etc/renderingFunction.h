#include <iostream>
#include <cstdarg>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <SDL2/SDL_ttf.h>

void logSDLError(std::ostream &os, const std::string &msg){
	os << msg << " error: " << SDL_GetError() << std::endl;
}

SDL_Texture* loadTexture(const std::string &file, SDL_Renderer *ren){
	SDL_Texture *texture = IMG_LoadTexture(ren, file.c_str());
	if (texture == nullptr){
		logSDLError(std::cout, "LoadTexture");
	}
	return texture;
}

void renderTexture(SDL_Texture *tex, SDL_Renderer *ren, int x, int y, int w, int h){
	SDL_Rect dst;
	dst.w = w;
	dst.h = h;
	dst.x = x;
	dst.y = y;

	SDL_RenderCopy(ren, tex, NULL, &dst);
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
