package gpu

import (
	"context"
	"fmt"
	"sync"

	"github.com/vargasjosej/CORE/internal/domain/pru"
	"github.com/vargasjosej/CORE/internal/parallel"
)

// OCRToken represents a token extracted by OCR
type OCRToken struct {
	ID       string
	Text     string
	Page     int
	BBox     [4]float32 // [x, y, w, h]
	Confidence float32
}

// CorrelationPair represents a correlation between OCR and visual tokens
type CorrelationPair struct {
	OCRID      string
	VisualID   string
	CorrelationScore float32
	IsSpatial  bool
	Distance   float32
}

// CorrelationEngine handles correlation between OCR tokens and visual tokens
type CorrelationEngine struct {
	gpuManager *GPUManager
	threadPool *parallel.ThreadPool
}

// NewCorrelationEngine creates a new correlation engine
func NewCorrelationEngine(gpuManager *GPUManager) *CorrelationEngine {
	return &CorrelationEngine{
		gpuManager: gpuManager,
		threadPool: parallel.NewThreadPool(4), // 4 workers for parallel correlation
	}
}

// CorrelateTokensGPU correlates OCR tokens with visual tokens using GPU optimization
func (ce *CorrelationEngine) CorrelateTokensGPU(ctx context.Context, ocrTokens []*OCRToken, visualTokens []*pru.VisualToken) ([]*CorrelationPair, error) {
	if !ce.gpuManager.initialized {
		return nil, fmt.Errorf("GPU manager not initialized")
	}

	// Split work into batches for parallel processing
	const batchSize = 100
	var allCorrelations []*CorrelationPair
	var mu sync.Mutex

	// Create tasks for parallel processing
	var tasks []parallel.Task
	for i := 0; i < len(ocrTokens); i += batchSize {
		end := i + batchSize
		if end > len(ocrTokens) {
			end = len(ocrTokens)
		}

		batchOCR := ocrTokens[i:end]
		
		task := func() error {
			batchCorrelations, err := ce.correlateBatch(ctx, batchOCR, visualTokens)
			if err != nil {
				return err
			}
			
			mu.Lock()
			allCorrelations = append(allCorrelations, batchCorrelations...)
			mu.Unlock()
			
			return nil
		}
		
		tasks = append(tasks, task)
	}

	// Execute tasks in parallel
	errors := ce.threadPool.SubmitBatch(tasks, 4) // Use 4 concurrent batches
	
	// Check for errors
	for _, err := range errors {
		if err != nil {
			return nil, err
		}
	}

	return allCorrelations, nil
}

// correlateBatch processes a batch of OCR tokens against all visual tokens
func (ce *CorrelationEngine) correlateBatch(ctx context.Context, ocrBatch []*OCRToken, visualTokens []*pru.VisualToken) ([]*CorrelationPair, error) {
	var correlations []*CorrelationPair

	for _, ocrToken := range ocrBatch {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		// Find spatially related visual tokens
		tokenCorrelations := ce.findSpatialCorrelations(ocrToken, visualTokens)
		correlations = append(correlations, tokenCorrelations...)
	}

	return correlations, nil
}

// findSpatialCorrelations finds spatial correlations between OCR and visual tokens
func (ce *CorrelationEngine) findSpatialCorrelations(ocrToken *OCRToken, visualTokens []*pru.VisualToken) []*CorrelationPair {
	var correlations []*CorrelationPair
	ocrCenterX := ocrToken.BBox[0] + ocrToken.BBox[2]/2
	ocrCenterY := ocrToken.BBox[1] + ocrToken.BBox[3]/2

	for _, visualToken := range visualTokens {
		// Calculate distance between OCR token center and visual token center
		visualCenterX := visualToken.BoundarySignature["centroid_x"].(float64)
		visualCenterY := visualToken.BoundarySignature["centroid_y"].(float64)
		
		distance := float32((ocrCenterX-float32(visualCenterX))*(ocrCenterX-float32(visualCenterX)) + 
			(ocrCenterY-float32(visualCenterY))*(ocrCenterY-float32(visualCenterY)))
		distance = float32(ce.gpuManager.Sqrt(float64(distance)))
		
		// Only consider correlations within a reasonable distance
		if distance < 100.0 { // 100 pixels threshold
			correlationScore := ce.calculateCorrelationScore(ocrToken, visualToken, distance)
			
			if correlationScore > 0.5 { // Only keep strong correlations
				correlation := &CorrelationPair{
					OCRID:            ocrToken.ID,
					VisualID:         string(visualToken.ID),
					CorrelationScore: correlationScore,
					IsSpatial:        true,
					Distance:         distance,
				}
				correlations = append(correlations, correlation)
			}
		}
	}

	return correlations
}

// calculateCorrelationScore calculates a correlation score based on multiple factors
func (ce *CorrelationEngine) calculateCorrelationScore(ocrToken *OCRToken, visualToken *pru.VisualToken, distance float32) float32 {
	// Start with inverse distance (closer = higher score)
	baseScore := 1.0 / (1.0 + float64(distance)/50.0)
	
	// Apply OCR confidence weight
	confidenceWeight := float64(ocrToken.Confidence)
	
	// Apply visual context weight
	visualType := visualToken.BoundarySignature["visual_type"].(string)
	visualWeight := 1.0
	if visualType == "text_region" || visualType == "text_block" {
		visualWeight = 1.5 // Higher weight for text-related visual elements
	}
	
	// Calculate final score
	score := float64(baseScore) * confidenceWeight * visualWeight
	
	// Normalize to 0-1 range
	if score > 1.0 {
		score = 1.0
	}
	if score < 0.0 {
		score = 0.0
	}
	
	return float32(score)
}

// Calculate correlation score using GPU acceleration (simulated)
func (gm *GPUManager) Sqrt(x float64) float64 {
	// In a real implementation, this would use GPU-accelerated math
	// For now, use CPU implementation
	return gm.sqrtCPU(x)
}

// CPU implementation of square root for simulation
func (gm *GPUManager) sqrtCPU(x float64) float64 {
	if x < 0 {
		return 0
	}
	if x == 0 {
		return 0
	}
	
	// Newton's method for square root
	z := x
	for i := 0; i < 10; i++ {
		z = z - (z*z-x)/(2*z)
	}
	return z
}

// ValidatePRURelations uses OCR context to validate PRU relations
func (ce *CorrelationEngine) ValidatePRURelations(ctx context.Context, relations []*pru.PRURelation, correlations []*CorrelationPair) ([]*pru.PRURelation, error) {
	// Create map of correlations for quick lookup
	correlationMap := make(map[string]map[string]*CorrelationPair)
	for _, corr := range correlations {
		if correlationMap[corr.OCRID] == nil {
			correlationMap[corr.OCRID] = make(map[string]*CorrelationPair)
		}
		correlationMap[corr.OCRID][corr.VisualID] = corr
	}

	var validatedRelations []*pru.PRURelation

	// Validate relations based on OCR context
	for _, rel := range relations {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		// Check if the relation source and target have strong OCR correlations
		validationScore := ce.validateRelationWithContext(rel, correlationMap)
		
		// Only keep relations with good validation scores
		if validationScore >= 0.6 {
			// Add validation confidence to the relation properties
			if rel.Properties == nil {
				rel.Properties = make(map[string]interface{})
			}
			rel.Properties["validation_score"] = validationScore
			rel.Properties["validated_by_ocr"] = true
			
			validatedRelations = append(validatedRelations, rel)
		}
	}

	return validatedRelations, nil
}

// validateRelationWithContext validates a PRU relation based on OCR correlations
func (ce *CorrelationEngine) validateRelationWithContext(relation *pru.PRURelation, correlationMap map[string]map[string]*CorrelationPair) float32 {
	sourceID := string(relation.SourceID)
	targetID := string(relation.TargetID)
	
	// Look for OCR correlations with source or target
	var scores []float32
	
	if sourceCorrs, exists := correlationMap[sourceID]; exists {
		if corr, exists := sourceCorrs[targetID]; exists {
			scores = append(scores, corr.CorrelationScore)
		}
	}
	
	if targetCorrs, exists := correlationMap[targetID]; exists {
		if corr, exists := targetCorrs[sourceID]; exists {
			scores = append(scores, corr.CorrelationScore)
		}
	}
	
	// If no direct correlation found, check for indirect context
	if len(scores) == 0 {
		// For sequential or topological relations, check for spatial context
		if relation.RelationType == pru.Sequentiality || relation.RelationType == pru.Topology {
			// These relations benefit from spatial context validation
			// Return a moderate score if the relation type matches spatial validation
			return 0.7
		}
		return 0.5 // Default score for relations without OCR context
	}
	
	// Calculate average correlation score
	var total float32
	for _, score := range scores {
		total += score
	}
	
	return total / float32(len(scores))
}

// Close shuts down the correlation engine
func (ce *CorrelationEngine) Close() {
	if ce.threadPool != nil {
		ce.threadPool.Stop()
	}
}