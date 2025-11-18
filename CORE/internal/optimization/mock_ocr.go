package optimization

import (
	"context"
	"image"
	"math/rand"
	"time"

	"github.com/vargasjosej/CORE/internal/gpu"
)

// MockOCRClient simulates an OCR service for testing
type MockOCRClient struct {
	responseDelay time.Duration
}

// NewMockOCRClient creates a new mock OCR client
func NewMockOCRClient(responseDelay time.Duration) *MockOCRClient {
	rand.Seed(time.Now().UnixNano())
	return &MockOCRClient{
		responseDelay: responseDelay,
	}
}

// ProcessPage simulates OCR processing of a page
func (moc *MockOCRClient) ProcessPage(ctx context.Context, page image.Image) ([]*gpu.OCRToken, error) {
	// Simulate processing delay
	select {
	case <-time.After(moc.responseDelay):
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	// Create some mock OCR tokens based on the image bounds
	bounds := page.Bounds()
	width := bounds.Dx()
	height := bounds.Dy()

	// Generate OCR tokens at regular intervals
	var tokens []*gpu.OCRToken
	tokenCount := 10 // Generate 10 OCR tokens per page
	intervalX := width / tokenCount
	intervalY := height / 5 // 5 rows of tokens

	for row := 0; row < 5; row++ {
		for col := 0; col < tokenCount; col++ {
			x := col * intervalX
			y := row * intervalY
			w := intervalX - 5 // Subtract 5 for spacing
			h := intervalY - 5 // Subtract 5 for spacing

			if w < 10 {
				w = 10
			}
			if h < 10 {
				h = 10
			}

			// Ensure we don't go out of bounds
			if x+w > width {
				w = width - x
			}
			if y+h > height {
				h = height - y
			}

			// Generate random text for the token
			text := randomText()
			confidence := 0.8 + rand.Float32()*0.2 // 0.8 to 1.0 confidence

			token := &gpu.OCRToken{
				ID:         generateOCRTokenID(row, col),
				Text:       text,
				Page:       0, // This would be set by the caller in real implementation
				BBox:       [4]float32{float32(x), float32(y), float32(w), float32(h)},
				Confidence: confidence,
			}

			tokens = append(tokens, token)
		}
	}

	return tokens, nil
}

// randomText generates random text for mock OCR tokens
func randomText() string {
	words := []string{"text", "document", "page", "paragraph", "header", "footer", "content", "section", "chapter", "title"}
	return words[rand.Intn(len(words))]
}

// generateOCRTokenID generates a unique ID for an OCR token
func generateOCRTokenID(row, col int) string {
	return "ocr_" + string(rune('A'+row)) + string(rune('0'+col))
}