package pru

import (
	"time"
)

// VisualToken represents a visual observation token
type VisualToken struct {
	ID                TokenID                    `json:"id"`
	ObserverID        ObserverID                 `json:"observer_id"`
	TimestampNs       int64                      `json:"timestamp_ns"`
	BoundarySignature map[string]interface{}     `json:"boundary_signature"`
	Context           map[string]interface{}     `json:"context"`
	BBox              [4]float32                 `json:"bbox"` // [x, y, w, h]
	EmbeddingLocal    []float32                  `json:"embedding_local"`
	AreaPx            float32                    `json:"area_px"`
	AspectRatio       float32                    `json:"aspect_ratio"`
	PageNumber        int                        `json:"page_number"`
	VisualType        string                     `json:"visual_type"` // text_block, image, diagram, etc.
}

func (vt *VisualToken) GetID() TokenID {
	return vt.ID
}

func (vt *VisualToken) GetObserverID() ObserverID {
	return vt.ObserverID
}

func (vt *VisualToken) GetTimestamp() time.Time {
	return time.Unix(0, vt.TimestampNs)
}

func (vt *VisualToken) GetBoundarySignature() map[string]interface{} {
	return vt.BoundarySignature
}

func (vt *VisualToken) GetContext() map[string]interface{} {
	return vt.Context
}