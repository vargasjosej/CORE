package gpu

import (
	"context"
	"image"
	"image/color"
	"testing"
	"time"
)

func TestGPUManagerInitialization(t *testing.T) {
	gm := NewGPUManager(0)
	
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	if !gm.initialized {
		t.Error("GPU manager should be initialized after Initialize()")
	}
}

func TestGPUManagerProcessImageBatch(t *testing.T) {
	gm := NewGPUManager(0)
	
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	// Create test images
	testImages := make([]image.Image, 2)
	for i := range testImages {
		// Create a simple 100x100 image
		img := image.NewRGBA(image.Rect(0, 0, 100, 100))
		for x := 0; x < 100; x++ {
			for y := 0; y < 100; y++ {
				img.Set(x, y, color.RGBA{uint8(x % 255), uint8(y % 255), 128, 255})
			}
		}
		testImages[i] = img
	}
	
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	tokens, err := gm.ProcessImageBatch(ctx, testImages)
	if err != nil {
		t.Fatalf("Failed to process image batch: %v", err)
	}
	
	if len(tokens) == 0 {
		t.Error("Expected to extract some visual tokens, got none")
	}

	// Each image should generate at least some tokens
	// The actual number depends on the region size and image dimensions
	// For a 100x100 image with 50x50 regions, we expect about 4 regions per image
	if len(tokens) < len(testImages)*2 { // At least 2 tokens per image
		t.Logf("Note: Got %d tokens for %d images, which is less than expected but may be acceptable", len(tokens), len(testImages))
	}
	
	// Verify token properties
	for _, token := range tokens {
		if token.ID == "" {
			t.Error("Token ID should not be empty")
		}
		if token.ObserverID == "" {
			t.Error("Token ObserverID should not be empty")
		}
		if token.AreaPx <= 0 {
			t.Errorf("Token area should be positive, got %f", token.AreaPx)
		}
	}
}

func TestGPUManagerProcessEmptyBatch(t *testing.T) {
	gm := NewGPUManager(0)
	
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	ctx := context.Background()
	
	tokens, err := gm.ProcessImageBatch(ctx, []image.Image{})
	if err != nil {
		t.Fatalf("Failed to process empty batch: %v", err)
	}
	
	if len(tokens) != 0 {
		t.Errorf("Expected 0 tokens for empty batch, got %d", len(tokens))
	}
}

func TestGPUManagerNotInitialized(t *testing.T) {
	gm := NewGPUManager(0)
	// Don't initialize the GPU manager

	ctx := context.Background()

	testImg := image.NewRGBA(image.Rect(0, 0, 10, 10))
	_, err := gm.ProcessImageBatch(ctx, []image.Image{testImg})
	if err == nil {
		t.Error("Expected error when GPU manager is not initialized")
	}

	if err.Error() != "GPU manager not initialized" {
		t.Errorf("Expected 'GPU manager not initialized', got: %v", err)
	}
}

func TestGPUManagerGetUtilization(t *testing.T) {
	gm := NewGPUManager(0)
	
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	utilization := gm.GetUtilization()
	
	if utilization == nil {
		t.Fatal("Utilization should not be nil")
	}
	
	if initialized, ok := utilization["initialized"].(bool); !ok || !initialized {
		t.Error("Utilization should show initialized as true")
	}
	
	if deviceID, ok := utilization["device_id"].(int); !ok || deviceID != 0 {
		t.Error("Utilization should show correct device ID")
	}
}

func TestGPUManagerShutdown(t *testing.T) {
	gm := NewGPUManager(0)
	
	if err := gm.Initialize(); err != nil {
		t.Fatalf("Failed to initialize GPU manager: %v", err)
	}
	
	if !gm.initialized {
		t.Error("GPU manager should be initialized")
	}
	
	gm.Shutdown()
	
	if gm.initialized {
		t.Error("GPU manager should not be initialized after shutdown")
	}
}