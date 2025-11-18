package services

import (
	"context"
	"fmt"
	"image"
	"log"

	"github.com/vargasjosej/CORE/internal/domain/pru"
	"github.com/vargasjosej/CORE/internal/infrastructure/io"
	"github.com/vargasjosej/CORE/internal/infrastructure/gpu"
	"github.com/vargasjosej/CORE/pkg/algorithms/kdtree"
)

// ExtractionService handles the extraction of PRU relations from documents
type ExtractionService struct {
	pdfProcessor  *io.PDFProcessor
	gpuProcessor  *gpu.CUDAProcessor
}

// NewExtractionService creates a new extraction service
func NewExtractionService() *ExtractionService {
	return &ExtractionService{
		pdfProcessor: io.NewPDFProcessor(),
		gpuProcessor: gpu.NewCUDAProcessor(),
	}
}

// ExtractPRUFromPDF extracts PRU relations from a PDF file
func (es *ExtractionService) ExtractPRUFromPDF(ctx context.Context, pdfPath string) ([]*pru.PRURelation, error) {
	log.Printf("Starting PRU extraction from PDF: %s", pdfPath)

	// Get number of pages
	pageCount, err := es.pdfProcessor.GetNumPages(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get PDF page count: %w", err)
	}

	log.Printf("Processing %d pages from PDF", pageCount)

	var allRelations []*pru.PRURelation

	// Process each page
	for i := 0; i < pageCount; i++ {
		log.Printf("Processing page %d/%d", i+1, pageCount)

		// Extract image for this specific page
		img, err := es.extractSinglePageImage(pdfPath, i)
		if err != nil {
			log.Printf("Warning: Could not extract page %d: %v", i, err)
			continue
		}

		// Extract visual tokens from the page image
		tokens, err := es.gpuProcessor.ExtractVisualTokensFromImage(ctx, img, i)
		if err != nil {
			log.Printf("Warning: Could not extract tokens from page %d: %v", i, err)
			continue
		}

		log.Printf("Extracted %d visual tokens from page %d", len(tokens), i)

		// Extract PRU relations from tokens
		pageRelations, err := es.extractPRURelationsFromTokens(tokens)
		if err != nil {
			log.Printf("Warning: Could not extract relations from page %d: %v", i, err)
			continue
		}

		log.Printf("Extracted %d PRU relations from page %d", len(pageRelations), i)
		allRelations = append(allRelations, pageRelations...)
	}

	log.Printf("Completed PRU extraction. Total relations: %d", len(allRelations))
	return allRelations, nil
}

// extractSinglePageImage extracts a single page as an image
// This is a workaround since go-fitz doesn't have direct single-page extract
func (es *ExtractionService) extractSinglePageImage(pdfPath string, pageNum int) (image.Image, error) {
	// For this implementation, let's use the same approach as the PDFProcessor
	// but return just the specified page's image
	doc, err := es.pdfProcessor.ExtractImages(context.Background(), pdfPath)
	if err != nil {
		return nil, err
	}

	if len(doc) <= pageNum {
		return nil, fmt.Errorf("page %d not found in document", pageNum)
	}

	return doc[pageNum], nil
}

// extractPRURelationsFromTokens extracts various types of PRU relations from visual tokens
func (es *ExtractionService) extractPRURelationsFromTokens(tokens []*pru.VisualToken) ([]*pru.PRURelation, error) {
	var relations []*pru.PRURelation

	// Convert tokens to points for KD-Tree spatial indexing
	points := make([]kdtree.Point, len(tokens))
	for i, token := range tokens {
		points[i] = kdtree.Point{
			ID: string(token.ID),
			X:  token.BoundarySignature["centroid_x"].(float64),
			Y:  token.BoundarySignature["centroid_y"].(float64),
			Data: token,
		}
	}

	// Create KD-Tree for efficient spatial queries
	kdtree := kdtree.NewKDTree(points)

	// Extract ENTITY relations (spatial co-occurrence)
	entityRels, err := es.extractEntityRelations(tokens, kdtree)
	if err == nil {
		relations = append(relations, entityRels...)
	}

	// Extract TOPOLOGY relations (spatial containment)
	topologyRels, err := es.extractTopologyRelations(tokens)
	if err == nil {
		relations = append(relations, topologyRels...)
	}

	// TODO: Extract other PRU relation types (Sequentiality, Modulation, etc.)

	return relations, nil
}

// extractEntityRelations finds spatial co-occurrence relations between tokens
func (es *ExtractionService) extractEntityRelations(tokens []*pru.VisualToken, tree *kdtree.KDTree) ([]*pru.PRURelation, error) {
	var relations []*pru.PRURelation

	// For each token, find nearby tokens to create ENTITY relations
	for _, token := range tokens {
		center := kdtree.Point{
			ID: string(token.ID),
			X:  token.BoundarySignature["centroid_x"].(float64),
			Y:  token.BoundarySignature["centroid_y"].(float64),
		}

		// Find all tokens within a certain radius
		nearbyPoints := tree.QueryRadius(center, 100.0) // 100 pixel radius

		for _, nearbyPoint := range nearbyPoints {
			if nearbyPoint.ID == center.ID {
				continue // Skip self-relation
			}

			// Find the corresponding token
			var nearbyToken *pru.VisualToken
			for _, t := range tokens {
				if string(t.ID) == nearbyPoint.ID {
					nearbyToken = t
					break
				}
			}

			if nearbyToken != nil {
				// Calculate distance-based strength (closer = stronger)
				dx := center.X - nearbyPoint.X
				dy := center.Y - nearbyPoint.Y
				distance := (dx*dx + dy*dy)
				strength := 1.0 / (1.0 + distance/10000.0) // Normalize strength

				relation := &pru.PRURelation{
					ID:           fmt.Sprintf("rel_entity_%s_%s", center.ID, nearbyPoint.ID),
					RelationType: pru.Entity,
					SourceID:     token.ID,
					TargetID:     nearbyToken.ID,
					Strength:     float32(strength),
					Properties: map[string]interface{}{
						"distance_px": distance,
						"centroid_x":  center.X,
						"centroid_y":  center.Y,
					},
					ObserverID:     "entity_extractor",
					ValidityDomain: pru.ValidityDomain{},
				}

				relations = append(relations, relation)
			}
		}
	}

	return relations, nil
}

// extractTopologyRelations finds containment relations between tokens
func (es *ExtractionService) extractTopologyRelations(tokens []*pru.VisualToken) ([]*pru.PRURelation, error) {
	var relations []*pru.PRURelation

	// Check each token against every other token for containment
	for i, tokenA := range tokens {
		for j, tokenB := range tokens {
			if i == j {
				continue // Skip self-comparison
			}

			// Check if tokenB is contained within tokenA
			if es.isContained(tokenA, tokenB) {
				// Calculate containment strength based on area ratio
				areaA := tokenA.AreaPx
				areaB := tokenB.AreaPx
				containmentRatio := float32(areaB) / areaA

				if containmentRatio < 1.0 { // Only consider actual containment, not equal size
					relation := &pru.PRURelation{
						ID:           fmt.Sprintf("rel_topology_%s_%s", tokenA.ID, tokenB.ID),
						RelationType: pru.Topology,
						SourceID:     tokenA.ID, // container
						TargetID:     tokenB.ID, // contained
						Strength:     containmentRatio,
						Properties: map[string]interface{}{
							"containment_ratio": containmentRatio,
							"container_area":    areaA,
							"contained_area":    areaB,
						},
						ObserverID:     "topology_extractor",
						ValidityDomain: pru.ValidityDomain{},
					}

					relations = append(relations, relation)
				}
			}
		}
	}

	return relations, nil
}

// isContained checks if tokenB is spatially contained within tokenA
func (es *ExtractionService) isContained(container, contained *pru.VisualToken) bool {
	// Get bounding boxes
	containerX := container.BBox[0]
	containerY := container.BBox[1]
	containerW := container.BBox[2]
	containerH := container.BBox[3]

	containedX := contained.BBox[0]
	containedY := contained.BBox[1]
	containedW := contained.BBox[2]
	containedH := contained.BBox[3]

	// Check if contained token's bbox is within container token's bbox
	return (containedX >= containerX) &&
		(containedY >= containerY) &&
		(containedX+containedW <= containerX+containerW) &&
		(containedY+containedH <= containerY+containerH)
}