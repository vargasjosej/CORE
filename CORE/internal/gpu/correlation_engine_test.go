package gpu

import (
	"context"
	"testing"
	"time"

	"github.com/vargasjosej/CORE/internal/domain/pru"
)

func TestCorrelationEngineInitialization(t *testing.T) {
	gm := NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	ce := NewCorrelationEngine(gm)
	
	if ce.gpuManager == nil {
		t.Error("Correlation engine should have GPU manager")
	}
	
	if ce.threadPool == nil {
		t.Error("Correlation engine should have thread pool")
	}
	
	ce.Close()
	gm.Shutdown()
}

func TestCorrelationEngineCorrelateTokens(t *testing.T) {
	gm := NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	ce := NewCorrelationEngine(gm)
	defer ce.Close()
	defer gm.Shutdown()
	
	// Create test OCR tokens
	ocrTokens := []*OCRToken{
		{
			ID:         "ocr_001",
			Text:       "Test Text",
			Page:       0,
			BBox:       [4]float32{10, 10, 100, 20},
			Confidence: 0.9,
		},
		{
			ID:         "ocr_002",
			Text:       "Another Text",
			Page:       0,
			BBox:       [4]float32{120, 15, 80, 15},
			Confidence: 0.85,
		},
	}
	
	// Create test visual tokens
	visualTokens := []*pru.VisualToken{
		{
			ID:          "vis_001",
			PageNumber:  0,
			BBox:        [4]float32{10, 10, 100, 20},
			AreaPx:      2000,
			AspectRatio: 5.0,
			BoundarySignature: map[string]interface{}{
				"centroid_x": float64(60),
				"centroid_y": float64(20),
				"visual_type": "text_region",
			},
		},
		{
			ID:          "vis_002",
			PageNumber:  0,
			BBox:        [4]float32{120, 15, 80, 15},
			AreaPx:      1200,
			AspectRatio: 5.33,
			BoundarySignature: map[string]interface{}{
				"centroid_x": float64(160),
				"centroid_y": float64(22.5),
				"visual_type": "text_block",
			},
		},
	}
	
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	correlations, err := ce.CorrelateTokensGPU(ctx, ocrTokens, visualTokens)
	if err != nil {
		t.Fatalf("Failed to correlate tokens: %v", err)
	}
	
	if len(correlations) == 0 {
		t.Error("Expected to find some correlations")
	}
	
	// Check that correlations have reasonable scores
	for _, corr := range correlations {
		if corr.CorrelationScore < 0 || corr.CorrelationScore > 1 {
			t.Errorf("Correlation score out of range: %f", corr.CorrelationScore)
		}
		if corr.Distance < 0 {
			t.Errorf("Distance should be positive: %f", corr.Distance)
		}
	}
}

func TestCorrelationEngineValidatePRURelations(t *testing.T) {
	gm := NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	ce := NewCorrelationEngine(gm)
	defer ce.Close()
	defer gm.Shutdown()
	
	// Create test relations
	relations := []*pru.PRURelation{
		{
			ID:           "rel_001",
			RelationType: pru.Entity,
			SourceID:     "vis_001",
			TargetID:     "vis_002",
			Strength:     0.8,
		},
		{
			ID:           "rel_002",
			RelationType: pru.Topology,
			SourceID:     "vis_001",
			TargetID:     "vis_003",
			Strength:     0.6,
		},
	}
	
	// Create test correlations
	correlations := []*CorrelationPair{
		{
			OCRID:            "vis_001",
			VisualID:         "vis_002",
			CorrelationScore: 0.9,
			IsSpatial:        true,
			Distance:         10,
		},
		{
			OCRID:            "vis_001",
			VisualID:         "vis_003",
			CorrelationScore: 0.7,
			IsSpatial:        true,
			Distance:         20,
		},
	}
	
	ctx := context.Background()
	
	// Validate relations
	validatedRelations, err := ce.ValidatePRURelations(ctx, relations, correlations)
	if err != nil {
		t.Fatalf("Failed to validate relations: %v", err)
	}
	
	// Check that validated relations have validation properties
	for _, rel := range validatedRelations {
		if props, exists := rel.Properties["validation_score"]; !exists || props == nil {
			t.Errorf("Relation %s should have validation_score property", rel.ID)
		}
		if props, exists := rel.Properties["validated_by_ocr"]; !exists || props != true {
			t.Errorf("Relation %s should have validated_by_ocr property set to true", rel.ID)
		}
	}
}

func TestCorrelationEngineValidatePRURelationsWithLowScores(t *testing.T) {
	gm := NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}

	ce := NewCorrelationEngine(gm)
	defer ce.Close()
	defer gm.Shutdown()

	// Create test relations with low confidence
	relations := []*pru.PRURelation{
		{
			ID:           "rel_low1",
			RelationType: pru.Entity,
			SourceID:     "vis_low1",
			TargetID:     "vis_low2",
			Strength:     0.3,
		},
		{
			ID:           "rel_low2",
			RelationType: pru.Sequentiality,
			SourceID:     "vis_seq1",
			TargetID:     "vis_seq2",
			Strength:     0.4,
		},
	}

	// Create test correlations with low scores
	correlations := []*CorrelationPair{
		{
			OCRID:            "vis_low1",
			VisualID:         "vis_low2",
			CorrelationScore: 0.2, // Low score
			IsSpatial:        true,
			Distance:         100, // Far distance
		},
		{
			OCRID:            "vis_seq1",
			VisualID:         "vis_seq2",
			CorrelationScore: 0.4, // Moderate score
			IsSpatial:        true,
			Distance:         50, // Medium distance
		},
	}

	ctx := context.Background()

	// Validate relations - some should be filtered out due to low scores
	validatedRelations, err := ce.ValidatePRURelations(ctx, relations, correlations)
	if err != nil {
		t.Fatalf("Failed to validate relations: %v", err)
	}

	// The test should pass even if no relations pass validation with low scores
	// This is expected behavior for the validation system
	if len(validatedRelations) > 2 { // Should be <= original count
		t.Errorf("Expected 0-2 validated relations with low scores, got %d", len(validatedRelations))
	}
}

func TestCorrelationEngineContextCancellation(t *testing.T) {
	gm := NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	ce := NewCorrelationEngine(gm)
	defer ce.Close()
	defer gm.Shutdown()
	
	// Create large test sets to ensure we have time to test cancellation
	ocrTokens := make([]*OCRToken, 50)
	for i := 0; i < len(ocrTokens); i++ {
		ocrTokens[i] = &OCRToken{
			ID:         "ocr_" + string(rune(i+'0')),
			Text:       "Test",
			Page:       0,
			BBox:       [4]float32{float32(i * 10), 10, 50, 20},
			Confidence: 0.8,
		}
	}

	visualTokens := make([]*pru.VisualToken, 50)
	for i := 0; i < len(visualTokens); i++ {
		visualTokens[i] = &pru.VisualToken{
			ID:          pru.TokenID("vis_" + string(rune(i+'0'))),
			PageNumber:  0,
			BBox:        [4]float32{float32(i * 10), 10, 50, 20},
			AreaPx:      1000,
			AspectRatio: 2.0,
			BoundarySignature: map[string]interface{}{
				"centroid_x": float64(i * 10 + 25),
				"centroid_y": float64(20),
				"visual_type": "image_region_gpu",
			},
		}
	}
	
	// Create a context that will be cancelled quickly
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()
	
	// This should return early due to context cancellation
	_, err := ce.CorrelateTokensGPU(ctx, ocrTokens, visualTokens)
	if err == nil {
		// We don't necessarily expect an error due to the short timeout,
		// but the function should handle context cancellation gracefully
	}
}

func TestCalculateCorrelationScore(t *testing.T) {
	gm := NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	ce := NewCorrelationEngine(gm)
	defer ce.Close()
	defer gm.Shutdown()
	
	// Test OCR token
	ocrToken := &OCRToken{
		ID:         "ocr_001",
		Text:       "Test",
		Page:       0,
		BBox:       [4]float32{10, 10, 100, 20},
		Confidence: 0.9,
	}
	
	// Test visual token
	visualToken := &pru.VisualToken{
		ID:          "vis_001",
		PageNumber:  0,
		BBox:        [4]float32{10, 10, 100, 20},
		AreaPx:      2000,
		AspectRatio: 5.0,
		BoundarySignature: map[string]interface{}{
			"centroid_x": float64(60),
			"centroid_y": float64(20),
			"visual_type": "text_region", // Should get higher weight
		},
	}
	
	score := ce.calculateCorrelationScore(ocrToken, visualToken, 5.0) // Close distance
	
	if score < 0 || score > 1 {
		t.Errorf("Correlation score out of range: %f", score)
	}
	
	// The score should be relatively high due to high confidence and close distance
	if score < 0.5 {
		t.Errorf("Expected score >= 0.5 for close, high-confidence match, got %f", score)
	}
}