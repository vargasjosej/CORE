package optimization

import (
	"context"
	"fmt"
	"image"
	"log"
	"sync"

	"github.com/vargasjosej/CORE/internal/domain/pru"
	"github.com/vargasjosej/CORE/internal/gpu"
	"github.com/vargasjosej/CORE/internal/parallel"
)

// OCRClient interface for OCR services (like DeepSeek OCR)
type OCRClient interface {
	ProcessPage(ctx context.Context, page image.Image) ([]*gpu.OCRToken, error)
}

// GPUOCRPRUProcessor handles the full GPU-OCR-PRU processing pipeline
type GPUOCRPRUProcessor struct {
	gpuManager      *gpu.GPUManager
	ocrClient       OCRClient
	correlationEngine *gpu.CorrelationEngine
	threadPool      *parallel.ThreadPool
	qualityThreshold float32
}

// NewGPUOCRPRUProcessor creates a new GPU-OCR-PRU processor
func NewGPUOCRPRUProcessor(gpuManager *gpu.GPUManager, ocrClient OCRClient) *GPUOCRPRUProcessor {
	return &GPUOCRPRUProcessor{
		gpuManager:      gpuManager,
		ocrClient:       ocrClient,
		correlationEngine: gpu.NewCorrelationEngine(gpuManager),
		threadPool:      parallel.NewThreadPool(4),
		qualityThreshold: 0.6, // Default 60% threshold for validation
	}
}

// ProcessImageWithOCR processes an image using GPU for visual tokens and OCR for text
func (p *GPUOCRPRUProcessor) ProcessImageWithOCR(ctx context.Context, img image.Image) ([]*pru.VisualToken, []*gpu.OCRToken, error) {
	var wg sync.WaitGroup
	var visualTokens []*pru.VisualToken
	var ocrTokens []*gpu.OCRToken
	var visualErr, ocrErr error

	// Process visual tokens with GPU
	wg.Add(1)
	go func() {
		defer wg.Done()
		select {
		case <-ctx.Done():
			visualErr = ctx.Err()
			return
		default:
			visualTokens, visualErr = p.gpuManager.ProcessImageBatch(ctx, []image.Image{img})
		}
	}()

	// Process OCR tokens in parallel
	wg.Add(1)
	go func() {
		defer wg.Done()
		select {
		case <-ctx.Done():
			ocrErr = ctx.Err()
			return
		default:
			ocrTokens, ocrErr = p.ocrClient.ProcessPage(ctx, img)
		}
	}()

	wg.Wait()

	if visualErr != nil {
		return nil, nil, fmt.Errorf("visual processing error: %w", visualErr)
	}

	if ocrErr != nil {
		return nil, nil, fmt.Errorf("OCR processing error: %w", ocrErr)
	}

	return visualTokens, ocrTokens, nil
}

// CorrelateAndValidate combines OCR and visual processing with validation
func (p *GPUOCRPRUProcessor) CorrelateAndValidate(ctx context.Context, visualTokens []*pru.VisualToken, ocrTokens []*gpu.OCRToken) ([]*gpu.CorrelationPair, error) {
	log.Printf("Correlating %d OCR tokens with %d visual tokens", len(ocrTokens), len(visualTokens))

	correlations, err := p.correlationEngine.CorrelateTokensGPU(ctx, ocrTokens, visualTokens)
	if err != nil {
		return nil, fmt.Errorf("correlation error: %w", err)
	}

	log.Printf("Found %d correlations between OCR and visual tokens", len(correlations))
	return correlations, nil
}

// ValidatePRURelationsWithOCR validates PRU relations using OCR context
func (p *GPUOCRPRUProcessor) ValidatePRURelationsWithOCR(ctx context.Context, relations []*pru.PRURelation, correlations []*gpu.CorrelationPair) ([]*pru.PRURelation, error) {
	log.Printf("Validating %d PRU relations with OCR context", len(relations))

	validatedRelations, err := p.correlationEngine.ValidatePRURelations(ctx, relations, correlations)
	if err != nil {
		return nil, fmt.Errorf("validation error: %w", err)
	}

	log.Printf("Validated %d PRU relations (original: %d)", len(validatedRelations), len(relations))
	return validatedRelations, nil
}

// OptimizeParameters automatically adjusts processing parameters based on OCR validation
func (p *GPUOCRPRUProcessor) OptimizeParameters(ctx context.Context, correlations []*gpu.CorrelationPair) error {
	if len(correlations) == 0 {
		return nil
	}

	// Calculate statistics from correlations to adjust parameters
	var totalScore float32
	var highScoreCount int

	for _, corr := range correlations {
		totalScore += corr.CorrelationScore
		if corr.CorrelationScore > 0.8 {
			highScoreCount++
		}
	}

	avgScore := totalScore / float32(len(correlations))
	highScoreRatio := float32(highScoreCount) / float32(len(correlations))

	log.Printf("Correlation statistics: avg=%.2f, high_ratio=%.2f", avgScore, highScoreRatio)

	// Adjust quality threshold based on correlation quality
	if avgScore > 0.7 {
		// High quality correlations - can be more selective
		p.qualityThreshold = 0.7
	} else if avgScore < 0.5 {
		// Lower quality correlations - be more permissive
		p.qualityThreshold = 0.4
	}

	log.Printf("Adjusted quality threshold to %.2f based on correlation quality", p.qualityThreshold)
	return nil
}

// ValidateAndOptimizePRURelations processes relations with full GPU-OCR validation
func (p *GPUOCRPRUProcessor) ValidateAndOptimizePRURelations(ctx context.Context, relations []*pru.PRURelation, ocrTokens []*gpu.OCRToken, visualTokens []*pru.VisualToken) ([]*pru.PRURelation, error) {
	// First, correlate OCR and visual tokens
	correlations, err := p.CorrelateAndValidate(ctx, visualTokens, ocrTokens)
	if err != nil {
		return nil, fmt.Errorf("correlation validation failed: %w", err)
	}

	// Optimize parameters based on correlations
	if err := p.OptimizeParameters(ctx, correlations); err != nil {
		log.Printf("Warning: parameter optimization failed: %v", err)
		// Continue processing even if optimization fails
	}

	// Validate PRU relations using OCR context
	validatedRelations, err := p.ValidatePRURelationsWithOCR(ctx, relations, correlations)
	if err != nil {
		return nil, fmt.Errorf("PRU validation failed: %w", err)
	}

	// Filter relations based on quality threshold
	var finalRelations []*pru.PRURelation
	for _, rel := range validatedRelations {
		if validationScore, exists := rel.Properties["validation_score"]; exists {
			if score, ok := validationScore.(float64); ok {
				if float32(score) >= p.qualityThreshold {
					finalRelations = append(finalRelations, rel)
				}
			} else if score, ok := validationScore.(float32); ok {
				if score >= p.qualityThreshold {
					finalRelations = append(finalRelations, rel)
				}
			}
		}
	}

	log.Printf("Filtered relations to %d (from %d) based on quality threshold %.2f",
		len(finalRelations), len(validatedRelations), p.qualityThreshold)

	// Ensure we always return a slice, not nil
	if finalRelations == nil {
		finalRelations = []*pru.PRURelation{}
	}

	return finalRelations, nil
}

// ProcessPageParallel processes a page using parallel GPU and OCR processing
func (p *GPUOCRPRUProcessor) ProcessPageParallel(ctx context.Context, img image.Image, pageIndex int) (*PageResult, error) {
	// Process visual and OCR tokens in parallel
	visualTokens, ocrTokens, err := p.ProcessImageWithOCR(ctx, img)
	if err != nil {
		return nil, fmt.Errorf("parallel processing failed: %w", err)
	}

	// Extract PRU relations from visual tokens (this would normally be done elsewhere)
	// For this example, we'll create some sample relations
	relations := p.createSamplePRURelations(visualTokens, pageIndex)

	// Validate and optimize the relations using OCR context
	validatedRelations, err := p.ValidateAndOptimizePRURelations(ctx, relations, ocrTokens, visualTokens)
	if err != nil {
		return nil, fmt.Errorf("relation optimization failed: %w", err)
	}

	return &PageResult{
		PageIndex:  pageIndex,
		VisualTokens: visualTokens,
		OCRTokens:    ocrTokens,
		Relations:    validatedRelations, // This could be nil, let's ensure it's initialized
		ProcessingTime: 0, // Would be calculated in real implementation
	}, nil
}

// createSamplePRURelations creates sample PRU relations from visual tokens
func (p *GPUOCRPRUProcessor) createSamplePRURelations(visualTokens []*pru.VisualToken, pageIndex int) []*pru.PRURelation {
	var relations []*pru.PRURelation
	
	// Create some sample relations between tokens
	for i := 0; i < len(visualTokens) && i+1 < len(visualTokens); i++ {
		rel := &pru.PRURelation{
			ID:           fmt.Sprintf("rel_%s_%s", visualTokens[i].ID, visualTokens[i+1].ID),
			RelationType: pru.Entity,
			SourceID:     visualTokens[i].ID,
			TargetID:     visualTokens[i+1].ID,
			Strength:     0.7, // Default strength
			Properties:   make(map[string]interface{}),
			ObserverID:   "gpu_processor",
		}
		relations = append(relations, rel)
	}
	
	return relations
}

// PageResult contains the result of processing a page
type PageResult struct {
	PageIndex     int
	VisualTokens  []*pru.VisualToken
	OCRTokens     []*gpu.OCRToken
	Relations     []*pru.PRURelation
	ProcessingTime float64
	Error         error
}

// ProcessDocumentParallel processes a document with parallel GPU-OCR processing
func (p *GPUOCRPRUProcessor) ProcessDocumentParallel(ctx context.Context, images []image.Image) ([]*PageResult, error) {
	log.Printf("Processing %d pages in parallel", len(images))

	pageResults := make([]*PageResult, len(images))
	var mu sync.Mutex

	// Process pages in parallel using thread pool
	tasks := make([]parallel.Task, len(images))

	for i := range images {
		i := i // Capture loop variable
		tasks[i] = func() error {
			result, err := p.ProcessPageParallel(ctx, images[i], i)
			if err != nil {
				result = &PageResult{
					PageIndex: i,
					Error:     err,
				}
			}

			mu.Lock()
			pageResults[i] = result
			mu.Unlock()

			return nil
		}
	}

	// Execute tasks in parallel
	errors := p.threadPool.SubmitBatch(tasks, 4) // Limit to 4 concurrent pages

	// Check for submission errors
	for _, err := range errors {
		if err != nil {
			log.Printf("Task submission error: %v", err)
		}
	}

	log.Printf("Completed processing of %d pages", len(images))
	return pageResults, nil
}

// Close shuts down the processor
func (p *GPUOCRPRUProcessor) Close() {
	if p.correlationEngine != nil {
		p.correlationEngine.Close()
	}
	if p.threadPool != nil {
		p.threadPool.Stop()
	}
}