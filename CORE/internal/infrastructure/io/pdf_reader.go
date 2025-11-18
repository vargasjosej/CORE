package io

import (
	"context"
	"image"
	"github.com/gen2brain/go-fitz"
)

// PDFProcessor handles PDF to image conversion for visual token extraction
type PDFProcessor struct {
}

// NewPDFProcessor creates a new PDF processor
func NewPDFProcessor() *PDFProcessor {
	return &PDFProcessor{}
}

// ExtractImages converts PDF pages to images
func (pp *PDFProcessor) ExtractImages(ctx context.Context, filePath string) ([]image.Image, error) {
	doc, err := fitz.New(filePath)
	if err != nil {
		return nil, err
	}
	defer doc.Close()

	var images []image.Image
	
	for i := 0; i < doc.NumPage(); i++ {
		img, err := doc.Image(i)
		if err != nil {
			continue
		}
		
		images = append(images, img)
	}
	
	return images, nil
}

// GetNumPages returns the number of pages in the PDF
func (pp *PDFProcessor) GetNumPages(filePath string) (int, error) {
	doc, err := fitz.New(filePath)
	if err != nil {
		return 0, err
	}
	defer doc.Close()
	
	return doc.NumPage(), nil
}