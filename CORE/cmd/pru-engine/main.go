package main

import (
	"context"
	"log"
)

func main() {
	log.Println("Starting PRU Extraction Engine...")
	
	// Initialize the engine
	engine, err := NewPRUEngine()
	if err != nil {
		log.Fatalf("Failed to initialize PRU Engine: %v", err)
	}
	
	// Run the engine
	ctx := context.Background()
	if err := engine.Run(ctx); err != nil {
		log.Fatalf("PRU Engine failed: %v", err)
	}
	
	log.Println("PRU Extraction Engine completed successfully")
}