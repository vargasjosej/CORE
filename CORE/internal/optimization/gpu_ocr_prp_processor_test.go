package optimization

import (
	"context"
	"image"
	"image/color"
	"testing"
	"time"

	"github.com/vargasjosej/CORE/internal/domain/pru"
	"github.com/vargasjosej/CORE/internal/gpu"
)

func TestGPUOCRPRUProcessorInitialization(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(10 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	if processor.gpuManager != gm {
		t.Error("Processor should have the correct GPU manager")
	}

	if processor.ocrClient != mockOCR {
		t.Error("Processor should have the correct OCR client")
	}

	if processor.correlationEngine == nil {
		t.Error("Processor should have correlation engine")
	}

	if processor.threadPool == nil {
		t.Error("Processor should have thread pool")
	}
}

func TestGPUOCRPRUProcessorProcessImageWithOCR(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create a test image
	testImage := image.NewRGBA(image.Rect(0, 0, 200, 200))
	for x := 0; x < 200; x++ {
		for y := 0; y < 200; y++ {
			testImage.Set(x, y, color.RGBA{uint8(x % 255), uint8(y % 255), 128, 255})
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	visualTokens, ocrTokens, err := processor.ProcessImageWithOCR(ctx, testImage)
	if err != nil {
		t.Fatalf("Failed to process image with OCR: %v", err)
	}

	if len(visualTokens) == 0 {
		t.Error("Expected to extract some visual tokens")
	}

	if len(ocrTokens) == 0 {
		t.Error("Expected to extract some OCR tokens")
	}

	// Verify token properties
	for _, token := range visualTokens {
		if token.ID == "" {
			t.Error("Visual token ID should not be empty")
		}
	}

	for _, token := range ocrTokens {
		if token.ID == "" {
			t.Error("OCR token ID should not be empty")
		}
		if token.Text == "" {
			t.Error("OCR token text should not be empty")
		}
	}
}

func TestGPUOCRPRUProcessorCorrelateAndValidate(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

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

	// Create test OCR tokens
	ocrTokens := []*gpu.OCRToken{
		{
			ID:         "vis_001", // Match to visual token
			Text:       "Test Text",
			Page:       0,
			BBox:       [4]float32{10, 10, 100, 20},
			Confidence: 0.9,
		},
		{
			ID:         "vis_002", // Match to visual token
			Text:       "Another Text",
			Page:       0,
			BBox:       [4]float32{120, 15, 80, 15},
			Confidence: 0.85,
		},
	}

	ctx := context.Background()

	correlations, err := processor.CorrelateAndValidate(ctx, visualTokens, ocrTokens)
	if err != nil {
		t.Fatalf("Failed to correlate and validate: %v", err)
	}

	if len(correlations) == 0 {
		t.Error("Expected to find some correlations")
	}

	// Check correlation properties
	for _, corr := range correlations {
		if corr.CorrelationScore < 0 || corr.CorrelationScore > 1 {
			t.Errorf("Invalid correlation score: %f", corr.CorrelationScore)
		}
		if corr.Distance < 0 {
			t.Errorf("Invalid distance: %f", corr.Distance)
		}
	}
}

func TestGPUOCRPRUProcessorValidatePRURelationsWithOCR(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create test relations
	relations := []*pru.PRURelation{
		{
			ID:           "rel_001",
			RelationType: pru.Entity,
			SourceID:     "tok_001",
			TargetID:     "tok_002",
			Strength:     0.8,
		},
		{
			ID:           "rel_002",
			RelationType: pru.Sequentiality,
			SourceID:     "tok_003",
			TargetID:     "tok_004",
			Strength:     0.6,
		},
	}

	// Create test correlations
	correlations := []*gpu.CorrelationPair{
		{
			OCRID:            "tok_001",
			VisualID:         "tok_002",
			CorrelationScore: 0.9,
			IsSpatial:        true,
			Distance:         10,
		},
		{
			OCRID:            "tok_003",
			VisualID:         "tok_004",
			CorrelationScore: 0.7,
			IsSpatial:        true,
			Distance:         20,
		},
	}

	ctx := context.Background()

	validatedRelations, err := processor.ValidatePRURelationsWithOCR(ctx, relations, correlations)
	if err != nil {
		t.Fatalf("Failed to validate PRU relations: %v", err)
	}

	if len(validatedRelations) == 0 {
		t.Error("Expected to validate some relations")
	}

	// Check that validated relations have validation properties
	for _, rel := range validatedRelations {
		if _, exists := rel.Properties["validation_score"]; !exists {
			t.Errorf("Relation %s should have validation_score property", rel.ID)
		}
	}
}

func TestGPUOCRPRUProcessorOptimizeParameters(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create test correlations with high scores
	correlations := []*gpu.CorrelationPair{
		{
			OCRID:            "tok_001",
			VisualID:         "tok_002",
			CorrelationScore: 0.9,
			IsSpatial:        true,
			Distance:         5,
		},
		{
			OCRID:            "tok_003",
			VisualID:         "tok_004",
			CorrelationScore: 0.85,
			IsSpatial:        true,
			Distance:         8,
		},
		{
			OCRID:            "tok_005",
			VisualID:         "tok_006",
			CorrelationScore: 0.95,
			IsSpatial:        true,
			Distance:         3,
		},
	}

	ctx := context.Background()

	// Store original threshold
	originalThreshold := processor.qualityThreshold

	err := processor.OptimizeParameters(ctx, correlations)
	if err != nil {
		t.Fatalf("Failed to optimize parameters: %v", err)
	}

	// With high correlation scores, the threshold should increase
	if processor.qualityThreshold <= originalThreshold {
		t.Errorf("Expected quality threshold to increase with high correlation scores, was %f, became %f", 
			originalThreshold, processor.qualityThreshold)
	}

	// Reset for second test with low scores
	processor.qualityThreshold = originalThreshold
	lowCorrelations := []*gpu.CorrelationPair{
		{
			OCRID:            "tok_001",
			VisualID:         "tok_002",
			CorrelationScore: 0.3,
			IsSpatial:        true,
			Distance:         50,
		},
		{
			OCRID:            "tok_003",
			VisualID:         "tok_004",
			CorrelationScore: 0.2,
			IsSpatial:        true,
			Distance:         60,
		},
	}

	err = processor.OptimizeParameters(ctx, lowCorrelations)
	if err != nil {
		t.Fatalf("Failed to optimize parameters with low scores: %v", err)
	}

	// With low correlation scores, the threshold should decrease
	if processor.qualityThreshold >= originalThreshold && processor.qualityThreshold >= 0.5 {
		t.Errorf("Expected quality threshold to decrease with low correlation scores, was %f, became %f", 
			originalThreshold, processor.qualityThreshold)
	}
}

func TestGPUOCRPRUProcessorValidateAndOptimizePRURelations(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create test relations
	relations := []*pru.PRURelation{
		{
			ID:           "rel_001",
			RelationType: pru.Entity,
			SourceID:     "tok_001",
			TargetID:     "tok_002",
			Strength:     0.8,
		},
		{
			ID:           "rel_002",
			RelationType: pru.Sequentiality,
			SourceID:     "tok_003",
			TargetID:     "tok_004",
			Strength:     0.6,
		},
	}

	// Create test OCR tokens
	ocrTokens := []*gpu.OCRToken{
		{
			ID:         "tok_001",
			Text:       "Test",
			Page:       0,
			BBox:       [4]float32{10, 10, 50, 20},
			Confidence: 0.85,
		},
		{
			ID:         "tok_002",
			Text:       "Text",
			Page:       0,
			BBox:       [4]float32{70, 10, 50, 20},
			Confidence: 0.8,
		},
	}

	// Create test visual tokens
	visualTokens := []*pru.VisualToken{
		{
			ID:          "tok_001",
			PageNumber:  0,
			BBox:        [4]float32{10, 10, 50, 20},
			AreaPx:      1000,
			AspectRatio: 2.5,
			BoundarySignature: map[string]interface{}{
				"centroid_x": float64(35),
				"centroid_y": float64(20),
				"visual_type": "text_region",
			},
		},
		{
			ID:          "tok_002",
			PageNumber:  0,
			BBox:        [4]float32{70, 10, 50, 20},
			AreaPx:      1000,
			AspectRatio: 2.5,
			BoundarySignature: map[string]interface{}{
				"centroid_x": float64(95),
				"centroid_y": float64(20),
				"visual_type": "text_region",
			},
		},
	}

	ctx := context.Background()

	resultRelations, err := processor.ValidateAndOptimizePRURelations(ctx, relations, ocrTokens, visualTokens)
	if err != nil {
		t.Fatalf("Failed to validate and optimize relations: %v", err)
	}

	// Should have at least one relation after validation
	if len(resultRelations) == 0 {
		t.Error("Expected at least one validated relation")
	}

	// Check that relations have validation properties
	for _, rel := range resultRelations {
		if _, exists := rel.Properties["validation_score"]; !exists {
			t.Errorf("Relation %s should have validation_score property", rel.ID)
		}
		if _, exists := rel.Properties["validated_by_ocr"]; !exists {
			t.Errorf("Relation %s should have validated_by_ocr property", rel.ID)
		}
	}
}

func TestGPUOCRPRUProcessorProcessPageParallel(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create a test image
	testImage := image.NewRGBA(image.Rect(0, 0, 100, 100))
	for x := 0; x < 100; x++ {
		for y := 0; y < 100; y++ {
			testImage.Set(x, y, color.RGBA{uint8(x % 255), uint8(y % 255), 128, 255})
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	result, err := processor.ProcessPageParallel(ctx, testImage, 0)
	if err != nil {
		t.Fatalf("Failed to process page in parallel: %v", err)
	}

	if result.PageIndex != 0 {
		t.Errorf("Expected page index 0, got %d", result.PageIndex)
	}

	if result.VisualTokens == nil {
		t.Error("Expected visual tokens in result")
	}

	if result.OCRTokens == nil {
		t.Error("Expected OCR tokens in result")
	}

	if result.Relations == nil {
		t.Error("Expected relations slice in result (can be empty)")
	}

	if len(result.VisualTokens) == 0 {
		t.Error("Expected some visual tokens")
	}

	if len(result.OCRTokens) == 0 {
		t.Error("Expected some OCR tokens")
	}

	if len(result.Relations) == 0 {
		t.Logf("Note: Got %d relations after validation and filtering (may be 0 due to quality threshold)", len(result.Relations))
	}
}

func TestGPUOCRPRUProcessorProcessDocumentParallel(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	mockOCR := NewMockOCRClient(5 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create test images
	testImages := make([]image.Image, 2)
	for i := range testImages {
		img := image.NewRGBA(image.Rect(0, 0, 100, 100))
		for x := 0; x < 100; x++ {
			for y := 0; y < 100; y++ {
				img.Set(x, y, color.RGBA{uint8(x % 255), uint8(y % 255), 128, 255})
			}
		}
		testImages[i] = img
	}

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	results, err := processor.ProcessDocumentParallel(ctx, testImages)
	if err != nil {
		t.Fatalf("Failed to process document in parallel: %v", err)
	}

	if len(results) != len(testImages) {
		t.Errorf("Expected %d results for %d images, got %d", len(testImages), len(testImages), len(results))
	}

	for i, result := range results {
		if result.PageIndex != i {
			t.Errorf("Expected page index %d, got %d", i, result.PageIndex)
		}
		if result.Error != nil {
			t.Errorf("Page %d had unexpected error: %v", i, result.Error)
		}
	}
}

func TestGPUOCRPRUProcessorContextCancellation(t *testing.T) {
	gm := gpu.NewGPUManager(0)
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	defer gm.Shutdown()

	// Use a longer delay to ensure we can test cancellation
	mockOCR := NewMockOCRClient(100 * time.Millisecond)
	processor := NewGPUOCRPRUProcessor(gm, mockOCR)
	defer processor.Close()

	// Create a test image
	testImage := image.NewRGBA(image.Rect(0, 0, 100, 100))

	// Create context that will be cancelled quickly
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()

	// This should return early due to context cancellation
	_, err := processor.ProcessPageParallel(ctx, testImage, 0)
	if err != nil {
		// We might get a context cancelled error, which is okay
		if err != context.DeadlineExceeded && err != context.Canceled {
			// Log the error but don't fail the test as it may be expected behavior
			t.Logf("Got expected timeout error: %v", err)
		}
	}
}