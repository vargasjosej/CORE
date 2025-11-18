package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"github.com/vargasjosej/CORE/internal/application/services"
)

func main() {
	log.Println("Starting PRU Extraction Engine...")

	// Check if a PDF path is provided as command line argument
	pdfPath := ""
	if len(os.Args) > 1 {
		pdfPath = os.Args[1]
	}

	// Initialize the engine
	engine, err := NewPRUEngine()
	if err != nil {
		log.Fatalf("Failed to initialize PRU Engine: %v", err)
	}

	// Run the engine with the specified PDF or all PDFs in data directory
	ctx := context.Background()
	if pdfPath != "" {
		if err := engine.ProcessSinglePDF(ctx, pdfPath); err != nil {
			log.Fatalf("PRU Engine failed on %s: %v", pdfPath, err)
		}
	} else {
		if err := engine.ProcessAllPDFsInDataDir(ctx); err != nil {
			log.Fatalf("PRU Engine failed: %v", err)
		}
	}

	log.Println("PRU Extraction Engine completed successfully")
}

// PRUEngine is the main engine for PRU extraction
type PRUEngine struct {
	extractionService *services.ExtractionService
}

// NewPRUEngine creates a new PRU engine
func NewPRUEngine() (*PRUEngine, error) {
	log.Println("Initializing PRU Extraction Engine...")

	engine := &PRUEngine{
		extractionService: services.NewExtractionService(),
	}

	return engine, nil
}

// ProcessSinglePDF processes a single PDF file
func (e *PRUEngine) ProcessSinglePDF(ctx context.Context, pdfPath string) error {
	log.Printf("Processing single PDF: %s", pdfPath)

	relations, err := e.extractionService.ExtractPRUFromPDF(ctx, pdfPath)
	if err != nil {
		return fmt.Errorf("failed to extract PRU relations from %s: %w", pdfPath, err)
	}

	log.Printf("Extracted %d PRU relations from %s", len(relations), pdfPath)

	// Print some sample relations
	for i, rel := range relations {
		if i < 5 { // Print first 5 relations as samples
			log.Printf("  Relation %d: %s -> %s (type: %s, strength: %.2f)",
				i, rel.SourceID, rel.TargetID, rel.RelationType, rel.Strength)
		}
	}

	if len(relations) > 5 {
		log.Printf("  ... and %d more relations", len(relations)-5)
	}

	return nil
}

// ProcessAllPDFsInDataDir processes all PDF files in the data directory
func (e *PRUEngine) ProcessAllPDFsInDataDir(ctx context.Context) error {
	log.Println("Processing all PDFs in data directory")

	// Get all PDF files in the data directory
	pdfFiles, err := filepath.Glob("data/*.pdf")
	if err != nil {
		return fmt.Errorf("failed to find PDF files in data directory: %w", err)
	}

	if len(pdfFiles) == 0 {
		log.Println("No PDF files found in data directory")
		return nil
	}

	log.Printf("Found %d PDF files to process", len(pdfFiles))

	// Process each PDF file
	for _, pdfFile := range pdfFiles {
		log.Printf("Processing PDF: %s", filepath.Base(pdfFile))

		// Skip the schematic.pdf as it might be a different format
		if strings.Contains(pdfFile, "schematic.pdf") {
			log.Printf("Skipping schematic.pdf for now")
			continue
		}

		if err := e.ProcessSinglePDF(ctx, pdfFile); err != nil {
			log.Printf("Warning: Failed to process %s: %v", pdfFile, err)
			continue
		}
	}

	return nil
}

// Run starts the PRU extraction engine
func (e *PRUEngine) Run(ctx context.Context) error {
	log.Println("PRU Extraction Engine running...")

	// Process all PDFs in the data directory
	return e.ProcessAllPDFsInDataDir(ctx)
}