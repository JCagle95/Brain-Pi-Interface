#include <iostream>
#include <fstream>
#include <sstream>
#include <ctime>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>

#include <etc/res_path.h>
#include <etc/objectMovement.h>
#include <etc/renderingFunction.h>

int SCREEN_WIDTH;
int SCREEN_HEIGHT;

bool Sync_Wait(std::string File, std::string Message, SDL_Event event){
	std::string New;
	while(New != Message){
		std::ifstream FileInput (File);
		getline(FileInput,New);
		FileInput.close();
		if (EventDetection(event) == SDL_SCANCODE_Q)
			return false;
	}
	return true;
}

bool Sync_Check(std::string File, std::string Message){
	std::string New;
	std::ifstream FileInput (File);
	getline(FileInput,New);
	FileInput.close();
	if(New == Message)
		return true;
	return false;
}

void Sync_Send(std::string File, std::string Message){
	std::ofstream FileOutput (File);
	FileOutput << Message;
	FileOutput.close();
}

int Read_Trial(std::string File){
	std::string New = "";
	while (New == ""){
		std::ifstream FileInput(File);
		getline(FileInput,New);
		FileInput.close();
	}
	return atoi(New.c_str());
}

std::string DirectionalReader(std::string File, std::string Previous){
	std::string New;
	std::ifstream FileInput (File);
	getline(FileInput,New);
	FileInput.close();
	if (New != Previous && New.length() > 0)
		return New;
	else
		return "No Update";

}

Feature DecodeString(std::string Line){
	Feature Direction;
	std::stringstream inputstream(Line);
	std::string Parser;
	for (int n = 0; n < 2; n++){
		std::getline(inputstream, Parser, ',');
		Direction.Results[n] = atoi(Parser.c_str());
	}
	return Direction;
}

int main(int, char**){
	// This section is the initialization for SDL2
	if (SDL_Init(SDL_INIT_EVERYTHING) != 0){
		logSDLError(std::cout, "SDL_Init");
		return 1;
	}
	SDL_Window *window = SDL_CreateWindow("Moving Window", 100, 100, 1440, 810, SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE);
	if (window == nullptr){
		logSDLError(std::cout, "CreateWindow");
		SDL_Quit();
		return 1;
	}
	SDL_Renderer *renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
	if (renderer == nullptr){
		logSDLError(std::cout, "CreateRenderer");
		SDL_DestroyWindow(window);
		SDL_Quit();
		return 1;
	}

	// Initialize all the Images and Texts Pointers
	const std::string resPath = getResourcePath("FeedbackDisplay");
	SDL_Texture *instruction = loadTexture(resPath + "instruction.png", renderer);
	SDL_Texture *background = loadTexture(resPath + "SyncStart.png", renderer);
	SDL_Texture *background2 = loadTexture(resPath + "SyncEnd.png", renderer);
	SDL_Texture *instruction2 = loadTexture(resPath + "instruction2.png", renderer);
	SDL_Texture *sphere = loadTexture(resPath + "sphere.png", renderer);
	SDL_Texture *Target = loadTexture(resPath + "Target.png", renderer);
	SDL_Texture *sphere2 = loadTexture(resPath + "sphere2.png", renderer);
	SDL_Texture *Target2 = loadTexture(resPath + "Target2.png", renderer);
	SDL_Texture *trialStart = loadTexture(resPath + "trialStart.png", renderer);
	SDL_Texture *trialEnd = loadTexture(resPath + "trialEnd.png", renderer);
	SDL_Event event;
	
	if (background == nullptr || background2 == nullptr || sphere == nullptr || instruction2 == nullptr || Target == nullptr || sphere2 == nullptr || Target2 == nullptr ||
		trialStart == nullptr || trialEnd == nullptr || instruction == nullptr)
	{
		SDL_DestroyWindow(window);
		SDL_DestroyRenderer(renderer);
		SDL_DestroyTexture(background);
		SDL_DestroyTexture(instruction);
		SDL_DestroyTexture(sphere);
		SDL_DestroyTexture(background2);
		SDL_DestroyTexture(sphere2);
		SDL_DestroyTexture(Target2);
		SDL_DestroyTexture(Target);
		SDL_DestroyTexture(instruction2);
		SDL_Quit();
		SDL_Quit();
		return 1;
	}

	SDL_GetWindowSize(window, &SCREEN_WIDTH, &SCREEN_HEIGHT);
	// Wait for Synchronization between OpenBCI and Feedback Display
	SDL_RenderClear(renderer);
	renderTexture(background, renderer, (SCREEN_WIDTH - SCREEN_HEIGHT) / 2, 0, SCREEN_HEIGHT, SCREEN_HEIGHT);
	SDL_RenderPresent(renderer);

	// Obtain the timer as well as the logging files
	const std::string Feature1 = getResourcePath("FIFO") + "X_Direction.txt";
	const std::string Feature2 = getResourcePath("FIFO") + "Y_Direction.txt";
	const std::string Trial_Info = getResourcePath("FIFO") + "Trial_Information.txt";
	const std::string Trigger_Log = getResourcePath("FIFO") + "Trigger_Log.txt";
	const std::string Feedback = getResourcePath("FIFO") + "Feedback_Log_0.txt";
	Sync_Send(Feedback, "Timer on");
	Sync_Wait(Trigger_Log, "All Set", event);
	SDL_RenderClear(renderer);
	renderTexture(background2, renderer, (SCREEN_WIDTH - SCREEN_HEIGHT) / 2, 0, SCREEN_HEIGHT, SCREEN_HEIGHT);
	SDL_RenderPresent(renderer);

	// flag used to stop the program execution
	bool Next_Trial, Finishing;
	Finishing = false;

	// Obtain Screen Size, Create position values for objects
	Position Centroid, Ball, Goal;
	const int SPHERE_SIZE = SCREEN_HEIGHT / 10;
	const int TARGET_WIDTH = SCREEN_HEIGHT / 10;
	const int TARGET_HEIGHT = TARGET_WIDTH;
	Centroid.Set(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0);
	std::string Previous_X, Previous_Y, Current_X, Current_Y;
	Feature X_Direction,Y_Direction;
	X_Direction.Set(1,0);
	X_Direction.Set(1,0);

	// Calibration
	if (!Sync_Wait(Trigger_Log, "Calibration On", event)){
		Sync_Send(Feedback,"Display End");
		SDL_DestroyWindow(window);
		SDL_DestroyRenderer(renderer);
		SDL_DestroyTexture(background);
		SDL_DestroyTexture(instruction);
		SDL_DestroyTexture(sphere);
		SDL_DestroyTexture(background2);
		SDL_DestroyTexture(sphere2);
		SDL_DestroyTexture(Target2);
		SDL_DestroyTexture(Target);
		SDL_DestroyTexture(instruction2);
		SDL_Quit();
		return 1;
	}

	SDL_RenderClear(renderer);
	renderTexture(instruction, renderer, (SCREEN_WIDTH - SCREEN_HEIGHT) / 2, 0, SCREEN_HEIGHT, SCREEN_HEIGHT);
	SDL_RenderPresent(renderer);	
	if (!Sync_Wait(Trigger_Log, "Calibration Stage2", event)){
		Sync_Send(Feedback,"Display End");
		SDL_DestroyWindow(window);
		SDL_DestroyRenderer(renderer);
		SDL_DestroyTexture(background);
		SDL_DestroyTexture(instruction);
		SDL_DestroyTexture(sphere);
		SDL_DestroyTexture(background2);
		SDL_DestroyTexture(sphere2);
		SDL_DestroyTexture(Target2);
		SDL_DestroyTexture(Target);
		SDL_DestroyTexture(instruction2);
		SDL_Quit();
		return 1;
	}

	SDL_RenderClear(renderer);
	renderTexture(instruction2, renderer, (SCREEN_WIDTH - SCREEN_HEIGHT) / 2, 0, SCREEN_HEIGHT, SCREEN_HEIGHT);
	SDL_RenderPresent(renderer);	
	if (!Sync_Wait(Trigger_Log, "Calibration End", event)){
		Sync_Send(Feedback,"Display End");
		SDL_DestroyWindow(window);
		SDL_DestroyRenderer(renderer);
		SDL_DestroyTexture(background);
		SDL_DestroyTexture(instruction);
		SDL_DestroyTexture(sphere);
		SDL_DestroyTexture(background2);
		SDL_DestroyTexture(sphere2);
		SDL_DestroyTexture(Target2);
		SDL_DestroyTexture(Target);
		SDL_DestroyTexture(instruction2);
		SDL_Quit();
		return 1;
	}


	/******************************
	 * The Actual Experiment Part *
	******************************/

	while(!(Sync_Check(Trigger_Log,"ALL FINISH")||Finishing)){
		// Determine the type of Trial
		if (!Sync_Wait(Trigger_Log, "Ready", event)){
			Sync_Send(Feedback,"Display End");
			SDL_DestroyWindow(window);
			SDL_DestroyRenderer(renderer);
			SDL_DestroyTexture(background);
			SDL_DestroyTexture(instruction);
			SDL_DestroyTexture(sphere);
			SDL_DestroyTexture(background2);
			SDL_DestroyTexture(sphere2);
			SDL_DestroyTexture(Target2);
			SDL_DestroyTexture(Target);
			SDL_DestroyTexture(instruction2);
			SDL_Quit();
			return 1;
		}
		switch (Read_Trial(Trial_Info)){
		case 0:
			Goal.Set(0, 0, TARGET_HEIGHT, TARGET_WIDTH);
			break;
		case 1:
			Goal.Set(SCREEN_WIDTH - TARGET_WIDTH, 0, TARGET_HEIGHT, TARGET_WIDTH);
			break;
		case 2:
			Goal.Set(0, SCREEN_HEIGHT - TARGET_HEIGHT, TARGET_WIDTH, TARGET_HEIGHT);
			break;
		case 3:
			Goal.Set(SCREEN_WIDTH - TARGET_WIDTH, SCREEN_HEIGHT - TARGET_HEIGHT, TARGET_WIDTH, TARGET_HEIGHT);
			break;
		}
		
		// Signal Trial Begin
		SDL_RenderClear(renderer);
		renderTexture(trialStart, renderer, (SCREEN_WIDTH-SCREEN_HEIGHT)/2, 0, SCREEN_HEIGHT, SCREEN_HEIGHT);
		SDL_RenderPresent(renderer);
		if (!Sync_Wait(Trigger_Log,"Trial Start", event)){
			Sync_Send(Feedback,"Display End");
			SDL_DestroyWindow(window);
			SDL_DestroyRenderer(renderer);
			SDL_DestroyTexture(background);
			SDL_DestroyTexture(instruction);
			SDL_DestroyTexture(sphere);
			SDL_DestroyTexture(background2);
			SDL_DestroyTexture(sphere2);
			SDL_DestroyTexture(Target2);
			SDL_DestroyTexture(Target);
			SDL_DestroyTexture(instruction2);
			SDL_Quit();
			return 1;
		}

		Ball.Set(Centroid.X - SPHERE_SIZE / 2, Centroid.Y - SPHERE_SIZE / 2, SPHERE_SIZE, SPHERE_SIZE);

		Next_Trial = false;
		while (!Next_Trial){
			// Listen to OpenBCI for Location Data
			Current_X = DirectionalReader(Feature1, Previous_X);
			Current_Y = DirectionalReader(Feature2, Previous_Y);

			if (Current_X != "No Update" && Current_Y != "No Update"){
				Y_Direction = DecodeString(Current_Y);
				X_Direction = DecodeString(Current_X);
				Previous_X = Current_X;
				Previous_Y = Current_Y;

				for (int rate = 0; rate < 10; rate++){
					Ball.Translocation(X_Direction.Results[0],Y_Direction.Results[0]);
					Ball.rangeCheck(SCREEN_WIDTH,SCREEN_HEIGHT);
					SDL_RenderClear(renderer);
					renderTexture(sphere, renderer, Ball.X, Ball.Y, Ball.W, Ball.H);
					renderTexture(Target, renderer, Goal.X, Goal.Y, Goal.W, Goal.H);
					SDL_RenderPresent(renderer);
					if (Determine_Location(Ball,Goal)){
						Next_Trial = true;
						rate = 10;
						SDL_RenderClear(renderer);
						renderTexture(sphere2, renderer, Ball.X, Ball.Y, Ball.W, Ball.H);
						renderTexture(Target2, renderer, Goal.X, Goal.Y, Goal.W, Goal.H);
						SDL_RenderPresent(renderer);
						Sync_Send(Feedback,"Complete");
						SDL_Delay(1000);
					}
					if (EventDetection(event) == SDL_SCANCODE_Q){
						Next_Trial = true;
						Finishing = true;
						Sync_Send(Feedback,"Complete");
					}
				}
			}

			if (Sync_Check(Trigger_Log,"Trial End")){
				Next_Trial = true;
			}
			// Check for Break or other commands
			if (EventDetection(event) == SDL_SCANCODE_Q){
				Next_Trial = true;
				Finishing = true;
				Sync_Send(Feedback,"Complete");
			}
		}

		SDL_RenderClear(renderer);
		renderTexture(trialEnd, renderer, (SCREEN_WIDTH-SCREEN_HEIGHT)/2, 0, SCREEN_HEIGHT, SCREEN_HEIGHT);
		SDL_RenderPresent(renderer);
		if (!Sync_Wait(Trigger_Log,"Trial End", event)){
			Sync_Send(Feedback,"Display End");
			SDL_DestroyWindow(window);
			SDL_DestroyRenderer(renderer);
			SDL_DestroyTexture(background);
			SDL_DestroyTexture(instruction);
			SDL_DestroyTexture(sphere);
			SDL_DestroyTexture(background2);
			SDL_DestroyTexture(sphere2);
			SDL_DestroyTexture(Target2);
			SDL_DestroyTexture(Target);
			SDL_DestroyTexture(instruction2);
			SDL_Quit();
			return 1;
		}
	}
	
	// Cleanning up
	Sync_Send(Feedback,"Display End");
	SDL_DestroyWindow(window);
	SDL_DestroyRenderer(renderer);
	SDL_DestroyTexture(background);
	SDL_DestroyTexture(instruction);
	SDL_DestroyTexture(sphere);
	SDL_DestroyTexture(background2);
	SDL_DestroyTexture(sphere2);
	SDL_DestroyTexture(Target2);
	SDL_DestroyTexture(Target);
	SDL_DestroyTexture(instruction2);
	SDL_Quit();
	return 0;
}
