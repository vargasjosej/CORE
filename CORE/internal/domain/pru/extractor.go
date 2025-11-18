package pru

import "context"

// PRUExtractor defines the interface for PRU relation extractors
type PRUExtractor interface {
	// Extract extracts PRU relations from the given data
	Extract(ctx context.Context) ([]*PRURelation, error)
	
	// GetType returns the type of PRU relations this extractor handles
	GetType() PRUType
}

// DocumentExtractor handles extraction from documents (PDF, images)
type DocumentExtractor interface {
	PRUExtractor
	ExtractFromDocument(ctx context.Context, documentPath string) ([]*PRURelation, error)
}

// SignalExtractor handles extraction from signal data
type SignalExtractor interface {
	PRUExtractor
	ExtractFromSignals(ctx context.Context, signals map[string][]float32) ([]*PRURelation, error)
}